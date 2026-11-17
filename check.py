#!/usr/bin/env python3
"""Checks the rules of this repository that currently rely on human discipline.

It covers mainly the traps the conventions classify as "no visible error":
Quadlet generates the unit, `podman inspect` does not complain, and the
defect only shows up in production.

Usage:
    python3 check.py            # check the repository
    python3 check.py --selftest # test the parser itself

Exits 1 if there is any error, 0 if there are only warnings.
No dependencies: stdlib only, so it runs on the immutable host as-is.
"""

import os
import re
import shlex
import sys
from collections import defaultdict
from pathlib import Path

import manifest
import svcwidgets
import instances
from qhui import (translator, directives, directives_of, published_port, format_unit,
                  red, yellow, green, dim, GRUPOS, valid_template, ENV_TYPES, ENV_TYPE_LINE, env_value_problem)

PT = {
    "unit(s) reformatted": "unit(s) reformatada(s)",
    "services,": "serviços,",
    "containers,": "containers,",
    "published ports": "portas publicadas",
    "error(s),": "erro(s),",
    "warning(s)": "aviso(s)",
    "does not use the app name as a prefix": "não usa o nome do app como prefixo",
    "is single-container but has a .network": "tem um container só mas tem uma .network",
    "(single-container uses the default network)": "(um container só usa a rede padrão)",
    "— they become the same systemd unit": "— viram a mesma unit do systemd",
    "repeated in": "repetido em",
    "uses Notify=healthy without HealthCmd=": "usa Notify=healthy sem HealthCmd=",
    "(the image's own HEALTHCHECK does not count)": "(o HEALTHCHECK da própria imagem não conta)",
    "uses localhost in HealthCmd": "usa localhost no HealthCmd",
    "(resolves IPv4+IPv6; use 127.0.0.1)": "(resolve IPv4+IPv6; use 127.0.0.1)",
    "has a bare $ in HealthCmd (escape it as $$)": "tem um $ solto no HealthCmd (escape como $$)",
    "Label with a backslash — Quadlet drops the whole line":
        "Label com barra invertida — o Quadlet descarta a linha inteira",
    "Label with an unquoted space, truncates at the first one":
        "Label com espaço sem aspas, corta no primeiro",
    "has AutoUpdate= — nothing in this repository updates on its own, pin the image and remove it":
        "tem AutoUpdate= — nada neste repositório atualiza sozinho, fixe a imagem e remova-o",
    "is on a floating tag": "está em tag flutuante",
    "pin a version, or a digest where upstream publishes none":
        "fixe uma versão, ou um digest onde o projeto não publica versão",
    "nothing will report a new version": "nada vai reportar versão nova",
    "published by": "publicada por",
    "has no recipe in app.json [secrets] — install.py cannot generate it":
        "não tem receita em app.json [secrets] — o install.py não consegue gerá-lo",
    "app.json has a recipe for": "app.json tem receita para",
    "README table(s) regenerated": "tabela(s) de README regerada(s)",
    "is not a Secret= any unit declares": "não é um Secret= que alguma unit declare",
    "must start with `shell ` — install.py runs nothing else":
        "tem que começar com `shell ` — o install.py não roda outra coisa",
    "needs a `manual` recipe in [secrets] — a generated secret is never checked":
        "precisa de receita `manual` em [secrets] — secret gerado nunca é conferido",
    "which no unit uses": "que nenhuma unit usa",
    "which no unit declares as a Secret=": "que nenhuma unit declara como Secret=",
    "has no row in the README services table": "não tem linha na tabela de serviços do README",
    "the README says": "o README diz",
    "the unit says": "a unit diz",
    "could not find": "não encontrei",
}
loc = translator(PT)


ROOT = Path(__file__).resolve().parent
APPS = ROOT / "apps"

errors: list[str] = []
warnings: list[str] = []


def error(rule, msg):
    errors.append(f"{rule}: {msg}")


def warn(rule, msg):
    warnings.append(f"{rule}: {msg}")


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------



def exemptions(text):
    """Rules the unit waives itself, via `# check: ignore <rule> <reason>`.

    It lives in the unit instead of a central allowlist on purpose: the reason
    sits next to what it justifies, like every other comment in this repo.
    """
    return {m.group(1) for m in re.finditer(r"^#\s*check:\s*ignore\s+(\S+)", text, re.M)}




def main_unit(folder):
    """The .container that represents the app (the one `qh` starts)."""
    conts = sorted(folder.glob("*.container"))
    if not conts:
        return None
    exact = folder / f"{folder.name}.container"
    if exact in conts:
        return exact
    return conts[0] if len(conts) == 1 else None


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_units(folders):
    seen = defaultdict(list)
    for folder in folders:
        files = sorted(folder.glob("*.container")) + sorted(folder.glob("*.network"))
        for f in files:
            seen[f.name].append(f"apps/{folder.name}")
            if not f.name.startswith(folder.name) and not folder.name.startswith(f.stem):
                warn("rule 1", f"apps/{folder.name}/{f.name} does not use the app name "
                               f"as a prefix")

        conts = [a for a in files if a.suffix == ".container"]
        nets = [a for a in files if a.suffix == ".network"]
        if nets and len(conts) == 1 and not any(
                "structure" in exemptions(c.read_text()) for c in conts):
            warn("structure", f"apps/{folder.name} is single-container but has a .network "
                              f"(single-container uses the default network)")

        for f in conts:
            check_container(f, folder)

        # A stack's sidecar that nothing pulls up sits installed and never
        # starts: `systemctl start <app>` walks Requires=/Wants=, and a unit
        # outside that walk only comes up at the next login, with an empty
        # journal in the meantime. Three of them hid that way. Only real stacks
        # are checked — a folder of independent services (media-stack, vm,
        # toolbx) has no main unit to hang them from.
        principal = main_unit(folder)
        if nets and principal and len(conts) > 1:
            juntos = " ".join(c.read_text() for c in conts)
            for c in conts:
                if c.stem == principal.stem:
                    continue
                puxado = re.search(rf"(Requires|Wants|After)=[^\n]*\b{re.escape(c.stem)}"
                                   rf"\.service", juntos)
                if not puxado and f"Network={c.stem}.container" not in juntos:
                    warn("sidecar", f"apps/{folder.name}/{c.name} is pulled up by nothing "
                                    f"— add Wants={c.stem}.service to {principal.name}")

    # The basename becomes the unit name across the whole host, even across
    # subfolders: two files with the same name in different folders really collide.
    for name, where in seen.items():
        if len(where) > 1:
            error("rule 1", f"basename {name} repeated in {', '.join(where)} "
                            f"— they become the same systemd unit")


# Measured on Podman 6.0.2: one unit generated per key, its `podman run` line
# diffed against a bare one. PodmanArgs bypasses every check Quadlet makes —
# its own manual says using it "is not recommended" — and each defect this
# repository has found in a unit arrived through it.
NATIVO = {
    "--add-host": "AddHost", "--cap-add": "AddCapability",
    "--cap-drop": "DropCapability", "--device": "AddDevice", "--dns": "DNS",
    "--entrypoint": "Entrypoint", "--env": "Environment",
    "--env-file": "EnvironmentFile", "--hostname": "HostName",
    "--init": "RunInit", "--label": "Label", "--memory": "Memory",
    "--pids-limit": "PidsLimit", "--publish": "PublishPort",
    "--read-only": "ReadOnly", "--secret": "Secret",
    "--security-opt": "NoNewPrivileges= or SecurityLabel*=",
    "--shm-size": "ShmSize", "--stop-timeout": "StopTimeout",
    "--tmpfs": "Tmpfs", "--user": "User", "--userns": "UserNS",
    "--workdir": "WorkingDir",
}


def check_podman_args(text, ref):
    """What goes through PodmanArgs, which Quadlet never looks at.

    Two ways it has gone wrong here. A flag that has a key of its own ends up
    written twice, and the last one silently wins — radicale ran at 50 pids
    while its own unit said 256. And a space inside one argument does not
    survive: unquoted, systemd splits it into separate arguments; escaped with
    a backslash, Quadlet drops the argument and says nothing. Quoting is the
    only spelling that works (`PodmanArgs=--foo="a b"`).
    """
    for n, line in enumerate(text.splitlines(), 1):
        if not line.startswith("PodmanArgs="):
            continue
        valor = line.partition("=")[2]
        onde = f"{ref}:{n}"
        if "\\ " in valor:
            error("PodmanArgs", f"{onde}: a backslash-escaped space drops the whole "
                                f"argument — quote it instead")
            continue
        try:
            tokens = shlex.split(valor)
        except ValueError:
            error("PodmanArgs", f"{onde}: unbalanced quote")
            continue
        for i, tok in enumerate(tokens):
            if i and not tok.startswith("-") and "=" in tokens[i - 1]:
                error("PodmanArgs", f"{onde}: an unquoted space splits "
                                    f"`{tokens[i - 1]} {tok}` into two arguments")
                break
        for tok in tokens:
            chave = NATIVO.get(tok.partition("=")[0])
            if chave:
                error("PodmanArgs", f"{onde}: {tok.partition('=')[0]} has a Quadlet key "
                                    f"of its own — use {chave}")


# systemd expands `$VAR`, so a literal dollar in HealthCmd is written `$$`
# (rule 7). One expression, shared with the test that holds it to account: the
# selftest used to rebuild it, so loosening this one — dropping the lookbehind
# and condemning the correct `$$` too — still printed "selftest: ok".
# Rule 9: every image is pinned. A tag with no `x.y` in it — `latest`, `main`, a
# bare major like `16` or `17-alpine` — is rebuilt under the same name, so the
# host runs whatever was pushed last. A digest pins the content even on such a
# tag, which is how images that publish no version stay fixed (monica-next, the
# Fedora toolbox).
PINNED_TAG = re.compile(r"\d+\.\d+")


def floating_tag(image):
    """The tag when the image is not pinned to one build, else None."""
    if "@sha256:" in image:
        return None
    nome = image.rsplit("/", 1)[-1]
    tag = nome.partition(":")[2] or "latest"
    return None if PINNED_TAG.search(tag) else tag


BARE_DOLLAR = re.compile(r"(?<!\$)\$(?!\$)[A-Za-z{]")


def bare_image(value):
    """An `Image=` with no tag and no digest: the version is not in the repository."""
    return ":" not in value.rpartition("/")[2] and "@" not in value


def image_templates(folder):
    """{unit: template} from `[image]` in the folder's app.json."""
    ini = manifest.view(folder)
    return dict(ini.items("image")) if ini.has_section("image") else {}


def image_template_problemas(folder):
    """What is wrong with a folder's `[image]` section, as [(unit, message)]."""
    saida = []
    ini = manifest.view(folder)
    fontes = dict(ini.items("upstream")) if ini.has_section("upstream") else {}
    for unit, tpl in image_templates(folder).items():
        caminho = folder / f"{unit}.container"
        if not caminho.exists():
            saida.append((unit, "is not a unit of this folder"))
            continue
        if not valid_template(tpl):
            saida.append((unit, f"template {tpl!r} needs exactly one {{version}} (or {{version:N}})"))
        imagens = [v for k, v in directives_of(caminho) if k == "Image"]
        if not imagens or not bare_image(imagens[0]):
            saida.append((unit, "has a template but its Image= is not bare: one of them has to go"))
        fonte = fontes.get(unit, "")
        if fonte == "-" or fonte.startswith(("compose:", "registry")):
            saida.append((unit, f"follows `{fonte}` in [upstream]: only a GitHub release can fill a template"))
    return saida


def check_container(path, folder):
    text = path.read_text()
    ds = directives(text)
    keys = {c for c, _ in ds}
    ref = f"apps/{folder.name}/{path.name}"

    check_podman_args(text, ref)

    # Rule 9. Nothing in this repository updates on its own: AutoUpdate= is refused, and an image is
    # either pinned here (a tag or a digest) or has NO tag and a `[image]` template in app.json —
    # `qh` then pins the latest release on the host, in a drop-in, and a person moves it.
    if "AutoUpdate" in keys:
        error("rule 9", f"{ref} has AutoUpdate= — nothing in this repository updates on "
                        f"its own, pin the image and remove it")
    if "floating" not in exemptions(text):
        for key, value in ds:
            if key != "Image":
                continue
            if bare_image(value):
                if path.stem not in image_templates(folder):
                    error("rule 9", f"{ref} has an image with no tag and no `[image]` template for "
                                    f"{path.stem} in app.json — `qh` would pull `latest`")
            elif tag := floating_tag(value):
                error("rule 9", f"{ref} is on a floating tag (`{tag}`) — pin a version, "
                                f"or a digest where upstream publishes none")

    if ("Notify", "healthy") in ds and "HealthCmd" not in keys:
        error("rule 14", f"{ref} uses Notify=healthy without HealthCmd= "
                         f"(the image's own HEALTHCHECK does not count)")

    for key, value in ds:
        if key == "HealthCmd":
            if "localhost" in value:
                error("rule 13", f"{ref} uses localhost in HealthCmd "
                                 f"(resolves IPv4+IPv6; use 127.0.0.1)")
            # systemd expands $VAR; a literal one needs $$.
            if BARE_DOLLAR.search(value):
                error("rule 7", f"{ref} has a bare $ in HealthCmd (escape it as $$)")

        if key == "Label":
            if "\\" in value:
                error("rule 18", f"{ref}: Label with a backslash — Quadlet drops the "
                                 f"whole line ({value[:40]}…)")
            # systemd reads % as a specifier and refuses to load the unit:
            # "Failed to resolve unit specifiers". A literal one is %%.
            if re.search(r"(?<!%)%(?!%)", value):
                error("rule 12", f"{ref}: Label with a bare % — systemd reads it as a "
                                 f"specifier and the unit will not load, escape it as "
                                 f"%% ({value[:44]}…)")
            _, _, content = value.partition("=")
            if " " in content and not (content.startswith(('"', "'"))):
                error("rule 12", f"{ref}: Label with an unquoted space, truncates at the "
                                 f"first one ({value[:40]}…)")

    # Rule 20 applies this one without testing, and nothing tracked it: 54 of
    # the 110 units had drifted without it, 16 already carrying ReadOnly and
    # DropCapability=ALL — the cheapest lock missing from the tightest units.
    # A warning, not an error: what is left needs a test on the machine those
    # containers run on, and a waiver written blind would only hide that.
    if "NoNewPrivileges" not in keys and "hardening" not in exemptions(text):
        warn("rule 20", f"{ref} has no NoNewPrivileges=true — rule 20 applies it "
                        f"without testing")


def check_ports(folders):
    uses = defaultdict(list)
    for folder in folders:
        for f in sorted(folder.glob("*.container")):
            text = f.read_text()
            if "ports" in exemptions(text):
                continue
            for key, value in directives(text):
                if key != "PublishPort":
                    continue
                p = published_port(value)
                if p:
                    uses[p].append(f"apps/{folder.name}/{f.name}")
    for (port, proto), where in sorted(uses.items()):
        if len(set(where)) > 1:
            error("ports", f"{port}/{proto} published by {', '.join(sorted(set(where)))}")
    return uses


def deprecated_problemas(valor):
    """What is wrong with a `[store] deprecated` reason, as a list; empty when it will do.

    It is shown to a person in the store, in a badge and a sentence: one line,
    saying what happened (archived, the image is gone, the project moved), not
    just that it is old.
    """
    v = valor.strip()
    if not v:
        return ["is empty — say why"]
    saida = []
    if len(v) > 300:
        saida.append(f"is {len(v)} characters; keep it to one short sentence (300 at most)")
    if re.search(r"[\r\n<>]", valor):
        saida.append("has a line break or a < >; it is shown as plain text, on one line")
    return saida


def env_type_problemas(texto):
    """What is wrong with the `# type:` hints of a `.env.example`, as [(line, message)].

    A hint belongs to the setting just below it: a known type, followed by a KEY= line before
    any blank line, and the value the example ships has to be one of that type."""
    saida, pendente = [], None
    for n, linha in enumerate(texto.splitlines(), 1):
        corpo = linha.lstrip("#").strip() if linha.startswith("#") else None
        m = ENV_TYPE_LINE.match(corpo) if corpo is not None else None
        if m:
            tipo = m.group(1).lower()
            if tipo not in ENV_TYPES:
                saida.append((n, f"unknown type {tipo!r} (one of {', '.join(ENV_TYPES)})"))
                pendente = None
            else:
                pendente = (n, tipo)
        elif re.match(r"^#?\s*[A-Za-z_][A-Za-z0-9_]*=", linha):
            if pendente:
                valor = linha.split("=", 1)[1]
                if env_value_problem(pendente[1], valor):
                    saida.append((n, f"the value {valor.strip()!r} is not a {pendente[1]}"))
            pendente = None
        elif not linha.strip():
            if pendente:
                saida.append((pendente[0], "a type hint with no setting below it"))
            pendente = None
    if pendente:
        saida.append((pendente[0], "a type hint with no setting below it"))
    return saida


def docs_problemas(valor):
    """What is wrong with `docs` (an https URL), as a list."""
    return [] if re.fullmatch(r"https://[A-Za-z0-9.-]+(/\S*)?", valor.strip()) else ["is not a plain https:// URL"]


def backup_problemas(ini):
    """What is wrong with an app.json [backup] section, as a list."""
    saida = []
    for key, valor in ini.items("backup"):
        if key not in ("mode", "exclude"):
            saida.append(f"has no key {key!r} (only `mode` and `exclude`)")
        elif key == "mode" and valor.strip() != "stop":
            saida.append("mode must be `stop`")
        elif key == "exclude":
            for p in (l.strip() for l in valor.splitlines() if l.strip()):
                if p.startswith("/") or ".." in Path(p).parts:
                    saida.append(f"exclude {p!r}: a pattern relative to the volumes, no leading / and no ..")
    return saida


def repo_problemas(valor):
    """What is wrong with `[store] repo`, as a list; empty when it will do.

    The store links the project, its issues and its releases from it, so it has to be a
    page that exists: `owner/repo` on GitHub, or a full https URL. Only needed where the
    image's own path would point somewhere else (the registry path is not always the
    repository's), which is why it is an override and not a field every service fills in.
    """
    v = valor.strip()
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", v) or re.fullmatch(r"https://[A-Za-z0-9.-]+/[A-Za-z0-9._/-]+", v):
        return []
    return ["is neither `owner/repo` (GitHub) nor a full https:// URL"]


def upstream_problema(valor):
    """What is wrong with an [upstream] value, or None when it parses.

    updates.py reads four forms and nothing checked which one it got:

        -                                  nothing to compare
        registry                           the registry's tag list
        registry:<pattern>                 that list, filtered
        compose:<owner>/<repo>:<path>      the tag the app's own compose pins
        compose:<url>                      the same, for a compose off GitHub
        <owner>/<repo>                     that project's GitHub releases

    A value outside them does not raise: it compares against the wrong thing
    or against nothing, and the run reports "cannot compare" at best. The
    grammar only grew a word recently — `registry:latest` — which is when a
    stray space in it became a way to switch the mode off in silence.
    """
    if valor == "-":
        return None
    if valor.startswith("registry"):
        resto = valor[len("registry"):]
        if not resto:
            return None
        if not resto.startswith(":"):
            return "expected `registry` or `registry:<pattern>`"
        padrao = resto[1:]
        if not padrao or padrao != padrao.strip():
            return "the pattern after `registry:` is empty or padded with spaces"
        try:
            re.compile(padrao)
        except re.error as e:
            return f"the pattern after `registry:` is not a regex ({e})"
        return None
    if valor.startswith("compose:"):
        resto = valor[len("compose:"):]
        if resto.startswith(("http://", "https://")):
            return None
        if ":" not in resto:
            return "expected `compose:<owner>/<repo>:<path>` or `compose:<url>`"
        repo, path = resto.split(":", 1)
        if repo.count("/") != 1 or not all(repo.split("/")) or not path:
            return "expected `<owner>/<repo>:<path>` after `compose:`"
        return None
    if valor.count("/") != 1 or not all(valor.split("/")) or " " in valor:
        return "expected `<owner>/<repo>`, `registry`, `compose:...` or `-`"
    return None


def layout_targets(folders):
    """Every .container the layout applies to: the apps and the template."""
    return [c for f in folders for c in sorted(f.glob("*.container"))] + \
        sorted((ROOT / "_template").glob("*.container"))


def check_layout(folders):
    """Every unit in the shared layout — the blocks of qhui.LAYOUT, a blank line apart.

    A convention nobody enforces lasts until the next unit is copied from an old
    one. Reordering never changes what runs (see qhui.LAYOUT), so this is an
    error and not a warning: the fix is mechanical, `python3 check.py --format`.
    """
    for c in layout_targets(folders):
        texto = c.read_text()
        if format_unit(texto) != texto:
            error("layout", f"{c.relative_to(ROOT)} is not in the standard layout — "
                            f"run: python3 check.py --format")


def check_shared_labels(folders):
    """A host path two units mount — the same one, or one inside the other — is `:z`.

    `:Z` is a private SELinux label: each container that starts relabels the
    path to its own categories, and the one that started before loses it.
    Measured: two containers on one folder with `:Z`, the first reads it, the
    second starts, the first gets `Permission denied`. media-stack mounted
    ${MEDIA_DATA_DIR} that way in nine units — only the last one up could see
    the media — and authentik and beszel shared a folder the same way. `:z` is
    the shared label; a container with SecurityLabelDisable (zerobyte, which
    reads everyone's volumes) is out of the question and skipped.
    """
    montagens = []   # (host, unit, private)
    for folder in folders:
        for c in folder.glob("*.container"):
            texto = c.read_text()
            if re.search(r"^SecurityLabelDisable=true", texto, re.M):
                continue
            for k, v in directives_of(c):
                if k != "Volume":
                    continue
                partes = v.split(":")
                host = partes[0].rstrip("/")
                if len(partes) < 2 or host.startswith(("/etc/", "%t/")) or not partes[1].startswith("/"):
                    continue
                opcoes = partes[2].split(",") if len(partes) > 2 else []
                montagens.append((host, c.stem, "Z" in opcoes))
    ditos = set()
    for i, (a, ua, za) in enumerate(montagens):
        for b, ub, zb in montagens[i + 1:]:
            if ua == ub or not (a == b or b.startswith(a + "/") or a.startswith(b + "/")):
                continue
            for host, unit, privado in ((a, ua, za), (b, ub, zb)):
                if privado and (unit, host) not in ditos:
                    ditos.add((unit, host))
                    outro = ub if unit == ua else ua
                    error("rule 16", f"{unit} mounts {host} with :Z, and {outro} mounts it too — "
                                     f"the private label locks one of them out; use :z")


def check_manifest(folders):
    """Every Secret= has a recipe, and every .example has a known destination.

    This is what keeps install.py from stopping halfway through a service.
    """
    for folder in folders:
        ini = manifest.view(folder)
        for problema in manifest.problems(manifest.load(folder), tuple(GRUPOS), folder):
            error("manifest", f"apps/{folder.name}/app.json: {problema}")
        recipes = set(ini["secrets"]) if ini.has_section("secrets") else set()
        declared = set()
        for f in sorted(folder.glob("*.container")):
            for key, value in directives_of(f):
                if key == "Secret":
                    declared.add(value.split(",")[0])
        for unit, msg in image_template_problemas(folder):
            error("manifest", f"apps/{folder.name}: app.json [image] {unit} {msg}")
        for exemplo in sorted(folder.glob("*.env.example")):
            for n, msg in env_type_problemas(exemplo.read_text()):
                error("manifest", f"apps/{folder.name}/{exemplo.name}:{n}: {msg}")
        for missing in sorted(declared - recipes):
            error("manifest", f"apps/{folder.name}: Secret={missing} has no recipe in "
                              f"app.json [secrets] — install.py cannot generate it")
        for extra in sorted(recipes - declared):
            warn("manifest", f"apps/{folder.name}: app.json has a recipe for {extra}, "
                             f"which no unit uses")
        # `[choices.<unit>]` and `[login.<unit>]` target one unit of a folder.
        # The suffix was validated by nobody: renaming [choices.vm-windows] to
        # [choices.vm-windowss] left check.py at zero errors while `qh
        # vm-windows` stopped asking VERSION and LANGUAGE — so the VM silently
        # downloaded the default edition — and `qh vm-chromeos` stopped printing
        # the password you need to log in. install.py skips a section whose
        # suffix matches no unit, without a word. Same failure the [validate]
        # check below was written to catch.
        unidades = {f.stem for f in folder.glob("*.container")}
        for secao in ini.sections():
            prefixo, _, sufixo = secao.partition(".")
            if not sufixo or prefixo not in ("choices", "login"):
                continue
            if sufixo not in unidades:
                error("manifest", f"apps/{folder.name}: app.json [{secao}] names "
                                  f"{sufixo}, which is not a unit of this folder")
        # [upstream] keys are unit names too, and its values have a grammar
        # (see upstream_problema). Neither was validated. A key naming no unit
        # is dropped by updates.py without a word, and the image falls back to
        # guessing its GitHub repository from the image name — the very guess
        # the override exists to replace.
        for key, valor in (ini.items("upstream") if ini.has_section("upstream") else []):
            if key not in unidades:
                error("manifest", f"apps/{folder.name}: app.json [upstream] {key} "
                                  f"is not a unit of this folder")
            problema = upstream_problema(valor)
            if problema:
                error("manifest", f"apps/{folder.name}: app.json [upstream] {key} = "
                                  f"{valor} — {problema}")
        if ini.has_section("backup"):
            for problema in backup_problemas(ini):
                error("manifest", f"apps/{folder.name}: app.json [backup] {problema}")
        # What the app store shows about the service: category, links, the discontinued reason, the
        # Podman floor. The view builds this section from app.json, so a key here is always a known one.
        if ini.has_section("store"):
            for key, valor in ini.items("store"):
                for problema in (repo_problemas(valor) if key == "repo"
                                 else docs_problemas(valor) if key == "docs"
                                 else [] if key == "group" and valor.strip() in GRUPOS
                                 else [f"is not one of: {', '.join(GRUPOS)}"] if key == "group"
                                 else [] if key == "min_podman" and re.fullmatch(r"\d+\.\d+(\.\d+)?", valor.strip())
                                 else ["is not a version like 5.4"] if key == "min_podman"
                                 else [] if key == "requires_https"
                                 else deprecated_problemas(valor)):
                    error("manifest", f"apps/{folder.name}: app.json [store] {key} {problema}")
        # widgets: a type the store knows how to read, and a unit that is in this folder
        for w in (manifest.load(folder).get("widgets") or []) if isinstance(manifest.load(folder).get("widgets"), list) else []:
            if not isinstance(w, dict):
                continue
            if w.get("type") not in svcwidgets.TYPES:
                error("manifest", f"apps/{folder.name}: widget type {w.get('type')!r} is not one of: {', '.join(svcwidgets.TYPES)}")
            if w.get("unit") and not (folder / f"{w['unit']}.container").is_file():
                error("manifest", f"apps/{folder.name}: widget unit {w['unit']!r} is not a .container in the folder")
        # options: a `database` choice that offers SQLite defaults to it (the repository's rule: SQLite whenever the app supports it)
        for chave, o in (manifest.load(folder).get("options") or {}).items():
            if isinstance(o, dict) and chave == "database" and "sqlite" in (o.get("values") or {}) and o.get("default") != "sqlite":
                error("manifest", f"apps/{folder.name}: options.database offers sqlite, so sqlite is the default (conventions: SQLite first)")
        # [vars]: every ${VAR} a Volume= of this folder names needs a default
        # here, because it is what the install offers when it asks — and a
        # variable left unset turns `${MEDIA_DATA_DIR}/downloads` into
        # `/downloads`, which is how media-stack-downtify failed to start.
        usadas = set()
        for c in folder.glob("*.container"):
            for k, v in directives_of(c):
                if k == "Volume":
                    usadas |= set(re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", v.split(":")[0]))
        declaradas = set(ini["vars"]) if ini.has_section("vars") else set()
        for nome in sorted(usadas - {d.upper() for d in declaradas} - declaradas):
            error("manifest", f"apps/{folder.name}: Volume= uses ${{{nome}}} with no default "
                              f"in app.json [vars] — the install has nothing to offer")
        for nome in sorted(declaradas - usadas - {u.lower() for u in usadas}):
            warn("manifest", f"apps/{folder.name}: app.json [vars] {nome} is used by no Volume=")
        # [login] names the secret the install prints as the credentials, in
        # either shape (`password` next to a literal user, or `credentials`
        # holding `user:password`). A typo here is silent — the footer would
        # just skip the block.
        for secao in [s for s in ini.sections() if s == "login" or s.startswith("login.")]:
            # install.py reads `password` (with or without `user`) or
            # `credentials`. A section with neither is printed by nobody, and
            # that went unseen: koffan's password-only form was once in this
            # state, and the install showed no password at all.
            if not (ini.has_option(secao, "password") or ini.has_option(secao, "credentials")):
                error("manifest", f"apps/{folder.name}: app.json [{secao}] has neither "
                                  f"`password` nor `credentials` — install.py prints nothing")
            for key in ("password", "credentials"):
                name = ini.get(secao, key, fallback=None)
                if name and name not in declared:
                    error("manifest", f"apps/{folder.name}: app.json [{secao}] {key} = "
                                      f"{name}, which no unit declares as a Secret=")
        # [validate] keys are secret names too. A typo there is worse than no
        # check at all: the install prints nothing, and you believe the value
        # was verified when it was never looked at.
        for key in (ini["validate"] if ini.has_section("validate") else ()):
            if key not in declared:
                error("manifest", f"apps/{folder.name}: app.json [validate] {key} "
                                  f"is not a Secret= any unit declares")
            # `shell` is the only form install.py runs. Any other word makes the
            # check silently do nothing, which is worse than having none: the
            # install prints no warning and you believe the value was verified.
            elif not ini.get("validate", key, fallback="").startswith("shell "):
                error("manifest", f"apps/{folder.name}: app.json [validate] {key} "
                                  f"must start with `shell ` — install.py runs nothing else")
            # Only a `manual` secret is ever typed, and typing is the only moment
            # there is a value to check. A recipe that generates its own has
            # nothing to validate, so the entry would never fire.
            elif not ini.get("secrets", key, fallback="").startswith("manual"):
                error("manifest", f"apps/{folder.name}: app.json [validate] {key} "
                                  f"needs a `manual` recipe in [secrets] — a generated "
                                  f"secret is never checked")


# O rótulo que pode aparecer imediatamente antes de `.ts.net`. Vazio inclusive:
# a documentação mostra `my-app..ts.net` de propósito, pra explicar o que
# acontece quando ${TAILNET} não está definida.
TAILNET_PLACEHOLDERS = {"", "${TAILNET}", "<tailnet>", "<your-tailnet>", "your-tailnet"}

# The label before `.ts.net`, which is the tailnet's name. One expression, used
# by the check and by the test that holds it to account. The selftest used to
# rebuild it instead, so loosening this one — dropping `{}` from the class, and
# with it `${TAILNET}` as a recognised placeholder — still printed "ok" while
# the guard on the repository's most emphatic rule quietly stopped guarding.
TAILNET_NAME = re.compile(r"([A-Za-z0-9_${}<>-]*)\.ts\.net")


def check_tailnet():
    """No real tailnet name anywhere: the repository is public.

    It leaked once from a block showing install.py's output — which looks like
    a log rather than configuration, and so escaped review. This checks every
    text file, not just the units.
    """
    skip = {".git", "__pycache__", "volumes", "secrets"}
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file() or any(p in skip for p in f.parts):
            continue
        try:
            text = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        lines = text.split("\n")
        for m in TAILNET_NAME.finditer(text):
            if m.group(1) not in TAILNET_PLACEHOLDERS:
                line = text[: m.start()].count("\n") + 1
                if "check: ignore tailnet" in lines[line - 1]:
                    continue
                error("tailnet", f"{f.relative_to(ROOT)}:{line} carries a real "
                                 f"tailnet name (`{m.group(1)}`) — the repository is "
                                 f"public; use ${{TAILNET}} or <your-tailnet>")


def check_socket_label():
    """A unit that mounts Podman's socket has to say how SELinux should see it.

    `:z` labels the file, but the process stays `container_t`, which the policy
    does not let talk to the runtime. The service then starts, passes its health
    check, and sees no containers — the worst shape a failure can take, and one
    that only appears on some distributions.
    """
    for f in sorted(f for f in APPS.glob("*/*.container") if not instances.is_instance(f.parent)):
        text = f.read_text()
        monta = any(k == "Volume" and "podman.sock" in v for k, v in directives(text))
        if not monta:
            continue
        if not any(k.startswith("SecurityLabel") for k, _ in directives(text)):
            error("rule 16", f"{f.relative_to(ROOT)} mounts podman.sock without a "
                             f"SecurityLabel — on SELinux it starts healthy and sees "
                             f"nothing; use SecurityLabelType=container_runtime_t")


def check_config_sources():
    """A [config] line whose source is missing is a step that never runs.

    install.py skips it without a word, and the service starts with no
    configuration — caddy did, and only the container's own error said so.
    """
    for pasta in sorted(p for p in APPS.iterdir() if p.is_dir() and not instances.is_instance(p)):
        cp = manifest.view(pasta)
        if not cp.has_section("config"):
            continue
        for origem, _ in cp.items("config"):
            if not (pasta / origem).exists():
                error("config", f"apps/{pasta.name}/app.json: \"config\" names "
                                f"`{origem}`, which does not exist")


def check_counts(folders):
    """The counts the READMEs open with, against what the folder actually holds.

    They are prose, so nothing breaks when they drift — the number just quietly
    becomes a lie, and the next person to add a service does not think to look.
    Both languages carry the same two claims, so both are checked.
    """
    conts = sorted(ROOT.glob("apps/*/*.container"))
    notify = [u for u in conts if "Notify=healthy" in u.read_text()]
    esperado = {
        "README.md": [
            (rf"{len(folders)} self-hosted services", "the service count"),
            (rf"{len(notify)} of the {len(conts)} units use it", "the Notify=healthy count"),
        ],
        "docs/pt-BR/README.md": [
            (rf"{len(folders)} serviços self-hosted", "the service count"),
            (rf"{len(notify)} das {len(conts)} units usam", "the Notify=healthy count"),
        ],
        # The same claim, in the comment explaining why bootstrap refuses
        # podman 4.x. It was not checked and it was the one that drifted:
        # it still said 80 of 88 when the repository had reached 102 of 110.
        "bootstrap.sh": [
            (rf"{len(notify)} of the {len(conts)} units use it", "the Notify=healthy count"),
        ],
    }
    for arquivo, checagens in esperado.items():
        texto = (ROOT / arquivo).read_text()
        for frase, oque in checagens:
            if frase not in texto:
                error("counts", f"{arquivo}: {oque} is stale — it should read "
                                f"\u201c{frase}\u201d")


README_TABLES = (("en", ROOT / "README.md"), ("pt", ROOT / "docs" / "pt-BR" / "README.md"))


def regenerated_readmes(folders):
    """{path: new text} of the READMEs whose services table differs from what app.json says.

    The table is the shop window — a logo, a name, one line, in both languages — and it is generated
    from `apps/*/app.json`, between two markers, so it cannot list an app twice or forget one."""
    apps = []
    for pasta in folders:
        m = manifest.load(pasta)
        logo = manifest.icon_file(pasta)
        if m.get("title") and logo and isinstance(m.get("short_desc"), dict):
            apps.append((pasta.name, m, logo))
    if len(apps) != len(folders):
        error("table", f"only {len(apps)} of {len(folders)} apps have a title, a short_desc and a logo: "
                       f"the services table would lose the rest")
        return {}
    saida = {}
    for lang, path in README_TABLES:
        atual = path.read_text()
        novo = manifest.splice(atual, manifest.services_table(apps, lang))
        if novo is None:
            error("table", f"{path.relative_to(ROOT)} has no `{manifest.TABLE_BEGIN[:20]}…` markers around the services table")
        elif novo != atual:
            saida[path] = novo
    return saida


def check_table(folders):
    for path in regenerated_readmes(folders):
        error("table", f"{path.relative_to(ROOT)}: the services table is out of date — "
                       f"regenerate it with `python3 check.py --readme`")


HARDENING = ROOT / "docs" / "hardening.md"
LINHA_HARD = re.compile(r"^\| `([a-z0-9.-]+)` \| (yes|no) \| (.+?) \|$")


def hardening_state(path):
    """(ReadOnly, capabilities) as the unit declares them, in the table's words."""
    t = path.read_text()
    def g(k):
        return re.findall(rf"^{k}=(\S+)", t, re.M)
    ro = "yes" if g("ReadOnly") and g("ReadOnly")[0].lower() == "true" else "no"
    drop, add = g("DropCapability"), sorted({a.lower() for a in g("AddCapability")})
    if drop and drop[0].lower() == "all":
        caps = (f"{len(add)} (" + ", ".join(f"`{a}`" for a in add) + ")") if add else "**none**"
    else:
        caps = "podman default" + (f" + {len(add)} add" if add else "")
    user, userns = g("User"), g("UserNS")
    if user:
        caps += f" + `User={user[0]}`"
    elif userns:
        caps += f" + `UserNS={userns[0]}`"
    return ro, caps


def check_hardening(folders):
    """docs/hardening.md's measured state, against the units it describes.

    The table is the expensive half of the repository: every row cost a test of
    what an image tolerates. It lived outside version control and drifted —
    radicale read `podman default` while its unit dropped all and added four,
    and fourteen containers had no row at all. Both are the kind of thing only a
    check finds, because nobody reads a 110-row table top to bottom.
    """
    if not HARDENING.exists():
        error("hardening", "docs/hardening.md is missing — the measured state lives there")
        return
    linhas = {}
    for n, line in enumerate(HARDENING.read_text().splitlines(), 1):
        m = LINHA_HARD.match(line)
        if m:
            linhas[m.group(1)] = (n, m.group(2), m.group(3))
    units = {c.stem: c for f in folders for c in f.glob("*.container")}
    for nome in sorted(set(units) - set(linhas)):
        error("hardening", f"{nome} has no row in docs/hardening.md")
    for nome in sorted(set(linhas) - set(units)):
        error("hardening", f"docs/hardening.md has a row for {nome}, which is not a unit")
    for nome, (n, ro, caps) in sorted(linhas.items()):
        if nome not in units:
            continue
        real_ro, real_caps = hardening_state(units[nome])
        if (ro, caps) != (real_ro, real_caps):
            error("hardening", f"docs/hardening.md:{n}: {nome} reads `{ro} | {caps}`, "
                               f"the unit says `{real_ro} | {real_caps}`")


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

def selftest():
    # [store] repo: owner/repo on GitHub, or a full https URL
    assert repo_problemas("netbootxyz/netboot.xyz") == [] and repo_problemas("https://codeberg.org/o/r") == []
    assert repo_problemas("") and repo_problemas("not a repo") and repo_problemas("http://github.com/o/r") and repo_problemas("a/b/c")

    # .env.example type hints
    assert env_type_problemas("# CPU\n# type: number\nCORES=2\n") == []
    assert env_type_problemas("# type: number\nRAM=4G\n") and env_type_problemas("# type: nope\nX=1\n")
    assert env_type_problemas("# type: bool\n\nX=1\n"), "a hint must sit right above its setting"
    assert env_type_problemas("# type: bool\n# X=Y\n") == [], "an optional (commented) setting carries one too"

    # [backup]: mode and exclude only; exclude is relative
    import configparser as _cp
    _i = _cp.ConfigParser(interpolation=None); _i.read_string("[backup]\nmode = stop\nexclude =\n    upload/thumbs\n")
    assert backup_problemas(_i) == []
    _i.read_string("[backup]\nexclude =\n    /abs\n    a/../b\nfoo = 1\n")
    assert len(backup_problemas(_i)) == 3

    # [store] min_podman: a version like 5.4
    assert re.fullmatch(r"\d+\.\d+(\.\d+)?", "5.4") and not re.fullmatch(r"\d+\.\d+(\.\d+)?", "five")

    # the generator's stderr: an error names the unit, a warning is kept apart
    e, w = quadlet_problemas('quadlet-generator[1]: Warning: a.container specifies the image "x" which not fully\n'
                             'quadlet-generator[1]: converting "a.container": unsupported key \'Foo\' in group \'Container\' in /t/a.container\n'
                             'quadlet-generator[1]: converting "b.container": requested Quadlet unit missing.network was not found\n'
                             'quadlet-generator[1]: processing encountered some errors\n', {"a.container": 1, "b.container": 1})
    assert [x[0] for x in e] == ["a.container", "b.container"] and "unsupported key" in e[0][1], e
    assert [x[0] for x in w] == ["a.container"], w
    assert quadlet_problemas("Loading source drop-in file x\n", {}) == ([], [])
    # and the real generator, when this machine has one: it must refuse a key it does not know
    if quadlet_generator()[0] and quadlet_generator()[1] >= QUADLET_MIN:
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            pasta = Path(t, "app")
            pasta.mkdir()
            (pasta / "app.container").write_text("[Container]\nImage=docker.io/x/y:1\nFoo=bar\n")
            (pasta / "app2.container").write_text("[Container]\nImage=docker.io/x/y:1\nNetwork=missing.network\n")
            antes = len(errors)
            check_quadlet([pasta])
            novos = errors[antes:]
            del errors[antes:]
            assert any("app.container" in x and "unsupported key 'Foo'" in x for x in novos), novos
            assert any("app2.container" in x and "missing.network" in x for x in novos), novos

    # [store] deprecated: one plain line that says why
    assert deprecated_problemas("Archived upstream on 2026-03-01; no release since 1.4.2.") == []
    assert deprecated_problemas("   ") == ["is empty — say why"]
    assert deprecated_problemas("x" * 301)[0].startswith("is 301 characters")
    assert deprecated_problemas("two\nlines") and deprecated_problemas("a <b>bold</b> claim")

    # rule 9: a version or a digest pins the image; anything else floats
    assert floating_tag("docker.io/library/postgres:16") == "16"
    assert floating_tag("docker.io/library/postgres:17-alpine") == "17-alpine"
    assert floating_tag("ghcr.io/gethomepage/homepage:latest") == "latest"
    assert floating_tag("ghcr.io/x/y") == "latest", "no tag at all is latest"
    assert floating_tag("localhost:5000/y") == "latest", "a registry port is not a tag"
    assert floating_tag("docker.io/library/postgres:16.15") is None
    assert floating_tag("lscr.io/linuxserver/sabnzbd:version-5.1.3") is None
    assert floating_tag("ghcr.io/monicahq/monica-next:main@sha256:" + "a" * 64) is None
    assert floating_tag("quay.io/toolbx/arch-toolbox@sha256:" + "b" * 64) is None
    assert floating_tag("docker.io/jeankhawand/anki-sync-server:26.08-distroless") is None

    # directives() and published_port() live in qhui.py now, tested there —
    # one parser for the three tools, so a change cannot land in one of them.

    # $$ is the correct escape; a bare $ is the silent defect of rule 7
    bad = BARE_DOLLAR
    assert bad.search("test $$(date)") is None
    assert bad.search("echo $VAR") is not None
    assert bad.search("price is R$ 5") is None, "a lone dollar sign is not expansion"
    # The correct escape itself, which nothing asserted: `$$(date)` above does
    # not reach the lookbehind, because `(` is outside the character class. So
    # dropping `(?<!\$)` left the selftest green while every properly escaped
    # unit became an error — a check that condemns the fix it asks for.
    assert bad.search("echo $$VAR") is None, "the escape rule 7 asks for is not a defect"
    assert bad.search("test $${HOME}") is None, "the braced form escapes the same way"

    # the hardening table's two columns, in the words docs/hardening.md uses
    import tempfile as _tf
    with _tf.TemporaryDirectory() as d:
        u = Path(d) / "x.container"
        u.write_text("[Container]\nReadOnly=true\nDropCapability=ALL\n")
        assert hardening_state(u) == ("yes", "**none**")
        u.write_text("[Container]\nDropCapability=all\nAddCapability=CHOWN\n"
                     "AddCapability=setuid\nUser=999\n")
        assert hardening_state(u) == ("no", "2 (`chown`, `setuid`) + `User=999`")
        u.write_text("[Container]\nUserNS=keep-id\n")
        assert hardening_state(u) == ("no", "podman default + `UserNS=keep-id`"), \
            "keep-id is not hardening, but it does decide the owner"

    assert LINHA_HARD.match("| `wud` | yes | **none** |").groups() == ("wud", "yes", "**none**")
    assert LINHA_HARD.match("| Container | `ReadOnly` | Capabilities |") is None, \
        "the header is not a row"

    # PodmanArgs: the three spellings of a space, and the flag with a key of its own
    def pa(valor):
        errors.clear()
        check_podman_args(f"PodmanArgs={valor}\n", "u")
        saida = list(errors)
        errors.clear()
        return saida

    assert pa('--foo="a b"') == [], "quoting is the spelling that survives"
    assert pa("--privileged") == [], "a flag with no Quadlet key is what PodmanArgs is for"
    assert "splits" in pa("--foo=a b")[0], "unquoted, systemd makes it two arguments"
    assert "drops" in pa(r"--foo=a\ b")[0], "backslash-escaped, Quadlet emits nothing"
    assert "PidsLimit" in pa("--pids-limit=50")[0]
    assert "ShmSize" in pa("--shm-size=512m")[0]
    assert "DropCapability" in pa("--cap-drop=NET_RAW")[0]
    assert pa("--device-cgroup-rule=c 226:* rwm"), "the defect vm-chromeos shipped with"

    # o guarda de tailnet: pega nome real, aceita os placeholders
    lab = TAILNET_NAME.findall
    assert lab("https://traccar.some-real-name.ts.net") == ["some-real-name"]  # check: ignore tailnet
    assert lab("https://memos.${TAILNET}.ts.net") == ["${TAILNET}"]
    assert lab("https://x.<your-tailnet>.ts.net") == ["<your-tailnet>"]
    assert lab("https://my-app..ts.net") == [""], "TAILNET vazia é exemplo da doc"
    assert all(x in TAILNET_PLACEHOLDERS for x in
               lab("https://a.${TAILNET}.ts.net https://b.<tailnet>.ts.net"))
    assert "some-real-name" not in TAILNET_PLACEHOLDERS  # check: ignore tailnet

    # [upstream]: the four forms updates.py reads, and the ways a value looks
    # right and means nothing. Calling upstream_problema rather than restating
    # the grammar, so loosening the shipped one fails here.
    for bom in ("-", "registry", "registry:latest", r"registry:^1\.2\..*$",
                "compose:immich-app/immich:docker/docker-compose.yml",
                "compose:https://goauthentik.io/docker-compose.yml",
                "karakeep-app/karakeep"):
        assert upstream_problema(bom) is None, bom
    for ruim in ("registry: latest", "registry latest", "registry:", "registry:[",
                 "compose:immich-app/immich", "compose:immich:docker/x.yml",
                 "compose:", "karakeep", "karakeep/app/karakeep", ""):
        assert upstream_problema(ruim), ruim

    print("selftest: ok")


# --------------------------------------------------------------------------

QUADLET_GERADORES = ("/usr/libexec/podman/quadlet", "/usr/lib/podman/quadlet", "/usr/local/libexec/podman/quadlet")
QUADLET_MIN = (5, 0)             # the keys these units use (Notify=healthy, PidsLimit...) came with Podman 5


def quadlet_generator():
    """(path, (major, minor)) of Podman's Quadlet generator, or (None, None) when this machine has none."""
    import shutil
    import subprocess
    for c in (*QUADLET_GERADORES, shutil.which("quadlet") or ""):
        if c and Path(c).is_file():
            try:
                r = subprocess.run([c, "--version"], capture_output=True, text=True, timeout=20)
            except (OSError, subprocess.TimeoutExpired):
                continue
            m = re.search(r"(\d+)\.(\d+)", r.stdout + r.stderr)
            return c, (int(m.group(1)), int(m.group(2))) if m else None
    return None, None


def quadlet_problemas(stderr, donos):
    """([(unit, message)], [(unit, warning)]) from the generator's stderr.

    An error reads `converting "x.container": unsupported key 'Foo' in group 'Container'`; a warning
    `Warning: x.container specifies the image ...`. `donos` maps a unit's file name to its folder."""
    erros, avisos = [], []
    for linha in stderr.splitlines():
        m = re.search(r'converting "([^"]+)": (.+)$', linha)
        if m:
            erros.append((m.group(1), m.group(2)))
            continue
        m = re.search(r"Warning: (\S+) (.+)$", linha)
        if m and m.group(1) in donos:
            avisos.append((m.group(1), m.group(2)))
    return erros, avisos


def check_quadlet(folders, exigido=False):
    """Every unit through Podman's own generator (`quadlet -dryrun -user`), the way the host will read it.

    The rest of this file knows the mistakes this repository has made; the generator knows what
    Quadlet accepts: an unsupported key, a `Network=` that names a file that is not there, a
    section it cannot read. Those used to show up at install. It does not validate VALUES it does
    not interpret (`Notify=maybe` passes), so this is a floor and not a substitute for the rest.

    All the units go in one directory, as on the host (a name is unique across apps, rule 1): a
    `Network=tsdproxy-net.network` has to find its file. Run when the machine has a generator at
    Podman 5 or newer; `exigido` (--quadlet) makes its absence an error, which is what CI asks for."""
    import subprocess
    import tempfile
    gerador, versao = quadlet_generator()
    if not gerador or not versao or versao < QUADLET_MIN:
        if exigido:
            error("quadlet", f"no Quadlet generator at Podman {QUADLET_MIN[0]}+ here "
                             f"(found: {gerador or 'none'} {versao or ''})")
        return
    donos = {}
    with tempfile.TemporaryDirectory(prefix="qh-quadlet-") as tmp:
        for folder in folders:
            for f in sorted(folder.iterdir()):
                if f.is_file() and f.suffix in (".container", ".network", ".volume", ".image", ".build", ".pod", ".kube"):
                    donos[f.name] = folder
                    Path(tmp, f.name).write_bytes(f.read_bytes())
        env = {**os.environ, "QUADLET_UNIT_DIRS": tmp}
        r = subprocess.run([gerador, "-dryrun", "-user"], capture_output=True, text=True, env=env, timeout=120)
    erros, avisos = quadlet_problemas(r.stderr, donos)
    for unit, msg in erros:
        pasta = donos.get(unit)
        error("quadlet", f"apps/{pasta.name if pasta else '?'}/{unit}: {msg}")
    for unit, msg in avisos:
        warn("quadlet", f"apps/{donos[unit].name}/{unit}: {msg}")
    if r.returncode != 0 and not erros:
        error("quadlet", f"the generator failed ({r.returncode}): {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ''}")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return 0

    if not APPS.is_dir():
        print(loc(f"could not find {APPS}"), file=sys.stderr)
        return 2

    folders = sorted(p for p in APPS.iterdir() if p.is_dir() and not instances.is_instance(p))
    if "--readme" in sys.argv:
        feitos = regenerated_readmes(folders)
        for path, texto in feitos.items():
            path.write_text(texto)
            print(f"  {path.relative_to(ROOT)}")
        print(loc(f"{len(feitos)} README table(s) regenerated"))
        return 0
    if "--format" in sys.argv:
        feitos = 0
        for c in layout_targets(folders):
            texto = c.read_text()
            novo_texto = format_unit(texto)
            if novo_texto != texto:
                c.write_text(novo_texto)
                print(f"  {c.relative_to(ROOT)}")
                feitos += 1
        print(loc(f"{feitos} unit(s) reformatted"))
        return 0
    check_units(folders)
    check_quadlet(folders, exigido="--quadlet" in sys.argv)
    check_layout(folders)
    uses = check_ports(folders)
    check_manifest(folders)
    check_shared_labels(folders)
    check_socket_label()
    check_config_sources()
    check_counts(folders)
    check_table(folders)
    check_hardening(folders)
    check_tailnet()

    conts = sum(len(list(p.glob("*.container"))) for p in folders)
    print(dim(loc(f"{len(folders)} services, {conts} containers, "
                  f"{len(uses)} published ports")) + "\n")

    for label, cor, items in (("ERROR", red, errors), ("warn ", yellow, warnings)):
        for i in items:
            print(f"  {cor(label)}  {loc(i)}")
    if errors or warnings:
        print()
    placar = loc(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    print(red(placar) if errors else yellow(placar) if warnings else green(placar))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

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

import configparser
import re
import shlex
import sys
from collections import defaultdict
from pathlib import Path

from qhui import (translator, directives, directives_of, published_port,
                  red, yellow, green, dim)

PT = {
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
    "has neither AutoUpdate= nor wud.watch —": "não tem AutoUpdate= nem wud.watch —",
    "nothing will report a new version": "nada vai reportar versão nova",
    "published by": "publicada por",
    "has no recipe in install.ini [secrets] — install.py cannot generate it":
        "não tem receita em install.ini [secrets] — o install.py não consegue gerá-lo",
    "install.ini has a recipe for": "install.ini tem receita para",
    "is not a Secret= any unit declares": "não é um Secret= que alguma unit declare",
    "must start with `shell ` — install.py runs nothing else":
        "tem que começar com `shell ` — o install.py não roda outra coisa",
    "needs a `manual` recipe in [secrets] — a generated secret is never checked":
        "precisa de receita `manual` em [secrets] — secret gerado nunca é conferido",
    "which no unit uses": "que nenhuma unit usa",
    "which no unit declares as a Secret=": "que nenhuma unit declara como Secret=",
    "has no row in the README version table": "não tem linha na tabela de versões do README",
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
    """The .container that represents the app (the one the version table mirrors)."""
    conts = sorted(folder.glob("*.container"))
    if not conts:
        return None
    exact = folder / f"{folder.name}.container"
    if exact in conts:
        return exact
    return conts[0] if len(conts) == 1 else None


def image_tag(path):
    """The tag in `Image=`, or None when there is no comparable tag.

    An image pinned by digest (`...@sha256:abc...`) has no tag: comparing the
    hex against the README's Version column would only produce noise.
    """
    for key, value in directives_of(path):
        if key == "Image":
            if "@sha256:" in value:
                return None
            _, _, tag = value.rpartition(":")
            return tag if tag and "/" not in tag else None
    return None


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
BARE_DOLLAR = re.compile(r"(?<!\$)\$(?!\$)[A-Za-z{]")


def check_container(path, folder):
    text = path.read_text()
    ds = directives(text)
    keys = {c for c, _ in ds}
    ref = f"apps/{folder.name}/{path.name}"

    check_podman_args(text, ref)

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

    # Main container only: a sidecar (database, broker, worker) usually follows
    # the version the app's own compose validates, not its own upstream.
    if path == main_unit(folder) and "wud" not in exemptions(text):
        if "AutoUpdate" not in keys and not any(
                c == "Label" and v.startswith("wud.watch") for c, v in ds):
            warn("wud", f"{ref} has neither AutoUpdate= nor wud.watch — "
                        f"nothing will report a new version")

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


def check_manifest(folders):
    """Every Secret= has a recipe, and every .example has a known destination.

    This is what keeps install.py from stopping halfway through a service.
    """
    import configparser
    for folder in folders:
        ini = configparser.ConfigParser(interpolation=None)
        ini.read(folder / "install.ini")
        recipes = set(ini["secrets"]) if ini.has_section("secrets") else set()
        declared = set()
        for f in sorted(folder.glob("*.container")):
            for key, value in directives_of(f):
                if key == "Secret":
                    declared.add(value.split(",")[0])
        for missing in sorted(declared - recipes):
            error("manifest", f"apps/{folder.name}: Secret={missing} has no recipe in "
                              f"install.ini [secrets] — install.py cannot generate it")
        for extra in sorted(recipes - declared):
            warn("manifest", f"apps/{folder.name}: install.ini has a recipe for {extra}, "
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
                error("manifest", f"apps/{folder.name}: install.ini [{secao}] names "
                                  f"{sufixo}, which is not a unit of this folder")
        # [upstream] keys are unit names too, and its values have a grammar
        # (see upstream_problema). Neither was validated. A key naming no unit
        # is dropped by updates.py without a word, and the image falls back to
        # guessing its GitHub repository from the image name — the very guess
        # the override exists to replace.
        for key, valor in (ini.items("upstream") if ini.has_section("upstream") else []):
            if key not in unidades:
                error("manifest", f"apps/{folder.name}: install.ini [upstream] {key} "
                                  f"is not a unit of this folder")
            problema = upstream_problema(valor)
            if problema:
                error("manifest", f"apps/{folder.name}: install.ini [upstream] {key} = "
                                  f"{valor} — {problema}")
        # [login] names the secret the install prints as the credentials, in
        # either shape (`password` next to a literal user, or `credentials`
        # holding `user:password`). A typo here is silent — the footer would
        # just skip the block.
        for secao in [s for s in ini.sections() if s == "login" or s.startswith("login.")]:
            for key in ("password", "credentials"):
                name = ini.get(secao, key, fallback=None)
                if name and name not in declared:
                    error("manifest", f"apps/{folder.name}: install.ini [{secao}] {key} = "
                                      f"{name}, which no unit declares as a Secret=")
        # [validate] keys are secret names too. A typo there is worse than no
        # check at all: the install prints nothing, and you believe the value
        # was verified when it was never looked at.
        for key in (ini["validate"] if ini.has_section("validate") else ()):
            if key not in declared:
                error("manifest", f"apps/{folder.name}: install.ini [validate] {key} "
                                  f"is not a Secret= any unit declares")
            # `shell` is the only form install.py runs. Any other word makes the
            # check silently do nothing, which is worse than having none: the
            # install prints no warning and you believe the value was verified.
            elif not ini.get("validate", key, fallback="").startswith("shell "):
                error("manifest", f"apps/{folder.name}: install.ini [validate] {key} "
                                  f"must start with `shell ` — install.py runs nothing else")
            # Only a `manual` secret is ever typed, and typing is the only moment
            # there is a value to check. A recipe that generates its own has
            # nothing to validate, so the entry would never fire.
            elif not ini.get("secrets", key, fallback="").startswith("manual"):
                error("manifest", f"apps/{folder.name}: install.ini [validate] {key} "
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
    for f in sorted(APPS.glob("*/*.container")):
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
    for ini in sorted(APPS.glob("*/install.ini")):
        cp = configparser.ConfigParser(interpolation=None)
        cp.optionxform = str
        cp.read(ini)
        if not cp.has_section("config"):
            continue
        for origem, _ in cp.items("config"):
            if not (ini.parent / origem).exists():
                error("config", f"{ini.relative_to(ROOT)}: [config] names "
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


def check_table(folders):
    readme = (ROOT / "README.md").read_text()
    rows = {}
    for line in readme.splitlines():
        m = re.match(r"^\|.*?\|\s*\[[^\]]+\]\(\./apps/([a-z0-9._-]+)\)\s*\|([^|]*)\|", line)
        if m:
            rows[m.group(1)] = m.group(2).strip()

    # A repeated row is invisible to the checks below — the dict keeps the last
    # one and everything agrees. It only shows up as the same app listed twice
    # in a 64-row table, which nobody reads top to bottom.
    vistos = {}
    for line in readme.splitlines():
        m = re.match(r"^\|.*?\|\s*\[[^\]]+\]\(\./apps/([a-z0-9._-]+)\)", line)
        if m:
            vistos[m.group(1)] = vistos.get(m.group(1), 0) + 1
    for nome, n in sorted(vistos.items()):
        if n > 1:
            error("table", f"apps/{nome} appears {n} times in the README table")

    names = {p.name for p in folders}
    for missing in sorted(names - rows.keys()):
        error("table", f"apps/{missing} has no row in the README version table")
    for extra in sorted(rows.keys() - names):
        error("table", f"the README table mentions apps/{extra}, which does not exist")

    for folder in folders:
        cell = rows.get(folder.name)
        if cell is None or cell.strip() in ("—", "-", ""):
            continue  # stack with no single version (media-stack)
        unit = main_unit(folder)
        if unit is None:
            continue  # multi-container with no clear main unit
        tag = image_tag(unit)
        if tag and tag not in cell:
            error("table", f"apps/{folder.name}: Image= uses `{tag}` but the README "
                           f"table says `{cell}`")


# The "Pinned to `a`, `b`" line each service README opens its Update section
# with. Both languages carry it. Portuguese settled on "Fixado em", and
# "Pinado em" stays accepted so a line written the old way is still checked
# rather than silently skipped.
FIXADO = re.compile(r"^(?:Pinned to|Fixado em|Pinado em) ((?:`[^`]+`(?:, )?)+)")


def pinned_tags(folder):
    """Every tag the folder's units pin, sorted and deduplicated.

    An image pinned by digest has no tag, and the READMEs quote the bare hex —
    that is what the line has to match for immich's database and mdrop.
    """
    out = []
    for unit in sorted(folder.glob("*.container")):
        for key, value in directives_of(unit):
            if key == "Image":
                out.append(value.partition("@sha256:")[2]
                           or value.rpartition(":")[2])
    return sorted(set(out))


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


def check_pinned(folders):
    """The service README's own version line, against the units beside it.

    The version lives in five places: `Image=`, the two version tables, and
    this line in each README. check_table covers the first two; this line had
    no check at all, so 80 of them drifted across 40 services while CI stayed
    green — the table was right and nobody reads the other file top to bottom.

    A service may legitimately carry no such line (actual-budget follows a
    floating tag), so only a line that exists is checked.
    """
    for folder in folders:
        esperado = ", ".join(f"`{t}`" for t in pinned_tags(folder))
        if not esperado:
            continue
        for readme in sorted(folder.glob("README*.md")):
            for n, line in enumerate(readme.read_text().splitlines(), 1):
                m = FIXADO.match(line)
                if m and m.group(1) != esperado:
                    error("pinned", f"apps/{folder.name}/{readme.name}:{n}: "
                                    f"the README says {m.group(1)}, "
                                    f"the unit says {esperado}")
        check_per_unit(folder)


# A stack big enough to document each unit apart says the version twice more:
# once in `docs/<unit>.md` and once in the Version column that links to it.
# media-stack is the only one today, and it drifted in both at once.
LINHA_UNIT = re.compile(r"^\| <img.*\]\(\./docs/(?:pt-BR/)?([a-z0-9._-]+)\.md\)"
                        r".*\| `([^`]+)` \|$")


def check_per_unit(folder):
    """The per-unit page and Version column of a stack, against each unit."""
    tags = {}
    for unit in sorted(folder.glob("*.container")):
        for key, value in directives_of(unit):
            if key == "Image":
                tags[unit.stem.replace(f"{folder.name}-", "")] = (
                    value.partition("@sha256:")[2] or value.rpartition(":")[2])
    docs = sorted(folder.glob("docs/*.md")) + sorted(folder.glob("docs/*/*.md"))
    for doc in docs:
        esperado = tags.get(doc.stem)
        if not esperado:
            continue  # a page that is not named after a unit documents something else
        for n, line in enumerate(doc.read_text().splitlines(), 1):
            m = FIXADO.match(line)
            if m and m.group(1) != f"`{esperado}`":
                error("pinned", f"{doc.relative_to(ROOT)}:{n}: the README says "
                                f"{m.group(1)}, the unit says `{esperado}`")
    for readme in sorted(folder.glob("README*.md")):
        for n, line in enumerate(readme.read_text().splitlines(), 1):
            m = LINHA_UNIT.match(line)
            if not m:
                continue
            esperado = tags.get(m.group(1))
            if esperado is None or esperado == m.group(2):
                continue
            if m.group(2) == "digest" and re.fullmatch(r"[0-9a-f]{64}", esperado):
                # toolbx's Arch row: the image is pinned by digest, and sixty-four
                # hex characters in a table cell say less than the word does.
                continue
            error("pinned", f"apps/{folder.name}/{readme.name}:{n}: the README "
                            f"says `{m.group(2)}`, the unit says `{esperado}`")


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

def selftest():
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

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.container"
        p.write_text("[Container]\nImage=ghcr.io/a/b:v1.2.3\n")
        assert image_tag(p) == "v1.2.3"
        p.write_text("[Container]\nImage=quay.io/a/b\n")
        assert image_tag(p) is None, "an untagged image must not become a fake tag"
        p.write_text("[Container]\nImage=docker.io/a/b@sha256:" + "0" * 64 + "\n")
        assert image_tag(p) is None, "a digest is not a tag: nothing to compare against"

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

    # the pinned-version line, in every wording the check has to recognise
    assert FIXADO.match("Pinned to `v1.2.3`. Nothing updates on its own").group(1) == "`v1.2.3`"
    assert FIXADO.match("Fixado em `16-alpine`, `2026.5.6`. Nada").group(1) == "`16-alpine`, `2026.5.6`"
    assert FIXADO.match("Pinado em `0.6.0`. As duas imagens").group(1) == "`0.6.0`", \
        "the wording the repository moved away from is still checked"
    assert FIXADO.match("Pinned to the tag above") is None, "a sentence with no tag is not the line"
    assert FIXADO.match("> Pinned to `v1`") is None, "the line is never quoted or indented"

    # the Version column of a stack's per-unit table
    linha = ('| <img src="https://x/jellyfin.svg" width="28" height="28" alt=""> | '
             '[Jellyfin](./docs/jellyfin.md) | Plays the library | `12.0` |')
    assert LINHA_UNIT.match(linha).groups() == ("jellyfin", "12.0")
    assert LINHA_UNIT.match(linha.replace("./docs/", "./docs/pt-BR/")).group(1) == "jellyfin"
    assert LINHA_UNIT.match(linha.replace(" | `12.0` |", " |")) is None, "no version, nothing to check"

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

def main():
    if "--selftest" in sys.argv:
        selftest()
        return 0

    if not APPS.is_dir():
        print(loc(f"could not find {APPS}"), file=sys.stderr)
        return 2

    folders = sorted(p for p in APPS.iterdir() if p.is_dir())
    check_units(folders)
    uses = check_ports(folders)
    check_manifest(folders)
    check_socket_label()
    check_config_sources()
    check_counts(folders)
    check_table(folders)
    check_pinned(folders)
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

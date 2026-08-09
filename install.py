#!/usr/bin/env python3
"""Installs a service from this repository on the host, deriving the steps from the unit.

Most of what a service README tells you to do is already stated, in a
structured way, inside the `.container` itself: `Volume=` says which directory
to create, `EnvironmentFile=` says where the `.env` goes, `Secret=` says which
secrets exist, `User=` says the volume needs a `podman unshare chown`. This
script reads that and runs it.

What can NOT be derived lives in `apps/<app>/install.ini` — today only each
secret's recipe and the destination of a config file that lands inside a
directory volume.

    python3 install.py --list
    python3 install.py traccar             # dry-run: only shows what it would do
    python3 install.py traccar --apply
    python3 install.py traccar --apply --prefix /tmp/test   # sandbox

No dependencies: stdlib only.
"""

import argparse
import configparser
import os
import re
import secrets
import string
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APPS = ROOT / "apps"


def directives(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";", "[")):
            continue
        key, sep, value = line.partition("=")
        if sep:
            out.append((key.strip(), value.strip()))
    return out


# --------------------------------------------------------------------------
# secret recipes
# --------------------------------------------------------------------------

def make_secret(recipe):
    """('value', None) for what can be generated, (None, 'instruction') for manual."""
    kind, _, rest = recipe.partition(" ")
    rest = rest.strip()
    if kind == "manual":
        return None, rest
    if kind == "shell":
        out = subprocess.run(rest, shell=True, capture_output=True, text=True, check=True)
        return out.stdout.strip("\n"), None
    n = int(rest)
    if kind == "rand-hex":
        return secrets.token_hex(n), None
    if kind == "rand-base64":
        return secrets.token_urlsafe(n), None       # urlsafe avoids / and + in the value
    if kind == "rand-urlsafe":
        return secrets.token_urlsafe(n), None
    if kind == "rand-alnum":
        alpha = string.ascii_letters + string.digits
        return "".join(secrets.choice(alpha) for _ in range(n)), None
    raise ValueError(f"unknown recipe: {recipe}")


# --------------------------------------------------------------------------
# language
# --------------------------------------------------------------------------

# Translation runs over the composed line, not over each f-string. The keys are
# whole phrases, long enough that they cannot collide with a path or a service
# name, and adding a message costs one entry here either way.
PT = {
    "shows the plan": "mostra o plano",
    "(dry-run)": "(simulação)",
    "nothing was done. repeat with --apply": "nada foi feito. repita com --apply",
    "done. Check with:": "pronto. Confira com:",
    "already installed —": "já instalado —",
    "unit(s) in": "unit(s) em",
    "  --update     re-copies the units and restarts, keeping data, env and secrets":
        "  --update     recopia as units e reinicia, mantendo dados, env e secrets",
    "  --reinstall  installs again, OVERWRITING env, config and secrets":
        "  --reinstall  instala de novo, SOBRESCREVENDO env, config e secrets",
    "nothing to do for": "nada a fazer para",
    "The items marked (!) above were not done — see":
        "Os itens marcados com (!) acima não foram feitos — ver",
    "restored.": "restaurado.",
    "backup ready.": "backup pronto.",
    "removed.": "removido.",
    "cancelled.": "cancelado.",
    "type `": "digite `",
    "` to confirm: ": "` para confirmar: ",
    "FAILED at:": "FALHOU em:",
    "(follows the log while it starts)": "(acompanha o log enquanto sobe)",
    "(substituting ${TAILNET})": "(substituindo ${TAILNET})",
    "already exists — kept (use --reinstall to overwrite)":
        "já existe — mantido (use --reinstall para sobrescrever)",
    "already exists — kept (recreating changes the value and invalidates sessions/keys)":
        "já existe — mantido (recriar muda o valor e invalida sessões/chaves)",
    "has no obvious destination — declare it in install.ini [config]":
        "não tem destino óbvio — declare em install.ini [config]",
    "has no recipe in install.ini [secrets]": "não tem receita em install.ini [secrets]",
    "has a systemd variable — create it by hand once the variable is set":
        "tem variável do systemd — crie na mão depois que a variável existir",
    "does not look installed — use the normal install":
        "não parece instalado — use a instalação normal",
    "kept at the default — no terminal to ask on. Edit":
        "mantido no padrão — sem terminal para perguntar. Edite",
    "before the first start.": "antes do primeiro start.",
    "still has a placeholder — edit it before using":
        "ainda tem um placeholder — edite antes de usar",
    "not one of the listed values — using": "não está entre os valores listados — usando",
    "as given": "como veio",
    "empty — skipped, create it by hand later (see the README)":
        "vazio — pulado, crie na mão depois (ver o README)",
    "value, or Enter to generate one (not echoed): ":
        "valor, ou Enter para gerar um (não ecoado): ",
    "value (not echoed): ": "valor (não ecoado): ",
    "(sandbox, not executed:": "(sandbox, não executado:",
    "the services": "os serviços",
    "user:     ": "usuário:  ",
    "password: ": "senha:    ",
    "ask for the value of": "perguntar o valor de",
    ", or generate one": ", ou gerar um",
    "steps": "passos",
    "install,": "instalar,",
    "update,": "atualizar,",
    "reinstall,": "reinstalar,",
    "remove,": "remover,",
    "backup,": "backup,",
    "ok —": "ok —",
    'execute (without it, only show)': 'executa (sem isso, só mostra)',
    'use another home (to test without touching the real one)': 'usa outra home (pra testar sem tocar na real)',
    'list the services': 'lista os serviços',
    "test the script's parser": 'testa o parser do script',
    'shorthand for --access local': 'atalho para --access local',
    're-copies the units and restarts; touches no data, env or secret': 'recopia as units e reinicia; não toca em dados, env nem secret',
    'installs again, OVERWRITING env, config and secrets': 'instala de novo, SOBRESCREVENDO env, config e secrets',
    'stops and removes the units, keeping the data': 'para e remove as units, mantendo os dados',
    'cold backup of the data (stop, pack, bring back)': 'backup a frio dos dados (para, empacota, religa)',
    'restores a .tar.gz from --backup OVER the current data': 'restaura um .tar.gz do --backup POR CIMA dos dados atuais',
    'with --remove: also delete volumes, secrets and env': 'com --remove: apaga também volumes, secrets e env',
    'with --backup: where to write the .tar.gz (default: here)': 'com --backup: onde gravar o .tar.gz (padrão: aqui)',
    'act on ALL the services in apps/': 'age sobre TODOS os serviços de apps/',
    'one or more services, or a single unit of one ': 'um ou mais serviços, ou uma unit só de um ',
    'type each secret instead of generating it ': 'digita cada secret em vez de gerá-lo ',
    '(Enter takes the generated one)': '(Enter aceita o gerado)',
    'point the dashboard link at the LAN instead of the tailnet ': 'aponta o link do dashboard pra LAN em vez do nome da tailnet ',
    'name (implied by --access local)': '(implícito no --access local)',
    'local: no tsdproxy, link to the LAN | tailnet: link via the ': 'local: sem tsdproxy, link pra LAN | tailnet: link pelo nome da ',
    'tailnet name (default) | both: on the tailnet, with a LAN link': 'tailnet (padrão) | both: na tailnet, com link da LAN',
    "failed:": "falharam:",
}

# pt only when the environment asks for it; QH_LANG wins, so a single run can
# be forced either way without touching the locale.
_lang = (os.environ.get("QH_LANG")
         or os.environ.get("LC_ALL") or os.environ.get("LANG") or "")
PTBR = _lang.lower().startswith("pt")


# Longest first: "act on ALL the services in apps/" has to win over the
# "the services" that is a substring of it, or the line comes out half English.
_PT_ORDER = sorted(PT.items(), key=lambda kv: -len(kv[0]))


def loc(s):
    """The line as the user should read it."""
    if not PTBR:
        return s
    for en, pt in _PT_ORDER:
        if en in s:
            s = s.replace(en, pt)
    return s


def say(*a, **kw):
    """print(), translated."""
    print(*(loc(x) if isinstance(x, str) else x for x in a), **kw)


# --------------------------------------------------------------------------
# reading the service
# --------------------------------------------------------------------------

# Software this repository deliberately does NOT install via Quadlet
# (root README, rule 21): it needs to *be* the host on the network, not a
# neighbour of it.
NOT_QUADLET = {
    "tailscale": (
        "Tailscale is not a Quadlet here, on purpose (root README, rule 21):\n"
        "  it needs to integrate with the host's systemd-resolved for MagicDNS\n"
        "  to work, and a container does not share the D-Bus/mount namespace.\n"
        "\n"
        "  install the tailscale package for your distribution\n"
        "  (https://tailscale.com/download), then:\n"
        "  sudo systemctl enable --now tailscaled\n"
        "  sudo tailscale up\n"
        "\n"
        "  Then, the variable the units use in homepage.href:\n"
        "  echo 'TAILNET=<your-tailnet>' > ~/.config/environment.d/tailnet.conf\n"
        "  systemctl --user daemon-reload && systemctl --user import-environment\n"
        "\n"
        "  Only then tsdproxy: python3 install.py tsdproxy --apply"
    ),
}


def published_port(value):
    """The HOST port of a `PublishPort=`, or None when Podman picks it.

    Forms: `port`, `host:cont`, `ip:host:cont`, each with an optional `/proto`.
    A bare `port` is the container side with a random host side — nothing to
    check. Mirrors check.py's parser, which cares about the same field.
    """
    value = value.partition("/")[0]
    parts = value.split(":")
    if len(parts) < 2:
        return None
    try:
        return int(parts[-2])
    except ValueError:
        return None


def preflight(s, tailnet, local=False):
    """Warns when the host lacks what the service assumes.

    The tailnet is OPTIONAL in this repository: every service publishes a port
    on the host and works on the local network alone. What does not work
    without it is the units' `homepage.href`, which points at a `.ts.net`
    domain — hence --local.

    That is why preflight distinguishes two cases: whoever has TAILNET set is
    using a tailnet, and a stopped tailscaled is a real problem; whoever has
    nothing set only needs to know that --local exists.
    """
    problems = []

    # A privileged host port fails at start, not at install, and the message
    # podman gives ("Couldn't listen on requested ports") does not say why.
    floor = 1024
    try:
        floor = int(Path("/proc/sys/net/ipv4/ip_unprivileged_port_start").read_text())
    except (OSError, ValueError):
        pass
    low = sorted({p for p in (published_port(v) for k, v in s.ds if k == "PublishPort")
                  if p is not None and p < floor})
    if low:
        ports = ", ".join(str(p) for p in low)
        problems.append(f"host port {ports} is below this kernel's unprivileged floor "
                        f"({floor}) — rootless cannot bind it. Lower the floor once: "
                        f"sudo sysctl -w net.ipv4.ip_unprivileged_port_start={low[0]}")

    uses_tailnet = any(c == "Label" and v.startswith("tsdproxy.enable") for c, v in s.ds) \
        or any("<your-tailnet>" in ex.read_text() for ex, _ in s.examples())
    if not uses_tailnet or local:
        return problems

    import shutil
    if tailnet:
        # Wants a tailnet: a missing daemon is an error.
        if not shutil.which("tailscale"):
            problems.append("TAILNET is set but tailscale is not installed — "
                            "`python3 install.py tailscale` explains how")
        elif subprocess.run(["systemctl", "is-active", "--quiet", "tailscaled"]).returncode != 0:
            problems.append("tailscaled is not active — "
                            "`sudo systemctl enable --now tailscaled`")
    else:
        problems.append("no TAILNET: the service works locally just the same, but the "
                        "dashboard link will be broken — use --local to point it "
                        "at the LAN address")
    return problems


class Service:
    def __init__(self, name, prefix=None, only=None):
        self.name = name
        self.only = only
        self.dir = APPS / name
        if not self.dir.is_dir():
            raise SystemExit(f"apps/{name} does not exist")
        self.home = Path(prefix) if prefix else Path.home()
        # interpolation=None: the values use %h (a systemd specifier) and %s
        # (printf), which configparser's interpolator would try to expand.
        self.ini = configparser.ConfigParser(interpolation=None)
        self.ini.read(self.dir / "install.ini")

        self.units = sorted(self.dir.glob("*.container")) + sorted(self.dir.glob("*.network"))
        # What the folder holds, before any filtering: `unit_dest` reads this,
        # because installing one unit of a stack must still land in the stack's
        # subfolder alongside the others.
        self.folder_units = list(self.units)
        if only:
            chosen = self.dir / f"{only}.container"
            if not chosen.is_file():
                raise SystemExit(f"apps/{name}/{only}.container does not exist")
            # The `.network` files stay: `Network=` names the file, and Quadlet
            # cannot generate the unit without it. They are cheap and inert.
            self.units = [chosen] + sorted(self.dir.glob("*.network"))
        # Everything below — volumes, env files, secrets, examples — derives
        # from these directives, so the filter above narrows all of them at once.
        self.ds = [(k, v) for u in self.units if u.suffix == ".container"
                   for k, v in directives(u.read_text())]

    # -- destinations -----------------------------------------------------

    def _expand(self, path):
        """%h becomes the effective home; ~ likewise. Leaves ${VAR} intact on purpose."""
        return path.replace("%h", str(self.home)).replace("~", str(self.home), 1)

    @property
    def unit_dest(self):
        base = self.home / ".config/containers/systemd"
        # 1 quadlet file goes loose; 2+ get their own subfolder (root README).
        # Counted on the folder, not on the filtered set: one unit picked out of
        # a stack still belongs in the stack's subfolder.
        return base if len(self.folder_units) == 1 else base / self.name

    def volumes(self):
        """[(host_path, is_file)] for the Volume= entries that live in the home."""
        out = []
        for k, v in self.ds:
            if k != "Volume":
                continue
            host = v.split(":")[0]
            if not (host.startswith("%h") or host.startswith(str(self.home))):
                continue        # bind of a system path (e.g. /etc/localtime)
            path = self._expand(host)
            if "${" in path:
                out.append((path, None))     # systemd variable, not resolved here
                continue
            # a file if a matching .example exists for the basename
            base = Path(path).name
            is_file = (self.dir / f"{base}.example").exists()
            out.append((path, is_file))
        return out

    def env_files(self):
        # dict.fromkeys: no duplicates (a stack repeats the same EnvironmentFile
        # across several containers) while keeping declaration order.
        return list(dict.fromkeys(self._expand(v) for k, v in self.ds
                                  if k == "EnvironmentFile"))

    def secrets(self):
        names, seen = [], set()
        for k, v in self.ds:
            if k == "Secret":
                n = v.split(",")[0]
                if n not in seen:
                    seen.add(n)
                    names.append(n)
        return names

    def login(self):
        """(username, secret name) for the credential you actually type, or None.

        Only the service knows which of its secrets is the login password and
        what the username next to it is — a JWT key and an API token are also
        secrets, and neither is something you type into a form. `install.ini`
        says so explicitly rather than the script guessing.

        Two shapes, because services store it two ways. Either the username is
        fixed in the app and only the password is a secret:

            [login]
            user = admin
            password = filebrowser-admin-password

        or one secret holds both as `user:password`, because that is the form
        the app itself reads (vaultzap's basic auth). Then the username comes
        back as None and the caller splits at the first `:`, where the app
        splits too.

            [login]
            credentials = vaultzap-basic-auth
        """
        if not self.ini.has_section("login"):
            return None
        both = self.ini.get("login", "credentials", fallback=None)
        if both:
            return (None, both)
        user = self.ini.get("login", "user", fallback=None)
        secret = self.ini.get("login", "password", fallback=None)
        return (user, secret) if user and secret else None

    def installed(self):
        """The unit files of this service already on the host, in either layout.

        Both are checked because the destination depends on how many Quadlet
        files the service has: one lands flat in `systemd/`, a stack goes in
        `systemd/<app>/`. `unit_dest` alone will not do — in the flat case it
        is the shared directory, which exists the moment anything at all is
        installed. Basenames are unique across the repository (rule 1), so a
        hit is always this service's own file.
        """
        found = []
        for u in self.units:
            for p in (self.unit_dest / u.name, self.unit_dest.parent / u.name):
                if p.exists():
                    found.append(p)
                    break
        return found

    def main_unit(self):
        """The .container that represents the app — the one you `start`.

        Rule 1 of the root README: the unit name is the file's BASENAME, not
        the folder's. `apps/actual-budget/actual.container` becomes
        `actual.service`. A stack with no clear main unit (media-stack) returns
        None: which one comes up is the user's choice, and `Requires=` pulls
        the chain from there — unless the user already made that choice by
        naming a single unit, which is what `only` is.
        """
        if self.only:
            return self.dir / f"{self.only}.container"
        conts = sorted(self.dir.glob("*.container"))
        exact = self.dir / f"{self.dir.name}.container"
        if exact in conts:
            return exact
        return conts[0] if len(conts) == 1 else None

    def volume_roots(self):
        """The directories under .../volumes/ this service actually uses.

        Also not deducible from the folder name: actual-budget writes to
        volumes/actual/.
        """
        base = str(self.home / ".config/containers/volumes") + "/"
        roots = set()
        for path, _ in self.volumes():
            if path.startswith(base) and "${" not in path:
                roots.add(base + path[len(base):].split("/")[0])
        return sorted(roots)

    def uid(self):
        for k, v in self.ds:
            if k == "User":
                return v.split(":")[0]
        return None

    def images(self):
        """The `Image=` values, deduplicated, in declaration order.

        A value ending in `.build` or `.image` names another Quadlet file
        rather than a registry reference — there is nothing to pull for those.
        """
        out = []
        for k, v in self.ds:
            if k == "Image" and not v.endswith((".build", ".image")) and v not in out:
                out.append(v)
        return out

    def env_file_for(self, unit_stem):
        """That unit's own `EnvironmentFile=`, or None."""
        path = self.dir / f"{unit_stem}.container"
        if not path.is_file():
            return None
        for key, value in directives(path.read_text()):
            if key == "EnvironmentFile":
                return self._expand(value)
        return None

    def choices(self):
        """[(unit, KEY, question, [(value, label)])] from install.ini.

        For `.env` values that are a pick from a fixed list and that only
        matter on the FIRST install — the Windows edition is downloaded once
        and never revisited. Asking beats shipping a default the user then has
        to find and edit. The first option is the default.

        `[choices]` targets the service's single `.env`; `[choices.<unit>]`
        targets that unit's own, which is what a folder holding several
        independent services needs — `apps/vm` asks a different VERSION for
        Windows than for macOS, and one section could not hold both.

        configparser lowercases keys, so they come back upper-cased: these are
        environment variables.
        """
        out = []
        for section in self.ini.sections():
            if section == "choices":
                unit = None
            elif section.startswith("choices."):
                unit = section.split(".", 1)[1]
                if self.only and unit != self.only:
                    continue          # a unit this run is not installing
            else:
                continue
            for key, block in self.ini.items(section):
                lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
                if len(lines) < 2:
                    continue                  # a question with no options is not one
                opts = []
                for line in lines[1:]:
                    # `value: label`, or a bare value when it describes itself
                    value, _, label = line.partition(":")
                    opts.append((value.strip(), label.strip()))
                out.append((unit, key.upper(), lines[0], opts))
        return out

    def examples(self):
        """[(example_file, destination)] — matched by name, falling back to the ini."""
        pairs, ini_dests = [], dict(self.ini.items("config")) if self.ini.has_section("config") else {}
        vols = [c for c, _ in self.volumes()]
        envs = self.env_files()
        for ex in sorted(self.dir.glob("*.example")):
            target = ex.name[: -len(".example")]
            if ex.name in ini_dests:
                pairs.append((ex, self._expand(ini_dests[ex.name])))
                continue
            if target == ".env" and len(envs) == 1:
                # `.env.example` is the generic name: the destination is the
                # unit's single EnvironmentFile=, which carries the app's name.
                found = envs[0]
            else:
                found = next((c for c in vols if Path(c).name == target), None) \
                    or next((e for e in envs if Path(e).name == target), None)
            if found:
                pairs.append((ex, found))
            elif not self.only:
                pairs.append((ex, None))
            # With `only`, an unmatched .example belongs to one of the units we
            # filtered out (media-stack's gluetun env when installing jellyfin).
            # Reporting it as "no obvious destination" would be a false alarm.
        return pairs


# --------------------------------------------------------------------------
# plan
# --------------------------------------------------------------------------

def plan_install(s, tailnet, force=False, interactive=False, access="tailnet",
                 href_local=False, ask_secrets=False):
    steps = []      # (description, callable, or None when it is only a warning)
    warnings = []

    dest = s.unit_dest
    steps.append((f"mkdir -p {dest}", lambda: dest.mkdir(parents=True, exist_ok=True)))
    for u in s.units:
        target = dest / u.name
        mark = ""
        if access == "local":
            mark = "  (no tsdproxy, href to the LAN)"
        elif href_local:
            mark = "  (on the tailnet, href to the LAN)"
        steps.append((f"cp {u.relative_to(ROOT)} -> {target}{mark}",
                      lambda u=u, target=target: write_unit(u, target, access, href_local)))

    for path, is_file in s.volumes():
        if is_file is None:
            warnings.append(f"{path} has a systemd variable — create it by hand once the "
                            f"variable is set")
            continue
        d = Path(path).parent if is_file else Path(path)
        steps.append((f"mkdir -p {d}", lambda d=d: d.mkdir(parents=True, exist_ok=True)))

    written = []
    for ex, target in s.examples():
        if target is None:
            warnings.append(f"{ex.name} has no obvious destination — declare it in "
                            f"install.ini [config]")
            continue
        if Path(target).exists() and not force:
            # These files become the user's after the first install: they hold
            # passwords, tokens and the already-closed signup.
            warnings.append(f"{target} already exists — kept (use --reinstall to overwrite)")
            continue
        steps.append((f"cp {ex.relative_to(ROOT)} -> {target}"
                      + ("  (substituting ${TAILNET})" if tailnet else ""),
                      lambda ex=ex, target=target: write_example(ex, Path(target), tailnet)))
        written.append(target)

    # Only on a file this run actually writes: an existing .env is the user's,
    # and a question that silently rewrites it would be a trap. Must come after
    # the copy step above — the steps run in order.
    by_env = {}
    for unit, key, question, opts in s.choices():
        env = s.env_file_for(unit) if unit else \
            next((w for w in written if w in s.env_files()), None)
        if env not in written:
            continue      # that .env was kept, or belongs to a unit not installed now
        by_env.setdefault(env, []).append((key, question, opts))
    for env, items in by_env.items():
        keys = ", ".join(k for k, _, _ in items)
        if interactive:
            steps.append((f"choose {keys} in {Path(env).name}  (asks)",
                          lambda env=env, items=items: ask_choices(env, items)))
        else:
            warnings.append(f"{keys}: kept at the default — no terminal to ask on. "
                            f"Edit {env} before the first start.")

    recipes = dict(s.ini.items("secrets")) if s.ini.has_section("secrets") else {}
    for name in s.secrets():
        r = recipes.get(name)
        if not r:
            warnings.append(f"secret {name} has no recipe in install.ini [secrets]")
            continue
        if r.startswith("manual"):
            instruction = r.partition(" ")[2]
            if secret_exists(name) and not force:
                continue
            if interactive:
                steps.append((f"ask for the value of {name}  ({instruction})",
                              lambda name=name, instruction=instruction:
                                  ask_secret(s, name, instruction)))
            else:
                warnings.append(f"secret {name}: {instruction}")
            continue
        if secret_exists(name) and not force:
            warnings.append(f"secret {name} already exists — kept "
                            f"(recreating changes the value and invalidates sessions/keys)")
            continue
        if ask_secrets and interactive:
            steps.append((f"ask for the value of {name}, or generate one  ({r})",
                          lambda name=name, r=r: ask_or_generate(s, name, r)))
            continue
        steps.append((f"podman secret create {name}  ({r})",
                      lambda name=name, r=r: create_secret(s, name, r)))

    uid = s.uid()
    if uid:
        for root in s.volume_roots():
            steps.append((f"podman unshare chown -R {uid}:{uid} {root}",
                          lambda root=root: run(["podman", "unshare", "chown", "-R",
                                                 f"{uid}:{uid}", root])))

    # Before the start, not during it: systemd would pull the image too, but
    # into the journal, leaving the terminal silent for gigabytes at a time.
    steps.extend(pull_steps(s))

    steps.append(("systemctl --user daemon-reload",
                  lambda: run(["systemctl", "--user", "daemon-reload"])))

    main = s.main_unit()
    if main:
        unit = main.stem
        # restart, not start: `start` on an already-running service is a silent
        # no-op, and then a new unit, a new .env and a new secret do not take
        # effect — the container keeps the old ones. `restart` also brings up
        # what was stopped.
        cname = container_name(main) if waits_for_health(main) else None
        mark = "  (follows the log while it starts)" if cname else ""
        steps.append((f"systemctl --user restart {unit}{mark}",
                      lambda unit=unit, cname=cname: restart_unit(unit, cname)))
    else:
        names = " ".join(sorted(u.stem for u in s.units if u.suffix == ".container"))
        warnings.append(f"stack with no main unit — start the one you want: "
                        f"systemctl --user start <one of: {names}>")
    return steps, warnings


def run_lenient(cmd):
    """Like run(), but without failing: stopping what is already stopped is success."""
    if SANDBOX:
        say(f"       (sandbox, not executed: {' '.join(cmd)})")
        return
    subprocess.run(cmd, capture_output=True)


def read_secret(name):
    """The stored value, or a fallback line when podman will not give it back."""
    r = subprocess.run(["podman", "secret", "inspect", "--showsecret",
                        "--format", "{{.SecretData}}", name],
                       capture_output=True, text=True)
    return r.stdout.strip("\n") if r.returncode == 0 else f"<run: podman secret inspect --showsecret {name}>"


def secret_exists(name):
    if SANDBOX:
        return False
    r = subprocess.run(["podman", "secret", "exists", name], capture_output=True)
    return r.returncode == 0


def service_units(s):
    """Unit names (basename, rule 1) of all the service's containers."""
    return sorted(u.stem for u in s.units if u.suffix == ".container")


def plan_update(s):
    """Re-copies the units over the installed ones and restarts. Touches no
    data, env or secret.

    It is the `wget -O` over the top described in CLAUDE.md, turned into a
    script: a commit in the repository does not change the file already
    installed on the host.
    """
    steps, warnings = [], []
    dest = s.unit_dest
    if not s.installed():
        warnings.append("does not look installed — use the normal install")
    steps.append((f"mkdir -p {dest}", lambda: dest.mkdir(parents=True, exist_ok=True)))
    for u in s.units:
        target = dest / u.name
        mark = "" if target.exists() and target.read_bytes() == u.read_bytes() else "  (changed)"
        steps.append((f"cp {u.relative_to(ROOT)} -> {target}{mark}",
                      lambda u=u, target=target: target.write_bytes(u.read_bytes())))
    # The version-bump path: a changed tag means a new image, which is exactly
    # the download worth watching.
    steps.extend(pull_steps(s))
    steps.append(("systemctl --user daemon-reload",
                  lambda: run(["systemctl", "--user", "daemon-reload"])))
    main = s.main_unit()
    targets = [main.stem] if main else service_units(s)
    paths = {u.stem: u for u in s.units if u.suffix == ".container"}
    for unit in targets:
        path = paths.get(unit)
        cname = container_name(path) if path and waits_for_health(path) else None
        mark = "  (follows the log while it starts)" if cname else ""
        steps.append((f"systemctl --user restart {unit}{mark}",
                      lambda unit=unit, cname=cname: restart_unit(unit, cname)))
    return steps, warnings


def plan_backup(s, destination):
    """Cold backup of the data: stops the service, packs it, brings it back.

    Cold on purpose. Copying SQLite or Postgres while the process is writing is
    the classic recipe for an archive that only reveals itself as corrupt when
    you try to restore it — the same warning the zerobyte README makes.

    It complements [zerobyte](apps/zerobyte), it does not replace it: that one
    is the scheduled, encrypted backup, this one is the "before bumping the
    version" backup.
    """
    steps, warnings = [], []
    base = s.home / ".config/containers"
    targets = []                                # relative to ~/.config/containers

    for root in s.volume_roots():
        if Path(root).exists():
            targets.append(str(Path(root).relative_to(base)))
    if not targets:
        warnings.append("no volume found — has the service been installed?")

    # Secrets and .env are tiny and they are what makes the backup restorable:
    # without them the data comes back, but the service does not start.
    source = base / "secrets" / s.name
    if source.exists():
        targets.append(str(source.relative_to(base)))
    for e in s.env_files():
        if Path(e).exists():
            targets.append(str(Path(e).relative_to(base)))

    if not targets:
        return steps, warnings

    stamp = time.strftime("%Y%m%d-%H%M%S")
    archive = Path(destination).expanduser().resolve() / f"{s.name}-{stamp}.tar.gz"
    units = service_units(s)

    steps.append((f"systemctl --user stop {' '.join(units)}",
                  lambda: run_lenient(["systemctl", "--user", "stop", *units])))
    steps.append((f"tar czf {archive}\n         from {base}: {' '.join(targets)}",
                  lambda: tar_cmd("czf", str(archive), "-C", str(base), *targets)))
    main = s.main_unit()
    restart = [main.stem] if main else units
    for unit in restart:
        steps.append((f"systemctl --user start {unit}",
                      lambda unit=unit: run_lenient(["systemctl", "--user", "start", unit])))
    warnings.append(f"to restore: tar xzf {archive.name} -C {base}")
    return steps, warnings


def plan_restore(s, archive):
    """Restores a .tar.gz produced by --backup, over what exists today.

    It first checks that the archive belongs to THIS service: restoring the
    homebox backup on top of traccar would wipe out both at once.
    """
    steps, warnings = [], []
    base = s.home / ".config/containers"
    tgz = Path(archive).expanduser().resolve()
    if not tgz.is_file():
        return steps, [f"could not find the file {tgz}"]

    import tarfile
    try:
        with tarfile.open(tgz) as t:
            inside = t.getnames()
    except tarfile.TarError as e:
        return steps, [f"{tgz.name} is not a readable tar.gz: {e}"]

    expected = [str(Path(r).relative_to(base)) for r in s.volume_roots()]
    expected.append(f"secrets/{s.name}")
    expected += [str(Path(e).relative_to(base)) for e in s.env_files()]
    top = {n.split("/")[0] + "/" + n.split("/")[1] for n in inside if "/" in n}
    if not any(any(t.startswith(e) for e in expected) for t in top):
        return steps, [f"{tgz.name} does not look like a backup of {s.name} "
                       f"(it contains {', '.join(sorted(top)[:3])})"]

    # Restoring does not install: without the unit in place, tar would have
    # nowhere to extract to and start would not find the service. Failing here,
    # with the command that fixes it, beats a "tar: Error is not recoverable"
    # halfway through.
    if not any((s.unit_dest / u.name).exists() for u in s.units):
        return steps, [f"{s.name} is not installed — run this first: "
                       f"python3 install.py {s.name} --apply"]

    units = service_units(s)
    steps.append((f"systemctl --user stop {' '.join(units)}",
                  lambda: run_lenient(["systemctl", "--user", "stop", *units])))

    # Clear before extracting, otherwise "restore" becomes a merge: `tar x`
    # overwrites what is in the archive and leaves the rest. With SQLite that
    # corrupts — a -wal from the current state on top of an old .db is exactly
    # the bad scenario. Only the roots the archive actually carries, so a
    # partial backup does not delete what it cannot put back.
    restored = []
    for root in s.volume_roots():
        rel = str(Path(root).relative_to(base))
        if not any(n == rel or n.startswith(rel + "/") for n in inside):
            continue
        restored.append(root)
        if Path(root).exists():
            steps.append((f"rm -rf {root}   (before extracting, so it is a swap not a mix)",
                          lambda root=root: _rmtree(Path(root))))

    # unshare in both directions: as namespace-root, tar recreates the owner
    # recorded in the archive — without it, the volume of a service with User=
    # comes back wrong.
    steps.append((f"tar xzf {tgz.name} -C {base}   ({len(inside)} entries)",
                  lambda: tar_cmd("xzf", str(tgz), "-C", str(base))))
    uid = s.uid()
    if uid:
        # Only the roots the archive carries: chown on a path that was not
        # extracted fails, and since run() uses check=True that would abort the
        # plan with the service already stopped and never restarted.
        for root in restored:
            steps.append((f"podman unshare chown -R {uid}:{uid} {root}   "
                          f"(a backup from another machine carries another subuid)",
                          lambda root=root: run(["podman", "unshare", "chown", "-R",
                                                 f"{uid}:{uid}", root])))
    # The tar carries the secret's FILE, but what the service reads is the
    # podman secret — and that one disappears on --remove --purge, or never
    # existed on a fresh machine. Without recreating it, Quadlet cannot resolve
    # Secret= and the unit does not start.
    for name in s.secrets():
        source = base / "secrets" / s.name / (name.removeprefix(s.name + "-") + ".txt")
        rel = str(source.relative_to(base))
        if rel not in inside:
            continue
        steps.append((f"podman secret create {name}  (from the restored file)",
                      lambda name=name, source=source: recreate_secret(name, source)))

    main = s.main_unit()
    for unit in ([main.stem] if main else units):
        steps.append((f"systemctl --user start {unit}",
                      lambda unit=unit: run(["systemctl", "--user", "start", unit])))
    return steps, warnings


def recreate_secret(name, source):
    if secret_exists(name):
        run(["podman", "secret", "rm", name])
    run(["podman", "secret", "create", name, str(source)])


def plan_remove(s, purge):
    """Stops, removes the units and (only with --purge) deletes volumes and secrets."""
    steps, warnings = [], []
    units = service_units(s)
    steps.append((f"systemctl --user stop {' '.join(units)}",
                  lambda: run_lenient(["systemctl", "--user", "stop", *units])))
    # reset-failed: without it the 'failed' state stays dangling after the unit
    # is gone (a trap documented in CLAUDE.md).
    steps.append((f"systemctl --user reset-failed {' '.join(units)}",
                  lambda: run_lenient(["systemctl", "--user", "reset-failed", *units])))
    dest = s.unit_dest
    if dest.name == s.name and dest.is_dir():
        steps.append((f"rm -rf {dest}", lambda: _rmtree(dest)))
    else:
        for u in s.units:
            target = dest / u.name
            if target.exists():
                steps.append((f"rm {target}", lambda target=target: target.unlink()))
    steps.append(("systemctl --user daemon-reload",
                  lambda: run(["systemctl", "--user", "daemon-reload"])))

    if purge:
        for root in s.volume_roots():
            if Path(root).exists():
                steps.append((f"rm -rf {root}   ({size(root)})",
                              lambda root=root: _rmtree(Path(root))))
        for name in s.secrets():
            if secret_exists(name):
                steps.append((f"podman secret rm {name}",
                              lambda name=name: run(["podman", "secret", "rm", name])))
        source = s.home / ".config/containers/secrets" / s.name
        if source.exists():
            steps.append((f"rm -rf {source}", lambda: _rmtree(source)))
        for e in s.env_files():
            if Path(e).exists():
                steps.append((f"rm {e}", lambda e=e: Path(e).unlink()))
    else:
        kept = [r for r in s.volume_roots() if Path(r).exists()]
        if kept:
            warnings.append("data kept: " + ", ".join(f"{r} ({size(r)})" for r in kept))
        warnings.append("tsdproxy does NOT deregister the tailnet node — "
                        "remove it in the Tailscale admin")
    return steps, warnings


def tar_cmd(*args):
    """tar via `podman unshare` outside the sandbox, plain tar inside it.

    Outside, unshare is mandatory: as namespace-root it reads and recreates the
    owner of a volume belonging to a service with User=, which is a subuid.
    Inside the sandbox the files belong to the user themselves — and routing
    this through run() would make tar merely announced while the rm really
    happened, i.e. the sandbox would destroy without putting anything back.
    """
    if SANDBOX:
        subprocess.run(["tar", *args], check=True, capture_output=True, text=True)
        return
    run(["podman", "unshare", "tar", *args])


def _rmtree(path):
    """rm -rf via podman unshare: the volume of a service with User= belongs to
    a subuid, which the host user cannot delete directly."""
    if SANDBOX:
        import shutil
        shutil.rmtree(path, ignore_errors=True)
        return
    run(["podman", "unshare", "rm", "-rf", str(path)])


def size(path):
    r = subprocess.run(["podman", "unshare", "du", "-sh", str(path)],
                       capture_output=True, text=True)
    return r.stdout.split("\t")[0].strip() if r.returncode == 0 else "?"


def write_unit(source, destination, access, href_local):
    """Copies the unit, adjusting how the service becomes reachable.

    Local access works in all three modes, because every unit publishes a port
    on the host — and tsdproxy depends on exactly that port to reach the
    service. What the mode decides is whether to register a tailnet node:

      local    strips the tsdproxy labels (comments them out, does not delete)
      tailnet  keeps the labels                                     (default)
      both     keeps the labels

    And `homepage.href` follows what makes sense for each: in `local` only the
    LAN address exists; in `tailnet` and `both` the link is the tailnet name,
    which works from anywhere. Whoever prefers the short link, straight to the
    LAN without the proxy hop, adds `--href-local`.
    """
    data = source.read_bytes()
    if access == "local" or href_local:
        text = data.decode()
        port = {}
        for key, value in directives(text):
            if key == "PublishPort":
                parts = value.partition("/")[0].split(":")
                if len(parts) >= 2:
                    port[parts[-1]] = parts[-2]
        internal = next((v.partition("=")[2].rpartition(":")[2].partition("/")[0]
                         for c, v in directives(text)
                         if c == "Label" and v.startswith("tsdproxy.port.web")), None)
        host = port.get(internal) or (list(port.values())[0] if len(port) == 1 else None)
        if host:
            text = re.sub(r"(?m)^(Label=homepage\.href=).*$",
                          rf"\1http://{local_ip()}:{host}", text)
        if access == "local":
            text = re.sub(r"(?m)^(Label=tsdproxy\.)",
                          r"# disabled by --access local: \1", text)
        data = text.encode()
    destination.write_bytes(data)


def write_example(source, destination, tailnet):
    txt = source.read_text()
    if tailnet:
        txt = txt.replace("<your-tailnet>", tailnet)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(txt)
    if re.search(r"CHANGEME|<your-", txt):
        say(f"    ! {destination} still has a placeholder — edit it before using")


def set_env_value(path, key, value):
    """Set KEY=value in an already-written .env, in place.

    Replaces the existing line — including a commented-out one, which is how
    the `.example` files carry an optional setting — or appends when the key is
    not mentioned at all.
    """
    p = Path(path)
    text = p.read_text()
    line = f"{key}={value}"
    # The real setting first, a commented-out one only as a fallback. The
    # `.example` files illustrate options in comments (`#   BOOT=https://...`),
    # and rewriting one of those would leave the actual line untouched below —
    # two KEY= lines, with the wrong one winning.
    active = re.compile(rf"^{re.escape(key)}=.*$", re.M)
    commented = re.compile(rf"^#\s*{re.escape(key)}=.*$", re.M)
    for pattern in (active, commented):
        if pattern.search(text):
            p.write_text(pattern.sub(line, text, count=1))
            return
    p.write_text(text.rstrip("\n") + f"\n{line}\n")


def ask_choices(path, choices):
    """Asks for each [choices] key and writes the answers into the .env."""
    for key, question, options in choices:
        default = options[0][0]
        say(f"\n  {question}")
        for i, (value, label) in enumerate(options, 1):
            mark = "  (default)" if i == 1 else ""
            sep = "  " if label else ""
            say(f"   {i:>2}) {value:<10}{sep}{label}{mark}")
        try:
            raw = input(f"  number or value [{default}]: ").strip()
        except EOFError:
            raw = ""
        if not raw:
            picked = default
        elif raw.isdigit() and 1 <= int(raw) <= len(options):
            picked = options[int(raw) - 1][0]
        elif any(raw == v for v, _ in options):
            picked = raw
        else:
            # Not on the list is not necessarily wrong — upstream accepts a URL
            # for VERSION, for instance — so take it and say so.
            picked = raw
            say(f"  not one of the listed values — using `{raw}` as given")
        set_env_value(path, key, picked)
        say(f"  {key}={picked}")


def ask_secret(s, name, instruction):
    """Reads the value from the terminal and creates the secret.

    A `manual` secret is one that cannot be drawn at random — a password you
    are going to type, an auth key from another system, a hash produced by
    another tool. Asking right away avoids an install that ends up "almost
    done", which is when the pending step gets forgotten.
    """
    import getpass
    say(f"\n  {name}")
    say(f"  {instruction}")
    value = getpass.getpass("  value (not echoed): ").strip()
    if not value:
        say("  empty — skipped, create it by hand later (see the README)")
        return
    store_secret(s, name, value)


def ask_or_generate(s, name, recipe):
    """Type the value, or press Enter and take the generated one.

    Generated is the right default — it is long, random and nobody reuses it
    from another site. But a password you have to type into a login form every
    day is worth choosing, and the alternative was reading it back out of the
    secret and pasting it in. Enter keeps the old behaviour exactly.
    """
    import getpass
    say(f"\n  {name}  ({recipe})")
    value = getpass.getpass("  value, or Enter to generate one (not echoed): ").strip()
    store_secret(s, name, value or make_secret(recipe)[0])


def create_secret(s, name, recipe):
    value, _ = make_secret(recipe)
    store_secret(s, name, value)


def store_secret(s, name, value):
    d = s.home / ".config/containers/secrets" / s.name
    d.mkdir(parents=True, exist_ok=True)
    f = d / (name.removeprefix(s.name + "-") + ".txt")
    # No trailing newline: several apps read the raw value, and the \n becomes
    # part of the password (vaultzap with type=env is the known case here).
    f.write_text(value)
    f.chmod(0o600)
    if secret_exists(name):
        run(["podman", "secret", "rm", name])
    run(["podman", "secret", "create", name, str(f)])


SANDBOX = False     # with --prefix: touches files, not systemd nor podman


def waits_for_health(unit_path):
    """True when the unit makes systemd hold the start until it is healthy."""
    return ("Notify", "healthy") in directives(unit_path.read_text())


def container_name(unit_path):
    """The `ContainerName=`, or the unit's basename, which is what Quadlet uses."""
    for key, value in directives(unit_path.read_text()):
        if key == "ContainerName":
            return value
    return unit_path.stem


def restart_unit(unit, container=None):
    """`systemctl restart`, streaming the container's log while it blocks.

    A unit with `Notify=healthy` holds systemd until the healthcheck passes —
    up to `TimeoutStartSec`. For a service that downloads something before it
    can answer (a VM fetching a guest OS is minutes of it), that is a terminal
    that looks hung while the interesting output goes to the journal. The
    container's own log is where the progress is, so show it until systemd
    returns, then stop following.
    """
    cmd = ["systemctl", "--user", "restart", unit]
    if SANDBOX:
        say(f"       (sandbox, not executed: {' '.join(cmd)})")
        return
    if container is None:
        run(cmd)
        return

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    follow = None
    try:
        # The container does not exist until systemd creates it, and following
        # a container that is not there yet fails immediately.
        while proc.poll() is None and follow is None:
            if subprocess.run(["podman", "container", "exists", container],
                              capture_output=True).returncode == 0:
                say()
                follow = subprocess.Popen(["podman", "logs", "-f", container])
            else:
                time.sleep(0.5)
        out, err = proc.communicate()
    finally:
        if follow is not None:
            follow.terminate()
            try:
                follow.wait(timeout=5)
            except subprocess.TimeoutExpired:
                follow.kill()
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, cmd, out, err)


def image_exists(image):
    """True when the image is already on the host, so the pull step is skipped."""
    return subprocess.run(["podman", "image", "exists", image],
                          capture_output=True).returncode == 0


def pull(image):
    """Pulls with podman's own output going straight to the terminal.

    `run()` captures output, which is right for systemctl and wrong here: the
    progress bars ARE the point. Without them, a multi-gigabyte image looks
    exactly like a hung script — and the reason to pull here at all, instead of
    letting the start do it implicitly, is that systemd sends that download to
    the journal where nobody is watching it.
    """
    if SANDBOX:
        say(f"       (sandbox, not executed: podman pull {image})")
        return
    say()
    subprocess.run(["podman", "pull", image], check=True)


def moving_tag(image):
    """True when the tag can point at a different image than it did yesterday.

    `image_exists` is the right skip for a pinned tag — `:1.5.1-stable` is the
    same bytes forever, and re-pulling it is wasted time. It is exactly wrong
    for a moving tag: the local copy having the name proves nothing about it
    being current, so the pull gets skipped and `--update` silently keeps
    running yesterday's build.
    """
    tag = image.rpartition(":")[2]
    return "/" in tag or tag in ("latest", "main", "master", "edge", "nightly", "develop")


def pull_steps(s):
    """A pull step per image the host does not have yet, or whose tag moves."""
    out = []
    for image in s.images():
        if not SANDBOX and image_exists(image) and not moving_tag(image):
            continue
        out.append((f"podman pull {image}", lambda image=image: pull(image)))
    return out


def run(cmd):
    """A command that acts on the host (systemctl, podman).

    With --prefix the file destination changes, but `systemctl --user stop X`
    and `podman secret rm X` would still apply to the REAL service — so in a
    sandbox they are only announced. Without this, `--remove --prefix` would
    take down the real service.
    """
    if SANDBOX:
        say(f"       (sandbox, not executed: {' '.join(cmd)})")
        return
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def local_ip():
    """IP of the interface that reaches the network — without sending a packet.

    `connect` on a UDP socket only pins the route and fills in the local sockname.
    """
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("192.0.2.1", 9))     # TEST-NET-1, not routable
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def addresses(service, tailnet):
    """[(unit, local_url, tailnet_url)] for the containers that serve HTTP.

    Everything comes from the unit itself: `tsdproxy.port.web` says which
    INTERNAL port is the web one (a service may publish several, like traccar
    with the OsmAnd protocol port), the matching `PublishPort` gives the host
    one, and `homepage.href` already carries the tailnet URL, with only
    ${TAILNET} left to resolve.
    """
    ip = local_ip()
    out = []
    for f in sorted(service.dir.glob("*.container")):
        ds = directives(f.read_text())
        labels = {}
        for key, value in ds:
            if key == "Label":
                k, _, v = value.partition("=")
                labels[k] = v.strip('"')
        href = labels.get("homepage.href", "")
        internal = labels.get("tsdproxy.port.web", "").rpartition(":")[2].partition("/")[0]
        # It has a UI if it shows up clickable on the homepage or declares the
        # web port to tsdproxy. An MQTT broker and a sync backend publish a port
        # without having an interface — any-sync-bundle has homepage labels but
        # no href for exactly that reason.
        if not href and not internal:
            continue

        published = [v.partition("/")[0].split(":") for c, v in ds if c == "PublishPort"]
        published = [x for x in published if len(x) >= 2]
        host = None
        if internal:
            host = next((x[-2] for x in published if x[-1] == internal), None)
        elif len(published) == 1:
            # Without the label (tsdproxy auto-detects), a single port leaves no
            # doubt about which one is the interface.
            host = published[0][-2]
        if tailnet:
            href = href.replace("${TAILNET}", tailnet)
        elif "${TAILNET}" in href:
            href = ""
        out.append((f.stem,
                    f"http://{ip}:{host}" if host else None,
                    href or None))
    return out


def find_tailnet():
    """$TAILNET, or environment.d if the session has not reloaded yet.

    Substituting an empty string is the silent failure mode the root README
    describes for homepage.href — better to warn loudly and leave the
    placeholder in place.
    """
    value = os.environ.get("TAILNET", "").strip()
    if not value:
        conf = Path.home() / ".config/environment.d/tailnet.conf"
        if conf.exists():
            m = re.search(r"^TAILNET=(.*)$", conf.read_text(), re.M)
            value = m.group(1).strip() if m else ""
    return value


# --------------------------------------------------------------------------

def selftest():
    """Checks the internal-port -> host-port match, which is the part of
    `addresses()` that is easy to get silently wrong."""
    import tempfile, types
    with tempfile.TemporaryDirectory() as d:
        dd = Path(d)
        # traccar: publishes the web port AND the OsmAnd protocol; only the web
        # one must come out
        (dd / "x.container").write_text(
            "[Container]\n"
            "PublishPort=8099:8082\n"
            "PublishPort=5056:5055/udp\n"
            "Label=tsdproxy.port.web=443/https:8082/http\n"
            "Label=homepage.href=https://x.${TAILNET}.ts.net\n")
        # a broker with no web: must not show up
        (dd / "y.container").write_text("[Container]\nPublishPort=1884:1883\n")
        # a backend with homepage labels but NO href: also not a UI
        (dd / "z.container").write_text(
            "[Container]\nPublishPort=33010:33010\n"
            "Label=homepage.name=Backend\n")
        # like tsdproxy: href, no port.web, a single port
        (dd / "w.container").write_text(
            "[Container]\nPublishPort=8080:8080\n"
            "Label=homepage.href=https://dash.${TAILNET}.ts.net\n")
        fake = types.SimpleNamespace(dir=dd)
        r = {u: (l, t) for u, l, t in addresses(fake, "your-tailnet")}
        assert set(r) == {"x", "w"}, r
        assert r["x"][0].endswith(":8099"), r          # the web port, not OsmAnd's
        assert r["x"][1] == "https://x.your-tailnet.ts.net", r
        assert r["w"][0].endswith(":8080"), r          # single port, no label
        assert r["w"][1] == "https://dash.your-tailnet.ts.net", r
        no_tail = {u: t for u, _, t in addresses(fake, "")}
        assert no_tail["x"] is None, "without TAILNET it must not invent a URL"

    # store_secret: no trailing \n (it becomes part of the password) and owner-only
    global SANDBOX
    SANDBOX = True
    with tempfile.TemporaryDirectory() as d:
        svc = types.SimpleNamespace(home=Path(d), name="app")
        store_secret(svc, "app-token", "abc:123")
        f = Path(d) / ".config/containers/secrets/app/token.txt"
        assert f.read_text() == "abc:123", repr(f.read_text())
        assert f.stat().st_mode & 0o777 == 0o600, oct(f.stat().st_mode)
    SANDBOX = False

    # find_app: a folder, a unit basename, and something that is neither
    assert find_app("media-stack") == ("media-stack", None)
    assert find_app("media-stack-jellyfin") == ("media-stack", "media-stack-jellyfin")
    assert find_app("nope") == (None, None)
    # the folder wins when a unit shares its name (apps/openwa/openwa.container)
    assert find_app("openwa") == ("openwa", None)

    # picking one unit narrows the volumes to that unit's, and drops the other
    # units' .example files instead of calling them undeclared
    with tempfile.TemporaryDirectory() as d:
        full = Service("media-stack", prefix=d)
        one = Service("media-stack", prefix=d, only="media-stack-jellyfin")
        assert len(one.units) < len(full.units), (len(one.units), len(full.units))
        assert one.main_unit().stem == "media-stack-jellyfin", one.main_unit()
        assert one.unit_dest == full.unit_dest, "a picked unit stays in the stack's folder"
        assert all("jellyfin" in p for p, _ in one.volumes()), one.volumes()
        assert all(t is not None for _, t in one.examples()), one.examples()

    # [choices]: the question, the options, and set_env_value replacing a
    # commented-out line rather than appending a second one
    ch = Service("vm").choices()
    keys = sorted({k for _, k, _, _ in ch})
    assert keys == ["BOOT", "LANGUAGE", "VERSION"], keys
    # the same key asked twice, scoped to different units, is the whole point
    versions = {u for u, k, _, _ in ch if k == "VERSION"}
    # membership, not equality: a new unit asking VERSION is not a regression
    assert {"vm-windows", "vm-macos"} <= versions, versions
    win = next(o for u, k, _, o in ch if k == "VERSION" and u == "vm-windows")
    mac = next(o for u, k, _, o in ch if k == "VERSION" and u == "vm-macos")
    assert win[0][0] == "11" and ("xp", "Windows XP Professional — 0.6 GB") in win, win[0]
    assert mac[0][0] == "15" and win != mac, mac[0]
    boot = next(o for u, k, _, o in ch if k == "BOOT")
    assert boot[0][0] == "alpine", boot[0]            # first option is the default
    lang = next(o for _, k, _, o in ch if k == "LANGUAGE")
    assert lang[0] == ("English", ""), lang[0]        # a bare value keeps an empty label

    # a pinned tag is the same bytes forever; a moving one is not, and skipping
    # its pull is how `--update` silently keeps yesterday's build
    assert not moving_tag("ghcr.io/x/y:1.5.1-stable")
    assert not moving_tag("docker.io/dockurr/windows:6.04")
    assert moving_tag("ghcr.io/wallacepnts/vaultzap:latest")
    assert moving_tag("ghcr.io/x/y:main")
    # no tag at all means :latest, and the registry port must not read as one
    assert moving_tag("ghcr.io/x/y")
    assert not moving_tag("registry:5000/x/y:2.1")

    # what show_secrets() gates on: names when there are any, nothing otherwise
    assert Service("filebrowser").secrets() == ["filebrowser-admin-password",
                                                "filebrowser-jwt-secret"]
    assert Service("toolbx").secrets() == []
    # [login] picks the one secret worth printing; without the section, none
    assert Service("filebrowser").login() == ("admin", "filebrowser-admin-password")
    assert Service("homebox").login() is None       # prints nothing at all
    # the combined shape: no username of its own, the secret carries both.
    # Synthetic because no shipped service uses it right now — vaultzap did,
    # until upstream replaced its Basic Auth with a login screen, and the
    # commented-out Basic Auth path in its unit is one uncomment from needing
    # it again.
    combined = Service("vaultzap")
    combined.ini = configparser.ConfigParser(interpolation=None)
    combined.ini.read_string("[login]\ncredentials = x-basic-auth\n")
    assert combined.login() == (None, "x-basic-auth")

    # --ask-secrets swaps the generate step for a prompt, and only with a
    # terminal to prompt on
    with tempfile.TemporaryDirectory() as d:
        fb = Service("filebrowser", d)
        plain = [t for t, _ in plan_install(fb, None)[0] if "secret" in t]
        asked = [t for t, _ in plan_install(fb, None, interactive=True,
                                            ask_secrets=True)[0] if "secret" in t]
        assert all(t.startswith("podman secret create") for t in plain), plain
        assert len(asked) == len(plain) and all("ask for the value" in t for t in asked), asked
        # without a terminal the flag is ignored rather than silently skipping
        descs = lambda **kw: [t for t, _ in plan_install(fb, None, **kw)[0]]
        assert descs(ask_secrets=True) == descs()

    # the language layer: longest phrase wins, and a path is never mangled
    global PTBR
    antes = PTBR
    try:
        PTBR = True
        assert loc("act on ALL the services in apps/") == "age sobre TODOS os serviços de apps/"
        assert loc("the services") == "os serviços"
        # um caminho que contém uma palavra traduzível continua intacto
        assert loc("mkdir -p /home/x/install/data") == "mkdir -p /home/x/install/data"
        PTBR = False
        assert loc("act on ALL the services in apps/") == "act on ALL the services in apps/"
    finally:
        PTBR = antes

    # what the already-installed guard gates on, in both layouts
    with tempfile.TemporaryDirectory() as d:
        flat, stack = Service("filebrowser", d), Service("vm", d)
        assert flat.installed() == [] and stack.installed() == []
        flat.unit_dest.mkdir(parents=True, exist_ok=True)
        (flat.unit_dest / "filebrowser.container").touch()
        assert len(flat.installed()) == 1, flat.installed()
        # the flat unit sits in the same directory the stack's parent is, and
        # must not be mistaken for one of the stack's own
        assert stack.installed() == [], stack.installed()
        stack.unit_dest.mkdir(parents=True, exist_ok=True)
        (stack.unit_dest / "vm-macos.container").touch()
        assert len(stack.installed()) == 1 < len(stack.units)

    with tempfile.TemporaryDirectory() as d:
        env = Path(d) / "x.env"
        env.write_text("VERSION=11\n# LANGUAGE=Portuguese\nRAM_SIZE=4G\n")
        set_env_value(env, "VERSION", "core11")
        set_env_value(env, "LANGUAGE", "French")
        set_env_value(env, "CPU_CORES", "4")
        got = env.read_text().splitlines()
        assert got[0] == "VERSION=core11", got
        assert got[1] == "LANGUAGE=French", got       # the commented line, uncommented
        assert got.count("LANGUAGE=French") == 1, got
        assert got[-1] == "CPU_CORES=4", got          # absent key is appended

        # a commented illustration must not win over the real setting below it
        env.write_text("#   BOOT=https://example.com/x.iso\nBOOT=alpine\n")
        set_env_value(env, "BOOT", "arch")
        got = env.read_text().splitlines()
        assert got == ["#   BOOT=https://example.com/x.iso", "BOOT=arch"], got

    # images(): dedup, order, and skipping a `.build`/`.image` reference
    with tempfile.TemporaryDirectory() as d:
        fake = types.SimpleNamespace()
        fake.ds = [("Image", "docker.io/a/b:1"), ("Volume", "x:y"),
                   ("Image", "docker.io/a/b:1"), ("Image", "quay.io/c/d:2"),
                   ("Image", "local.build")]
        assert Service.images(fake) == ["docker.io/a/b:1", "quay.io/c/d:2"], \
            Service.images(fake)

    # waits_for_health / container_name: which units get the log followed
    with tempfile.TemporaryDirectory() as d:
        u = Path(d) / "svc.container"
        u.write_text("[Container]\nImage=x\nContainerName=my-app\nNotify=healthy\n")
        assert waits_for_health(u) is True
        assert container_name(u) == "my-app"
        u.write_text("[Container]\nImage=x\nNotify=healthy\n")
        assert container_name(u) == "svc", "no ContainerName= means the unit basename"
        u.write_text("[Container]\nImage=x\n")
        assert waits_for_health(u) is False, "no Notify=healthy means no waiting to narrate"

    # published_port: the host side, and the forms that have no host side
    assert published_port("445:445") == 445
    assert published_port("8006:8006") == 8006
    assert published_port("69:69/udp") == 69
    assert published_port("127.0.0.1:8082:80") == 8082
    assert published_port("69") is None, "a bare port is picked by Podman"

    say("selftest: ok")


def show_addresses(s, tailnet):
    """The URLs, raw, ready to click or paste. A stack gets the unit name above
    each one, because otherwise the bare list would not say which is which."""
    lines = addresses(s, tailnet)
    if not lines:
        return
    many = len(lines) > 1
    say()
    for unit, local, tail in lines:
        if many:
            say(f"{unit}:")
        for url in (local, tail):
            if url:
                say(f"  {url}" if many else url)


def show_secrets(s):
    """The credentials you log in with, in the clear.

    A password you cannot see is a password you cannot use, and the alternative
    was pasting a `podman secret inspect` after every install. `[login]` in
    install.ini names the one secret that is a typed password — the JWT keys and
    API tokens next to it are secrets too, and printing those would be noise for
    everyone who is never going to type them.

    It lands in the scrollback: worth knowing before you screenshot an install
    or paste its output somewhere.
    """
    login = s.login()
    # secret_exists() so a dry-run before the first install stays quiet rather
    # than printing a placeholder for something that is not there yet.
    if not login or not secret_exists(login[1]):
        return
    user, secret = login
    password = read_secret(secret)
    if user is None:
        # one secret holding `user:password` — split where the app splits
        user, _, password = password.partition(":")
    say(f"\n  user:     {user}\n  password: {password}")


def find_app(name):
    """(folder, unit) for an APP argument — a folder name, or a unit basename.

    The folder wins when both exist (they are the same service anyway:
    `apps/openwa/openwa.container`). Otherwise the basename is looked up across
    every folder, which is unambiguous by rule 1 — one basename, one unit, in
    the whole repository — and `check.py` fails the build if that ever breaks.
    """
    if (APPS / name).is_dir():
        return name, None
    hits = sorted(APPS.glob(f"*/{name}.container"))
    return (hits[0].parent.name, name) if hits else (None, None)


def run_one(a, ap, app, access, href_local):
    """Runs the chosen action for ONE service. Returns the exit code."""
    if app in NOT_QUADLET and not (APPS / app).is_dir():
        say(NOT_QUADLET[app])
        return 0

    folder, only = find_app(app)
    s = Service(folder, a.prefix, only)

    # A plain install over an installed service is never what someone means:
    # it rewrites the units and restarts, but leaves env, config and secrets
    # untouched — an update wearing the wrong name. Stop and let the caller
    # say which of the two they wanted.
    if not (a.update or a.reinstall or a.remove or a.backup or a.restore):
        here = s.installed()
        if here:
            # "1 of 6" is the case worth seeing: a stack where only some units
            # are on the host refuses too, and --reinstall is what completes it.
            say(f"{app}: already installed — {len(here)} of {len(s.units)} "
                  f"unit(s) in {here[0].parent}")
            say("  --update     re-copies the units and restarts, keeping data, "
                  "env and secrets")
            say("  --reinstall  installs again, OVERWRITING env, config and secrets")
            # Still the answer to "what was my password" — the refusal is about
            # not reinstalling, not about withholding what is already there.
            show_secrets(s)
            return 1

    tailnet = find_tailnet()
    for problem in preflight(s, tailnet, access == "local"):
        say(f"  !  {problem}")
    if a.update:
        verb, (steps, warnings) = "update", plan_update(s)
    elif a.backup:
        verb, (steps, warnings) = "backup", plan_backup(s, a.out)
    elif a.restore:
        verb, (steps, warnings) = "RESTORE (overwrites)", plan_restore(s, a.restore)
    elif a.remove:
        verb, (steps, warnings) = ("remove + DELETE DATA" if a.purge else "remove",
                                   plan_remove(s, a.purge))
    else:
        verb = "reinstall" if a.reinstall else "install"
        interactive = a.apply and not a.prefix and sys.stdin.isatty()
        if a.ask_secrets and not interactive:
            ap.error("--ask-secrets needs a terminal and --apply")
        steps, warnings = plan_install(s, tailnet, force=a.reinstall,
                                       interactive=interactive, access=access,
                                       href_local=href_local,
                                       ask_secrets=a.ask_secrets)

    if not steps:
        # With no steps, "done" would be a lie: the reason is in the warnings
        # (wrong file, nothing installed, missing volume).
        say(f"{app}: nothing to do for `{verb}`.")
        for w in warnings:
            say(f"  !  {w}")
        return 1

    say(f"{app}: {verb}, {len(steps)} steps" + ("" if a.apply else "  (dry-run)"))
    for desc, _ in steps:
        say(f"  {'->' if a.apply else '  '} {desc}")
    for w in warnings:
        say(f"  !  {w}")

    if not a.apply:
        if not (a.remove or a.backup or a.restore):
            show_addresses(s, tailnet)
            show_secrets(s)
        return 0

    if a.purge or a.restore:
        # Deleting/overwriting data is irreversible: confirm by typing the name.
        # With several services, each one asks for its own — on purpose.
        say("\nThis OVERWRITES the current data, with no way back."
              if a.restore else "\nThis DELETES the data listed above, with no way back.")
        try:
            if input(f"type `{app}` to confirm: ").strip() != app:
                say("cancelled.")
                return 1
        except (EOFError, KeyboardInterrupt):
            say("\ncancelled.")
            return 1

    for desc, action in steps:
        try:
            action()
        except subprocess.CalledProcessError as e:
            say(f"\nFAILED at: {desc}\n{(e.stderr or '').strip()}", file=sys.stderr)
            return 1
    unit = (s.main_unit() or Path(app)).stem
    if a.restore:
        say(f"\n{app}: restored.")
    elif a.backup:
        say(f"\n{app}: backup ready.")
    elif a.remove:
        say(f"\n{app} removed.")
    else:
        say(f"\n{app}: done. Check with:  systemctl --user status {unit}")
        show_addresses(s, tailnet)
        show_secrets(s)
    if warnings and not (a.remove or a.backup or a.restore):
        say("The items marked (!) above were not done — see apps/%s/README.md" % s.name)
    return 0


def main():
    # The examples in the docstring have to match how you actually invoked it:
    # installed as a `qh` symlink, telling you to type `python3 install.py`
    # sends you back to a directory you no longer need to be in.
    called = Path(sys.argv[0]).name
    how = "python3 install.py" if called.endswith(".py") else called
    ap = argparse.ArgumentParser(description=__doc__.replace("python3 install.py", how),
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("app", nargs="*", metavar="APP",
                    help=loc("one or more services, or a single unit of one "
                             "(`media-stack-jellyfin`, `toolbx-ubuntu`)"))
    ap.add_argument("--apply", action="store_true", help=loc("execute (without it, only show)"))
    ap.add_argument("--prefix", help=loc("use another home (to test without touching the real one)"))
    ap.add_argument("--list", action="store_true", help=loc("list the services"))
    ap.add_argument("--selftest", action="store_true", help=loc("test the script's parser"))
    ap.add_argument("--access", choices=("local", "tailnet", "both"), default="tailnet",
                    help=loc("local: no tsdproxy, link to the LAN | tailnet: link via the "
                             "tailnet name (default) | both: on the tailnet, with a LAN link"))
    ap.add_argument("--href-local", action="store_true",
                    help=loc("point the dashboard link at the LAN instead of the tailnet "
                             "name (implied by --access local)"))
    ap.add_argument("--local", action="store_true",
                    help=loc("shorthand for --access local"))
    action = ap.add_mutually_exclusive_group()
    action.add_argument("--update", action="store_true",
                        help=loc("re-copies the units and restarts; touches no data, env or secret"))
    action.add_argument("--reinstall", action="store_true",
                        help=loc("installs again, OVERWRITING env, config and secrets"))
    action.add_argument("--remove", action="store_true",
                        help=loc("stops and removes the units, keeping the data"))
    action.add_argument("--backup", action="store_true",
                        help=loc("cold backup of the data (stop, pack, bring back)"))
    action.add_argument("--restore", metavar="FILE",
                        help=loc("restores a .tar.gz from --backup OVER the current data"))
    ap.add_argument("--ask-secrets", action="store_true",
                    help=loc("type each secret instead of generating it "
                             "(Enter takes the generated one)"))
    ap.add_argument("--purge", action="store_true",
                    help=loc("with --remove: also delete volumes, secrets and env"))
    ap.add_argument("--out", default=".",
                    help=loc("with --backup: where to write the .tar.gz (default: here)"))
    ap.add_argument("--all", action="store_true",
                    help=loc("act on ALL the services in apps/"))
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return 0

    if a.all:
        a.app = sorted(x.name for x in APPS.iterdir() if x.is_dir())

    if a.list or not a.app:
        for p in sorted(x.name for x in APPS.iterdir() if x.is_dir()):
            say(" ", p)
        say("\n  (tailscale is not here: it is not a Quadlet, see "
              "`python3 install.py tailscale`)")
        return 0

    if a.purge and not a.remove:
        ap.error("--purge only makes sense with --remove")
    # Check the names BEFORE starting: with several services, finding out
    # halfway through that the third does not exist leaves the job half done.
    unknown = [x for x in a.app
               if x not in NOT_QUADLET and find_app(x) == (None, None)]
    if unknown:
        ap.error("not found in apps/: " + ", ".join(unknown)
                 + "  (`--list` shows what is available)")

    # A single unit out of a stack is an install/update concept only. The data
    # actions work on the folder's volume roots — `volume_roots()` collapses
    # `volumes/media-stack/jellyfin/...` to `volumes/media-stack` — so a
    # `--remove --purge` on one unit would delete the whole stack's data.
    picked = [x for x in a.app if find_app(x)[1]]
    if picked and (a.backup or a.restore or a.remove):
        ap.error(f"{', '.join(picked)}: naming a single unit works for install and "
                 f"--update only. Backup, restore and remove act on the whole "
                 f"service, whose data these units share — use the folder name.")

    if a.restore and len(a.app) > 1:
        ap.error("--restore acts on a single service: the .tar.gz belongs to one")
    if a.all and a.restore:
        ap.error("--all does not work with --restore")

    global SANDBOX
    SANDBOX = bool(a.prefix)
    # One flag, one meaning: --access decides the tailnet node, --href-local
    # decides the dashboard link. Before, --local did both things depending on
    # whether it came alone, which is the kind of behaviour nobody gets right
    # the first time.
    if a.local and "--access" in " ".join(sys.argv):
        ap.error("--local is shorthand for --access local; to change only the "
                 "link use --href-local")
    access = "local" if a.local else a.access
    href_local = a.href_local or access == "local"
    failures = []
    for i, app in enumerate(a.app):
        if len(a.app) > 1:
            say(("\n" if i else "") + "─" * 62)
        rc = run_one(a, ap, app, access, href_local)
        if rc:
            failures.append(app)

    if len(a.app) > 1:
        say("\n" + "─" * 62)
        say(f"{len(a.app) - len(failures)}/{len(a.app)} ok"
              + (f" — failed: {', '.join(failures)}" if failures else ""))
    if not a.apply:
        say("\nnothing was done. repeat with --apply")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

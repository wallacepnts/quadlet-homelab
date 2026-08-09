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

import qhui
from qhui import translator, red, yellow, green, dim, bold

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
    'tsdproxy does NOT deregister the tailnet node — remove it in the Tailscale admin': 'o tsdproxy NÃO desregistra o nó da tailnet — isso é no admin do Tailscale',
    'steps': 'passos',
    'This OVERWRITES the current data, with no way back.': 'Isso SOBRESCREVE os dados atuais, sem volta.',
    'This DELETES the data listed above, with no way back.': 'Isso APAGA os dados listados acima, sem volta.',
    'cancelled.': 'cancelado.',
    '  number or value [': '  número ou valor [',
    '  (default)': '  (padrão)',
    'could not find the file': 'não encontrei o arquivo',
    'installed and stopped:': 'instalados e parados:',
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
    "(run it with no arguments to see the list)": "(rode sem argumentos para ver a lista)",
    'To be on a tailnet, in this order:': 'Para estar numa tailnet, nesta ordem:',
    '  1. Tailscale, as a host package — not a Quadlet. It has to integrate': '  1. Tailscale, como pacote do sistema — não Quadlet. Ele precisa se',
    "     with the host's systemd-resolved for MagicDNS, and a container": '     integrar ao systemd-resolved do host pro MagicDNS, e container',
    '     does not share the D-Bus and mount namespaces.': '     não compartilha os namespaces de D-Bus e mount.',
    '     install the tailscale package for your distribution': '     instale o pacote tailscale da sua distribuição',
    '  2. The name of your tailnet, which the units use in their links:': '  2. O nome da sua tailnet, que as units usam nos links:',
    '  3. tsdproxy, which publishes every other service on the tailnet:': '  3. tsdproxy, que publica todos os outros serviços na tailnet:',
    '  Without a tailnet, install any service with --local.': '  Sem tailnet, instale qualquer serviço com --local.',
    "to join a tailnet:": "para entrar numa tailnet:",
    "(https://tailscale.com/download), then:": "(https://tailscale.com/download) e depois:",
    'Tailscale is not installed': 'Tailscale não está instalado',
    'tailscaled is not running': 'tailscaled não está rodando',
    'Tailscale is installed but not logged in': 'Tailscale instalado, mas sem login',
    'Tailscale is up': 'Tailscale no ar',
    'TAILNET is set': 'TAILNET definida',
    'TAILNET is not set': 'TAILNET não definida',
    'tsdproxy is not installed': 'tsdproxy não instalado',
    'tsdproxy is installed but not running': 'tsdproxy instalado, mas parado',
    'tsdproxy is running': 'tsdproxy rodando',
    '  pending: step': '  pendente: passo',
    '  nothing pending — you are on the tailnet.': '  nada pendente — você está na tailnet.',
    'save the rule every install and update follows ': 'salva a regra que toda instalação e atualização segue ',
    '(local, tailnet or both), and exit': '(local, tailnet ou both), e sai',
    'rule saved:': 'regra salva:',
    'every install and update follows it, unless --access says otherwise': 'toda instalação e atualização segue ela, a menos que o --access diga outra coisa',
    '  rule:': '  regra:',
    '  (default, never set)': '  (padrão, nunca definida)',
    '  change it with:  qh --set-access <local|tailnet|both>': '  mudar com:  qh --set-access <local|tailnet|both>',
    '  installed but not following it:': '  instalados que não a seguem:',
    '  bring them in line:  qh --all --update --apply': '  alinhar todos:  qh --all --update --apply',
    'what is installed, running, and changed in the repository': 'o que está instalado, rodando, e mudou no repositório',
    'nothing installed yet.': 'nada instalado ainda.',
    '  installed:': '  instalados:',
    'needing attention:': 'precisando de atenção:',
    'changed in the repository:': 'mudaram no repositório:',
    'done:': 'feito:',
    'directories': 'diretórios',
    'units and files copied': 'units e arquivos copiados',
    'secrets created': 'secrets criados',
    'images pulled': 'imagens baixadas',
    'volumes chowned': 'volumes com dono ajustado',
    'services restarted': 'serviços reiniciados',
    'services stopped': 'serviços parados',
    'archives written': 'arquivos gravados',
    'data deleted': 'dados apagados',
    'secrets removed': 'secrets removidos',
    'directory': 'diretório',
    'unit or file copied': 'unit ou arquivo copiado',
    'secret created': 'secret criado',
    'image pulled': 'imagem baixada',
    'volume chowned': 'volume com dono ajustado',
    'service restarted': 'serviço reiniciado',
    'service stopped': 'serviço parado',
    'archive written': 'arquivo gravado',
    'secret removed': 'secret removido',
    'done.': 'pronto.',
    'Check with:': 'Confira com:',
    "unit(s) in": "unit(s) em",
    "failed:": "falharam:",
}

loc = translator(PT)


def say(*a, **kw):
    """print(), translated."""
    print(*(loc(x) if isinstance(x, str) else x for x in a), **kw)


# --------------------------------------------------------------------------
# reading the service
# --------------------------------------------------------------------------

# Software this repository deliberately does NOT install via Quadlet
# (root README, rule 21): it needs to *be* the host on the network, not a
# neighbour of it.
NOT_QUADLET = {"tailscale": None}   # printed by show_tailscale()


def tailscale_steps():
    """The three steps to be on a tailnet, each with what the host actually shows.

    Printing the same instructions to someone who is already on the tailnet is
    noise; the useful answer is which step is missing. Everything here reads
    without privilege, so a check never asks for a password.
    """
    import shutil

    def ok(cmd):
        return subprocess.run(cmd, capture_output=True, text=True).returncode == 0

    steps = []

    # 1. the daemon, and whether it is logged in
    if not shutil.which("tailscale"):
        steps.append((False, loc("Tailscale is not installed"),
                      ["install the tailscale package for your distribution",
                       "(https://tailscale.com/download)"]))
    elif not ok(["systemctl", "is-active", "--quiet", "tailscaled"]):
        steps.append((False, loc("tailscaled is not running"),
                      ["sudo systemctl enable --now tailscaled"]))
    else:
        r = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True)
        ip = r.stdout.strip().splitlines()[0] if r.returncode == 0 and r.stdout.strip() else ""
        if ip:
            steps.append((True, loc("Tailscale is up") + f" ({ip})", []))
        else:
            steps.append((False, loc("Tailscale is installed but not logged in"),
                          ["sudo tailscale up"]))

    # 2. TAILNET, which every unit's link is built from
    tn = find_tailnet()
    if tn:
        steps.append((True, loc("TAILNET is set") + f" ({tn})", []))
    else:
        steps.append((False, loc("TAILNET is not set"),
                      ["mkdir -p ~/.config/environment.d",
                       "echo 'TAILNET=<your-tailnet>' > ~/.config/environment.d/tailnet.conf",
                       "systemctl --user daemon-reload"]))

    # 3. tsdproxy, which publishes everything else
    s = Service("tsdproxy")
    if not s.installed():
        steps.append((False, loc("tsdproxy is not installed"), ["qh tsdproxy --apply"]))
    elif not ok(["systemctl", "--user", "is-active", "--quiet", "tsdproxy"]):
        steps.append((False, loc("tsdproxy is installed but not running"),
                      ["systemctl --user start tsdproxy"]))
    else:
        steps.append((True, loc("tsdproxy is running"), []))

    return steps


def show_tailscale():
    steps = tailscale_steps()
    say("")
    for i, (done, titulo, cmds) in enumerate(steps, 1):
        say(f"  {green('✓') if done else yellow('·')} {i}. {titulo}")
        for c in cmds:
            say(f"       {c}")
    pend = [i for i, (d, _, _) in enumerate(steps, 1) if not d]
    say("")
    if pend:
        say(loc("  pending: step") + " " + ", ".join(map(str, pend)))
    else:
        say(loc("  nothing pending — you are on the tailnet."))
    say(loc("  Without a tailnet, install any service with --local."))


def access_drift(regra):
    """Installed services whose unit does not match the rule in force.

    A rule that only applies to what you install next is half a rule: the
    services already on the host keep whatever they were installed with, and
    nothing says so. This is what turns that into one line.
    """
    fora = []
    for d in sorted(x.name for x in APPS.iterdir() if x.is_dir()):
        s = Service(d)
        for u in s.installed():
            if installed_access(u) != regra:
                fora.append(u.stem)
                break
    return fora


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
        secao = "login"
        if self.only:
            # A stack can have one login per unit — vm-windows and vm-chromeos
            # have different users and different passwords.
            porunit = f"login.{Path(self.only).stem}"
            if self.ini.has_section(porunit):
                secao = porunit
        if not self.ini.has_section(secao):
            return None
        both = self.ini.get(secao, "credentials", fallback=None)
        if both:
            return (None, both)
        user = self.ini.get(secao, "user", fallback=None)
        secret = self.ini.get(secao, "password", fallback=None)
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

    def exclusive_volumes(self):
        """Volume directories that belong to the picked unit and to no other.

        `volume_roots()` collapses a folder to `volumes/<app>`, which is right
        for a stack that shares its data and wrong for a folder of independent
        services: purging one of media-stack's twelve would take the other
        eleven with it. A path with a systemd variable is never included —
        `${MEDIA_DATA_DIR}` is the library, not this service's data.
        """
        if not self.only:
            return None
        minhas, outras = set(), set()
        for u in self.dir.glob("*.container"):
            alvo = minhas if u.stem == self.only else outras
            for k, v in directives(u.read_text()):
                if k == "Volume":
                    origem = v.split(":")[0]
                    if "$" in origem or not origem.startswith("%h"):
                        continue
                    alvo.add(self._expand(origem))
        return sorted(minhas - outras)

    def chowns(self):
        """[(directory, uid)] — each unit's own volumes, at that unit's uid.

        Not the folder's volume root: a stack can have one unit with `User=`
        and others without, and chowning the shared root to that one uid takes
        the other containers' directories with it. immich is the case — the
        Postgres runs as 999, the server does not, and one `chown -R` on
        `volumes/immich` left the server unable to write its own uploads.
        """
        out = []
        for u in self.units:
            if u.suffix != ".container":
                continue
            texto = u.read_text()
            uid = next((v.split(":")[0] for k, v in directives(texto) if k == "User"), None)
            if not uid or uid == "0":
                continue
            for valor in (v for k, v in directives(texto) if k == "Volume"):
                origem = self._expand(valor.split(":")[0])
                if origem.startswith(str(self.home)) and "$" not in origem:
                    out.append((origem, uid))
        return out

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

    for diretorio, uid in s.chowns():
        steps.append((f"podman unshare chown -R {uid}:{uid} {diretorio}",
                      lambda d=diretorio, u=uid: run(["podman", "unshare", "chown", "-R",
                                                      f"{u}:{u}", d])))

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


ACCESS_MODES = ("local", "tailnet", "both")


def access_file(home=None):
    return (home or Path.home()) / ".config/quadlet-homelab/access"


def saved_access(home=None):
    """The mode chosen once and followed from then on, or None if never set."""
    f = access_file(home)
    if not f.exists():
        return None
    v = f.read_text().strip()
    return v if v in ACCESS_MODES else None


def save_access(mode, home=None):
    f = access_file(home)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(mode + "\n")
    return f


def installed_access(path):
    """Which --access the unit on the host was installed with.

    An update has to keep the mode it found, or a service installed with
    --local silently rejoins the tailnet on the next version bump — and one
    installed for the tailnet gets its port reopened on the LAN. The unit says
    which it is: install commented the tsdproxy labels, or the proxied port.
    """
    if not path.exists():
        return None
    text = path.read_text()
    if "# disabled by --access local:" in text:
        return "local"
    if "# reached over tsdproxy-net" in text:
        return "tailnet"
    return "both"


def plan_update(s, access="tailnet", href_local=False):
    """Re-copies the units over the installed ones and restarts. Touches no
    data, env or secret.

    It is the `wget -O` over the top described in CLAUDE.md, turned into a
    script: a commit in the repository does not change the file already
    installed on the host.
    """
    steps, warnings = [], []
    dest = s.unit_dest
    if not s.installed():
        # No steps on purpose: copying the unit without creating the volumes
        # leaves a service systemd keeps restarting until it hits the start
        # limit, and `--all --update` would do that to every service you never
        # installed.
        return [], ["does not look installed — use the normal install"]
    steps.append((f"mkdir -p {dest}", lambda: dest.mkdir(parents=True, exist_ok=True)))
    for u in s.units:
        target = dest / u.name
        modo = access or saved_access(s.home) or installed_access(target) or "tailnet"
        mark = "" if target.exists() else "  (changed)"
        steps.append((f"cp {u.relative_to(ROOT)} -> {target}  (--access {modo})",
                      lambda u=u, target=target, modo=modo:
                          write_unit(u, target, modo, href_local)))
    # The version-bump path: a changed tag means a new image, which is exactly
    # the download worth watching.
    steps.extend(pull_steps(s))
    steps.append(("systemctl --user daemon-reload",
                  lambda: run(["systemctl", "--user", "daemon-reload"])))
    # Every unit, not just the main one. A sidecar nothing declares as a
    # dependency — beszel's agent, authentik's worker, immich's ML — would be
    # copied and then never started, sitting installed with an empty journal
    # until the next login. Restarting the main one alone hid three of them.
    main = s.main_unit()
    outros = [u.stem for u in s.units if u.suffix == ".container"
              and (not main or u.stem != main.stem)]
    targets = ([main.stem] if main else []) + sorted(outros)
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
    # Per unit, like the install: one unit's User= must not chown a sibling's
    # directory. Only what the archive carries — a chown on a path that was not
    # extracted fails, and run() uses check=True, which would abort the plan
    # with the service stopped and never restarted.
    for diretorio, uid in s.chowns():
        if any(str(diretorio).startswith(str(r)) for r in restored):
            steps.append((f"podman unshare chown -R {uid}:{uid} {diretorio}   "
                          f"(a backup from another machine carries another subuid)",
                          lambda d=diretorio, u=uid: run(["podman", "unshare", "chown",
                                                          "-R", f"{u}:{u}", d])))
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
    # Only when the whole folder is being removed: with one unit picked, its
    # eleven siblings live in that same directory.
    if not s.only and dest.name == s.name and dest.is_dir():
        steps.append((f"rm -rf {dest}", lambda: _rmtree(dest)))
    else:
        for u in s.units:
            target = dest / u.name
            if target.exists():
                steps.append((f"rm {target}", lambda target=target: target.unlink()))
    steps.append(("systemctl --user daemon-reload",
                  lambda: run(["systemctl", "--user", "daemon-reload"])))

    # With a single unit picked, only what is that unit's own: its siblings keep
    # their directories, the shared .env and the secrets they also read.
    proprios = s.exclusive_volumes()
    alvos = proprios if proprios is not None else s.volume_roots()
    if purge:
        for root in alvos:
            if Path(root).exists():
                steps.append((f"rm -rf {root}   ({size(root)})",
                              lambda root=root: _rmtree(Path(root))))
        if proprios is None:
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
            warnings.append("shared .env and secrets kept — they belong to the "
                            "other units of this folder too")
    else:
        kept = [r for r in alvos if Path(r).exists()]
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


# The dashboard's one-line description, in Portuguese. It is a display string
# like every other, so it lives with them instead of doubling a label in 69
# units — and `unit_bytes` swaps it in as the unit is written, the same place
# `--access local` rewrites `homepage.href`.
DESCRICOES = {
    "A bridge between Zigbee devices and MQTT, with no proprietary hub": "Ponte entre dispositivos Zigbee e MQTT, sem hub proprietário",
    "Advanced web interface (Vue.js) for OwnTracks Recorder": "Interface web avançada (Vue.js) para o OwnTracks Recorder",
    "A light, minimal CalDAV/CardDAV server": "Servidor CalDAV/CardDAV leve e mínimo",
    "A local, browsable archive of exported WhatsApp conversations": "Acervo local e navegável de conversas exportadas do WhatsApp",
    "A macOS VM reachable in the browser, with VNC on 5900": "VM de macOS acessível no navegador, com VNC na 5900",
    "An ARM64 Windows VM, for an ARM host": "VM de Windows ARM64, para host ARM",
    "Any OS in a VM, reachable in the browser": "Qualquer sistema numa VM, acessível no navegador",
    "Audiobook and podcast server, with progress synced across devices": "Servidor de audiolivros e podcasts, com progresso sincronizado entre dispositivos",
    "Automatic subtitles": "Legendas automáticas",
    "A web file manager with search, previews and WebDAV": "Gerenciador de arquivos web com busca, prévias e WebDAV",
    "A Windows VM reachable in the browser, with RDP on 3389": "VM de Windows acessível no navegador, com RDP na 3389",
    "Backup automation (Restic)": "Automação de backup (Restic)",
    "Bookmark manager with full-text search and automatic page archiving": "Gerenciador de favoritos com busca no texto e arquivamento automático das páginas",
    "Chat interface for local LLMs (Ollama) or over an API": "Interface de chat para LLMs locais (Ollama) ou por API",
    "ChromeOS Flex in a VM, with GPU acceleration and a login on the viewer": "ChromeOS Flex numa VM, com aceleração de GPU e login no visualizador",
    "Cloud file sync and sharing (SQLite evaluation)": "Sincronização e compartilhamento de arquivos na nuvem (avaliação em SQLite)",
    "Converts PDF, Office, image and audio to Markdown, without leaving the machine": "Converte PDF, Office, imagem e áudio para Markdown, sem sair da máquina",
    "CPU/RAM/disk/network and container monitoring for this host": "Monitoramento de CPU/RAM/disco/rede e containers deste host",
    "File server with uploads from the browser, the phone or WebDAV": "Servidor de arquivos com upload pelo navegador, pelo celular ou por WebDAV",
    "Flow automation via a visual node editor": "Automação de fluxos por editor visual de nós",
    "GPS tracking — live map, history, geofences and reports": "Rastreamento GPS — mapa ao vivo, histórico, cercas e relatórios",
    "Home inventory — what you own, where it is, the receipt and the warranty": "Inventário doméstico — o que você tem, onde está, a nota e a garantia",
    "Identity server / SSO (the portal only — no forward-auth in this repository, see the README)": "Servidor de identidade / SSO (só o portal — sem forward-auth neste repositório, ver o README)",
    "Image update monitor (it never applies them itself)": "Monitor de atualização de imagens (nunca aplica nada sozinho)",
    "Indexer manager": "Gerenciador de indexadores",
    "Invoicing and invoice tracking, with no external service": "Emissão e acompanhamento de faturas, sem serviço externo",
    "IPTV manager (streams, EPG, VOD)": "Gerenciador de IPTV (streams, EPG, VOD)",
    "Local LLM server, Open WebUI's backend": "Servidor de LLM local, backend do Open WebUI",
    "Movie and TV requests (integrates with Sonarr/Radarr/Jellyfin)": "Pedidos de filmes e séries (integra com Sonarr/Radarr/Jellyfin)",
    "Movie automation": "Automação de filmes",
    "Music automation": "Automação de músicas",
    "Network PXE boot server": "Servidor de boot PXE pela rede",
    "Network-wide ad and tracker blocking over DNS": "Bloqueio de anúncios e rastreadores por DNS, para a rede toda",
    "NVR with AI object detection": "NVR com detecção de objetos por IA",
    "Offline converters, generators and calculators — everything runs in the browser": "Conversores, geradores e calculadoras offline — tudo roda no navegador",
    "P2P file sync between devices, with no central server": "Sincronização P2P de arquivos entre dispositivos, sem servidor central",
    "PDF manipulation — merge, split, convert, OCR, sign": "Manipulação de PDF — juntar, dividir, converter, OCR, assinar",
    "Personal AI agent with skills and memory, exposing an OpenAI-compatible API": "Agente de IA pessoal com habilidades e memória, expondo API compatível com a da OpenAI",
    "Personal CRM — relationships, contacts, reminders": "CRM pessoal — relacionamentos, contatos, lembretes",
    "Photo and video backup and organisation, with face recognition and smart search": "Backup e organização de fotos e vídeos, com reconhecimento facial e busca inteligente",
    "Plain-text recipes (CookLang) — versionable in git, with no database": "Receitas em texto puro (CookLang) — versionáveis em git, sem banco de dados",
    "Proxmox VE web interface, for trying it without dedicating a machine": "Interface web do Proxmox VE, para experimentar sem dedicar uma máquina",
    "Publishes containers on the tailnet automatically": "Publica containers na tailnet automaticamente",
    "Push notification server — where the uptime-kuma, wud and zerobyte alerts go": "Servidor de notificações push — para onde vão os alertas do uptime-kuma, do wud e do zerobyte",
    "Quick notes, self-hosted and markdown-native": "Notas rápidas, self-hosted e markdown-native",
    "Recurring household chores, with who does them and when they are due": "Tarefas recorrentes da casa, com quem faz e quando vence",
    "Self-hosted Anytype backend": "Backend do Anytype self-hosted",
    "Self-hosted blog/newsletter (SQLite, development mode)": "Blog/newsletter self-hosted (SQLite, modo de desenvolvimento)",
    "Self-hosted document manager": "Gerenciador de documentos self-hosted",
    "Self-hosted ebook library server": "Servidor de biblioteca de ebooks self-hosted",
    "Self-hosted Git": "Git self-hosted",
    "Self-hosted home automation": "Automação residencial self-hosted",
    "Self-hosted location tracking": "Rastreamento de localização self-hosted",
    "Self-hosted media server": "Servidor de mídia self-hosted",
    "Self-hosted password vault (Bitwarden)": "Cofre de senhas self-hosted (Bitwarden)",
    "Self-hosted personal budgeting": "Orçamento pessoal self-hosted",
    "Self-hosted RSS/Atom feed aggregator": "Agregador de feeds RSS/Atom self-hosted",
    "Self-hosted Spotify music downloader": "Baixador de músicas do Spotify self-hosted",
    "Self-hosted vehicle maintenance tracking": "Controle de manutenção de veículos self-hosted",
    "Static file server": "Servidor de arquivos estáticos",
    "Torrent client, behind the VPN": "Cliente de torrent, atrás da VPN",
    "TV series automation": "Automação de séries",
    "Uptime monitor for the services and the tailnet": "Monitor de disponibilidade dos serviços e da tailnet",
    "Usenet client": "Cliente de Usenet",
    "Web interface for yt-dlp — paste the URL and the video lands on disk": "Interface web para o yt-dlp — cole a URL e o vídeo cai no disco",
    "WhatsApp API gateway — sessions, webhooks and message sending over HTTP": "Gateway de API do WhatsApp — sessões, webhooks e envio de mensagens por HTTP",
    "Workflow automation via a visual node editor": "Automação de fluxos de trabalho por editor visual de nós",
    "Workout planning and tracking, with an exercise database and body measurements": "Planejamento e acompanhamento de treinos, com base de exercícios e medidas corporais",
    "ZimaOS in a VM — the CasaOS-derived NAS interface, without the hardware": "ZimaOS numa VM — a interface de NAS derivada do CasaOS, sem o hardware",
}

# The dashboard's groups, by what the service is for — a name is only useful
# here if it tells you where to look for something.
GRUPOS = {
    "AI": "IA",
    "Automation": "Automação",
    "Downloads": "Downloads",
    "Files": "Arquivos",
    "Home": "Casa",
    "Media": "Mídia",
    "Monitoring": "Monitoramento",
    "Network & Security": "Rede e Segurança",
    "Personal": "Pessoal",
    "Productivity": "Produtividade",
    "Tools": "Ferramentas",
    "Virtual Machines": "Máquinas Virtuais",
}


def unit_bytes(source, access, href_local):
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

    # The dashboard reads these labels; swapping them here is the same place
    # `--access local` rewrites `homepage.href`. A value with no entry keeps the
    # English rather than failing. Quotes are re-added when the translation
    # brings in a space the English did not have, because an unquoted value is
    # truncated at the first one (rule 12 of the conventions).
    if qhui.PTBR:
        for chave, tabela in ((b"description", DESCRICOES), (b"group", GRUPOS)):
            def troca(m, tabela=tabela):
                bruto = m.group(2).decode()
                novo = tabela.get(bruto.strip('"'), bruto.strip('"'))
                aspas = bruto.startswith('"') or " " in novo
                return m.group(1) + (f'"{novo}"' if aspas else novo).encode()
            data = re.sub(rb'(?m)^(Label=homepage\.' + chave + rb'=)(.*)$', troca, data)

    # On the tailnet and nowhere else: the port tsdproxy proxies is commented
    # out, so nothing of it is open on the LAN. tsdproxy still reaches the
    # container over the shared network — measured: it dials the container's own
    # IP on the internal port, which is why tsdproxy.autodetect is on the units.
    # Only that one port: a unit can also publish DNS, MQTT or a torrent port,
    # which devices reach directly and which no proxy stands in front of.
    if access == "tailnet" and not href_local:
        text = data.decode()
        web = next((v.rpartition(":")[2].partition("/")[0]
                    for c, v in directives(text)
                    if c == "Label" and v.startswith("tsdproxy.port.web")), None)
        if web:
            def hide(m):
                if m.group(0).partition("/")[0].rpartition(":")[2] != web:
                    return m.group(0)
                return "# reached over tsdproxy-net, not the LAN: " + m.group(0)
            text = re.sub(r"(?m)^PublishPort=.*$", hide, text)
            data = text.encode()

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
    return data


def write_unit(source, destination, access, href_local):
    destination.write_bytes(unit_bytes(source, access, href_local))


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
            # loc() by hand: input() does not go through say()
            raw = input(loc(f"  number or value [{default}]: ")).strip()
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
        # SANDBOX so secret_exists() answers the same on any host: the first
        # version of this test read the real podman, and passed only while both
        # secrets happened to exist.
        antes_sb = SANDBOX
        try:
            SANDBOX = True
            fb = Service("filebrowser", d)
            passos = lambda **kw: [t for t, _ in plan_install(fb, None, **kw)[0]]
            plain = [t for t in passos() if t.startswith("podman secret create")]
            asked = [t for t in passos(interactive=True, ask_secrets=True)
                     if t.startswith("ask for the value")]
            assert len(plain) == 2, plain          # senha e chave do JWT
            assert len(asked) == len(plain), (asked, plain)
        finally:
            SANDBOX = antes_sb
        # without a terminal the flag is ignored rather than silently skipping
        assert passos(ask_secrets=True) == passos()

    # tailscale_steps() reads the host, so the values vary; the shape must not
    passos = tailscale_steps()
    assert len(passos) == 3, passos
    for feito, titulo, cmds in passos:
        assert isinstance(feito, bool) and titulo and isinstance(cmds, list)
        assert feito == (not cmds), (feito, cmds)   # pendente sempre traz o comando

    # one login per unit, where a stack has more than one
    def _login(nome):
        pasta, only = find_app(nome)
        return Service(pasta, None, only).login()
    assert _login("vm-windows") == ("Docker", "vm-windows-password")
    assert _login("vm-chromeos") == ("admin", "vm-chromeos-password")
    assert _login("vm-macos") is None                  # essa não tem senha
    assert Service("proxmox").login() == ("root", "proxmox-root-password")

    # drift: what is installed against the rule in force
    for regra in ("local", "tailnet", "both"):
        fora = access_drift(regra)
        assert isinstance(fora, list) and all(isinstance(x, str) for x in fora)
    # nem toda regra pode ter tudo alinhado ao mesmo tempo
    assert not (not access_drift("local") and not access_drift("tailnet"))

    # --status reads the host, so the numbers vary; the shape must not
    assert callable(show_status)
    assert run_read(["true"]) == ""
    assert run_read(["false"]) is None
    assert run_read(["comando-que-nao-existe-xyz"]) is None

    # every dashboard label a unit carries has a Portuguese entry
    for chave, tabela in (("description", DESCRICOES), ("group", GRUPOS)):
        usadas = set()
        for u in APPS.glob("*/*.container"):
            usadas |= {v.strip('"') for v in re.findall(
                r'(?m)^Label=homepage\.' + chave + r'=(.*)$', u.read_text())}
        assert not usadas - set(tabela), (chave, sorted(usadas - set(tabela)))

    # a group whose Portuguese name has a space stays quoted, or systemd cuts it
    grupo = APPS / "vm" / "vm-windows.container"
    antes_pt = qhui.PTBR
    try:
        qhui.PTBR = True
        assert 'Label=homepage.group="Máquinas Virtuais"'.encode() in unit_bytes(grupo, "both", False)
        qhui.PTBR = False
        assert b'Label=homepage.group="Virtual Machines"' in unit_bytes(grupo, "both", False)
    finally:
        qhui.PTBR = antes_pt

    # removing one unit of a folder touches only what is that unit's own
    def _um(nome):
        pasta, only = find_app(nome)
        return Service(pasta, None, only)
    assert [str(x).split("/volumes/")[-1] for x in _um("media-stack-bazarr").exclusive_volumes()] \
        == ["media-stack/bazarr/config"], "só o diretório da unit"
    assert _um("media-stack").exclusive_volumes() is None, "pasta inteira não filtra"
    # ${MEDIA_DATA_DIR} é a biblioteca compartilhada, nunca alvo de purge
    assert not any("$" in str(x) for x in _um("media-stack-deluge").exclusive_volumes())

    # the repo column compares against what an install would write, not the raw
    # file: --access tailnet comments the proxied port out, and a byte compare
    # would report every service as changed forever
    with tempfile.TemporaryDirectory() as d:
        src = APPS / "memos" / "memos.container"
        alvo = Path(d) / "memos.container"
        write_unit(src, alvo, "tailnet", False)
        assert alvo.read_bytes() != src.read_bytes(), "tailnet comenta a porta"
        assert unit_bytes(src, "tailnet", False) == alvo.read_bytes()
        # `both` changes nothing — in English. In Portuguese the dashboard
        # description is swapped, which is a change by design.
        antes_pt = qhui.PTBR
        try:
            qhui.PTBR = False
            assert unit_bytes(src, "both", False) == src.read_bytes()
            qhui.PTBR = True
            traduzida = unit_bytes(src, "both", False)
            assert traduzida != src.read_bytes()
            assert b"Notas r" in traduzida, "a descrição do memos vira português"
        finally:
            qhui.PTBR = antes_pt

    # verbs are a closed set too: `remove` is a substring of half the sentences
    import qhui as _v
    b = _v.PTBR
    try:
        _v.PTBR = True
        assert verbo("remove", 1) == "remoção" and verbo("remove", 3) == "remoções"
        assert loc("remove it in the Tailscale admin") == "remove it in the Tailscale admin"
        _v.PTBR = False
        assert verbo("remove", 1) == "remove" and verbo("remove", 2) == "removes"
    finally:
        _v.PTBR = b

    # status words are looked up whole: `up` is a substring of `update`, and
    # the phrase translator once turned an update summary into "1 no ardate"
    import qhui as _u
    a = _u.PTBR
    try:
        _u.PTBR = True
        assert est("up") == "no ar" and est("update") == "update"
        assert loc("update") == "atualização" or "update" in loc("update")
    finally:
        _u.PTBR = a

    # colour never reaches a pipe, and never changes the text itself
    import qhui as _ui
    antes_cor = _ui.COLOR
    try:
        _ui.COLOR = False
        assert _ui.red("x") == "x" and _ui.green("y") == "y"
        _ui.COLOR = True
        assert _ui.red("x") == "\033[31mx\033[0m"
        assert len("x") == 1                       # o texto não muda, só o entorno
    finally:
        _ui.COLOR = antes_cor

    # --update on a service that is not installed does nothing: copying the
    # unit without its volumes leaves systemd restarting it to the start limit
    with tempfile.TemporaryDirectory() as d:
        passos, avisos = plan_update(Service("freshrss", d))
        assert passos == [] and avisos, (passos, avisos)

    # the summary classifies the steps it already prints; a step that no rule
    # matches would vanish from it silently
    assert classificar("mkdir -p /x") == "directories"
    assert classificar("cp a -> b") == "units and files copied"
    assert classificar("podman pull x") == "images pulled"
    assert classificar("systemctl --user restart x  (follows the log)") == "services restarted"
    assert classificar("systemctl --user daemon-reload") is None
    assert set(SINGULAR) == {r for _, r in FEITO}, "every label needs a singular"

    # the saved rule: command line beats it, it beats what the host has
    with tempfile.TemporaryDirectory() as d:
        h = Path(d)
        assert saved_access(h) is None
        save_access("local", h)
        assert saved_access(h) == "local"
        (h / ".config/quadlet-homelab/access").write_text("lixo\n")
        assert saved_access(h) is None, "valor inválido não vale como regra"

    # an update keeps the mode it finds, unless --access says otherwise
    with tempfile.TemporaryDirectory() as d:
        src, alvo = APPS / "adguardhome" / "adguardhome.container", Path(d) / "a.container"
        assert installed_access(alvo) is None                  # nada instalado
        for modo in ("local", "tailnet"):
            write_unit(src, alvo, modo, False)
            assert installed_access(alvo) == modo, modo
        write_unit(src, alvo, "both", False)
        assert installed_access(alvo) == "both"

    # only the proxied port is hidden, and only on the tailnet: a unit that also
    # publishes DNS, MQTT or a torrent port keeps those in every mode
    with tempfile.TemporaryDirectory() as d:
        src = APPS / "adguardhome" / "adguardhome.container"
        for modo, escondida in (("tailnet", True), ("local", False), ("both", False)):
            alvo = Path(d) / f"{modo}.container"
            write_unit(src, alvo, modo, False)
            linhas = [l for l in alvo.read_text().splitlines() if "PublishPort" in l]
            web = [l for l in linhas if l.rstrip().endswith("3006:3000/tcp")]
            dns = [l for l in linhas if "5335:53" in l]
            assert len(web) == 1 and len(dns) == 2, (modo, linhas)
            assert web[0].startswith("#") is escondida, (modo, web)
            assert not any(l.startswith("#") for l in dns), (modo, dns)

    # the language layer: longest phrase wins, and a path is never mangled
    antes = qhui.PTBR
    try:
        qhui.PTBR = True
        assert loc("act on ALL the services in apps/") == "age sobre TODOS os serviços de apps/"
        assert loc("the services") == "os serviços"
        # um caminho que contém uma palavra traduzível continua intacto
        assert loc("mkdir -p /home/x/install/data") == "mkdir -p /home/x/install/data"
        qhui.PTBR = False
        assert loc("act on ALL the services in apps/") == "act on ALL the services in apps/"
    finally:
        qhui.PTBR = antes

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


def show_addresses(s, tailnet, modo="both"):
    """The URLs, raw, ready to click or paste, for the mode it was installed in.

    Printing the LAN address of a service whose LAN port was just closed sends
    you to a connection refused; printing a tailnet name for one installed
    `--local` sends you to a name that does not resolve. A stack gets the unit
    name above each one, because otherwise the bare list would not say which is
    which.
    """
    lines = addresses(s, tailnet)
    if not lines:
        return
    many = len(lines) > 1
    saida = []
    for unit, local, tail in lines:
        quais = {"local": (local,), "tailnet": (tail,)}.get(modo, (local, tail))
        urls = [u for u in quais if u]
        if urls:
            saida.append((unit, urls))
    if not saida:
        return
    say()
    for unit, urls in saida:
        if many:
            say(f"{unit}:")
        for url in urls:
            say(f"  {url}" if many else url)


def run_read(cmd):
    """stdout of a read-only command, or None when it is not available."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


VERBOS = {
    "install": ("instalação", "instalações"),
    "reinstall": ("reinstalação", "reinstalações"),
    "update": ("atualização", "atualizações"),
    "remove": ("remoção", "remoções"),
    "remove + DELETE DATA": ("remoção com APAGAR DADOS", "remoções com APAGAR DADOS"),
    "backup": ("backup", "backups"),
    "RESTORE (overwrites)": ("RESTAURAÇÃO (sobrescreve)", "RESTAURAÇÕES (sobrescrevem)"),
}


def verbo(v, n):
    """A closed set too: `remove` is a substring of half the sentences here."""
    if not qhui.PTBR:
        return v if n == 1 else v + "s"
    par = VERBOS.get(v)
    return (par[0] if n == 1 else par[1]) if par else v


ESTADOS = {
    "service": "serviço", "unit": "unit", "container": "container", "repo": "repo",
    "active": "ativo", "inactive": "inativo", "failed": "falhou",
    "activating": "iniciando", "deactivating": "parando",
    "healthy": "saudável", "unhealthy": "doente", "up": "no ar", "down": "parado",
    "changed": "mudou",
}


def est(v):
    """A closed set of words, looked up whole.

    Not through the phrase translator: `up` is a substring of `update`, and a
    three hundred line run once ended in "1 no ardate".
    """
    return ESTADOS.get(v, v) if qhui.PTBR else v


def show_status(apps=None):
    """What is installed, what is running, and what drifted from the repository.

    One row per service: a folder with several units collapses into `2/12`,
    because the question at this level is "is this service up", not which of
    its twelve pieces. Naming services expands those into a row each.
    """
    ativos, saude = {}, {}
    r = run_read(["systemctl", "--user", "list-units", "--type=service",
                  "--all", "--no-legend", "--plain"])
    for linha in (r or "").splitlines():
        campos = linha.split()
        if len(campos) >= 4 and campos[0].endswith(".service"):
            ativos[campos[0][:-8]] = campos[2]
    r = run_read(["podman", "ps", "-a", "--format", "{{.Names}}|{{.Status}}"])
    for linha in (r or "").splitlines():
        nome, _, estado = linha.partition("|")
        saude[nome] = estado

    def estado_container(u):
        cont = next((v for k, v in directives(u.read_text())
                     if k == "ContainerName"), u.stem)
        c = saude.get(cont, "—")
        return ("healthy" if "healthy" in c else
                "unhealthy" if "unhealthy" in c else
                "up" if c.startswith("Up") else
                "—" if c == "—" else "down")

    linhas, problemas, mudados, escondidas = [], 0, 0, 0
    for d in sorted(x.name for x in APPS.iterdir() if x.is_dir()):
        if apps and d not in apps:
            continue
        s = Service(d)
        units = [u for u in s.installed() if u.suffix == ".container"]
        if not units:
            continue
        detalhe = []
        for u in units:
            fonte = APPS / d / u.name
            deriva = ""
            if fonte.exists():
                modo = installed_access(u) or "tailnet"
                deriva = "changed" if unit_bytes(fonte, modo, modo == "local") != u.read_bytes() else ""
            e, c = ativos.get(u.stem, "—"), estado_container(u)
            if e != "active" or c in ("unhealthy", "down"):
                problemas += 1
            if deriva:
                mudados += 1
            detalhe.append((u.stem, e, c, deriva or "—"))
        # In a folder of independent services, an inactive unit is one you chose
        # not to start — noise, not news. In a real stack (its own .network) an
        # inactive piece is why the service is down, so those stay. `failed`
        # always stays: that one nobody chose.
        stack = any(u.suffix == ".network" for u in s.units)
        if apps or stack:
            linhas += detalhe
        else:
            visiveis = [x for x in detalhe if x[1] != "inactive"]
            escondidas += len(detalhe) - len(visiveis)
            linhas += visiveis

    if not linhas:
        say(loc("nothing installed yet."))
        return 0

    def coluna(v, largura, bons=(), ruins=()):
        """Translate, colour, then pad by the visible text: an escape code has
        width 0, so padding the coloured string collapses every column after."""
        cor = green if v in bons else red if v in ruins else dim
        texto = est(v)
        return cor(texto) + " " * max(0, largura - len(texto))

    say(dim(f"  {est('service'):<26} {est('unit'):<10} {est('container'):<10} {est('repo')}"))
    for n, e, c, dv in linhas:
        say(f"  {n:<26} {coluna(e, 10, ('active',), ('failed',))}"
            f" {coluna(c, 10, ('healthy', 'up'), ('unhealthy', 'down'))}"
            f" {yellow(est(dv)) if dv == 'changed' else dim(dv)}")
    say("")
    say(loc("  installed:") + f" {sum(1 for _ in linhas)}  "
        + loc("needing attention:") + f" {problemas}  "
        + loc("changed in the repository:") + f" {mudados}"
        + (f"  {loc('installed and stopped:')} {escondidas}" if escondidas else ""))
    return 1 if problemas else 0


# What each executed step counts as, matched on the description it already
# prints. Keeping the classification here means a new step shows up in the
# summary without a second place to update.
FEITO = (
    ("mkdir -p ", "directories"),
    ("cp ", "units and files copied"),
    ("podman secret create", "secrets created"),
    ("ask for the value of", "secrets created"),
    ("podman pull", "images pulled"),
    ("podman unshare chown", "volumes chowned"),
    ("systemctl --user restart", "services restarted"),
    ("systemctl --user stop", "services stopped"),
    ("tar ", "archives written"),
    ("rm -rf ", "data deleted"),
    ("podman secret rm", "secrets removed"),
)


SINGULAR = {
    "directories": "directory",
    "units and files copied": "unit or file copied",
    "secrets created": "secret created",
    "images pulled": "image pulled",
    "volumes chowned": "volume chowned",
    "services restarted": "service restarted",
    "services stopped": "service stopped",
    "archives written": "archive written",
    "data deleted": "data deleted",
    "secrets removed": "secret removed",
}


def classificar(desc):
    for prefixo, rotulo in FEITO:
        if desc.startswith(prefixo) or f" {prefixo}" in desc[:20]:
            return rotulo
    return None


def show_summary(feitos, verbos):
    """What actually ran, once, at the end.

    With one service the step list above is the summary; with `--all` it is
    three hundred lines, and the question left is "so what changed".
    """
    if not feitos:
        return
    say("")
    resumo = ", ".join(f"{n} {loc(SINGULAR[r] if n == 1 else r)}"
                       for r, n in sorted(feitos.items(), key=lambda kv: -kv[1]))
    porverbo = ", ".join(f"{n} {verbo(v, n)}" for v, n in sorted(verbos.items()))
    say(green(loc("done:")) + f" {porverbo}")
    say(f"  {resumo}")


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


def run_one(a, ap, app, access, href_local, feitos=None, verbos=None):
    feitos = {} if feitos is None else feitos
    verbos = {} if verbos is None else verbos
    """Runs the chosen action for ONE service. Returns the exit code."""
    if app in NOT_QUADLET and not (APPS / app).is_dir():
        show_tailscale()
        return 0

    folder, only = find_app(app)
    s = Service(folder, a.prefix, only)

    # A plain install over an installed service is never what someone means:
    # it rewrites the units and restarts, but leaves env, config and secrets
    # untouched — an update wearing the wrong name. Stop and let the caller
    # say which of the two they wanted.
    if not (a.update or a.reinstall or a.remove or a.backup or a.restore):
        here = s.installed()
        # Half installed does not count: a unit whose volumes were never created
        # can only fail, and refusing the plain install would send you to
        # --reinstall, which overwrites env and secrets to fix what is missing.
        completo = here and all(Path(c).exists() for c, arq in s.volumes()
                                if arq is not None)
        if here and completo:
            # "1 of 6" is the case worth seeing: a stack where only some units
            # are on the host refuses too, and --reinstall is what completes it.
            # `1/1` instead of "1 of 1": a word interpolated between two
            # translated halves is a word that stays English.
            say(f"{app}: {yellow(loc('already installed —'))}"
                f" {len(here)}/{len(s.units)} " + loc("unit(s) in")
                + f" {here[0].parent}")
            say("  --update     re-copies the units and restarts, keeping data, "
                  "env and secrets")
            say("  --reinstall  installs again, OVERWRITING env, config and secrets")
            # Still the answer to "what was my password" — the refusal is about
            # not reinstalling, not about withholding what is already there.
            show_secrets(s)
            return 1

    tailnet = find_tailnet()
    # Same precedence plan_update uses, so the address printed at the end is the
    # one the unit actually got: what you typed, then the saved rule, then what
    # the host already had.
    primeira = s.installed()
    modo_efetivo = (access or saved_access(s.home)
                    or (installed_access(primeira[0]) if primeira else None) or "tailnet")
    for problem in preflight(s, tailnet, modo_efetivo == "local"):
        say(f"  !  {problem}")
    if a.update:
        verb, (steps, warnings) = "update", plan_update(s, access, href_local)
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
                                       interactive=interactive,
                                       access=access or saved_access(s.home) or "tailnet",
                                       href_local=href_local,
                                       ask_secrets=a.ask_secrets)

    if not steps:
        # With no steps, "done" would be a lie: the reason is in the warnings
        # (wrong file, nothing installed, missing volume).
        say(f"{app}: nothing to do for `{verb}`.")
        for w in warnings:
            say(f"  !  {w}")
        return 1

    say(f"{app}: {verbo(verb, 1)}, {len(steps)} " + loc("steps")
        + ("" if a.apply else "  " + loc("(dry-run)")))
    if a.apply:
        verbos[verb] = verbos.get(verb, 0) + 1
    for desc, _ in steps:
        say(f"  {'->' if a.apply else '  '} {desc}")
    for w in warnings:
        say(f"  {yellow('!')}  {w}")

    if not a.apply:
        if not (a.remove or a.backup or a.restore):
            show_addresses(s, tailnet, modo_efetivo)
            if not a.update:
                show_secrets(s)
        return 0

    if a.purge or a.restore:
        # Deleting/overwriting data is irreversible: confirm by typing the name.
        # With several services, each one asks for its own — on purpose.
        say("\nThis OVERWRITES the current data, with no way back."
              if a.restore else "\nThis DELETES the data listed above, with no way back.")
        try:
            # loc() by hand: input() does not go through say()
            if input(loc(f"type `{app}` to confirm: ")).strip() != app:
                say("cancelled.")
                return 1
        except (EOFError, KeyboardInterrupt):
            say("\ncancelled.")
            return 1

    for desc, action in steps:
        try:
            action()
            rotulo = classificar(desc)
            if rotulo:
                feitos[rotulo] = feitos.get(rotulo, 0) + 1
        except subprocess.CalledProcessError as e:
            say(f"\n{red('FAILED at:')} {desc}\n{(e.stderr or '').strip()}", file=sys.stderr)
            return 1
    unit = (s.main_unit() or Path(app)).stem
    if a.restore:
        say(f"\n{app}: restored.")
    elif a.backup:
        say(f"\n{app}: backup ready.")
    elif a.remove:
        say(f"\n{app} removed.")
    else:
        say(f"\n{app}: {green(loc('done.'))} " + loc("Check with:")
            + f"  systemctl --user status {unit}")
        show_addresses(s, tailnet, modo_efetivo)
        # Not on an update: it changes no credential, and `qh --all --update`
        # would spill every password in the terminal at once. `qh <app>` still
        # prints it, which is the deliberate way to look one up.
        if not a.update:
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
    ap.add_argument("--selftest", action="store_true", help=loc("test the script's parser"))
    ap.add_argument("--status", action="store_true",
                    help=loc("what is installed, running, and changed in the repository"))
    ap.add_argument("--set-access", choices=ACCESS_MODES, metavar="MODE",
                    help=loc("save the rule every install and update follows "
                             "(local, tailnet or both), and exit"))
    ap.add_argument("--access", choices=ACCESS_MODES, default=None,
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

    if a.status:
        return show_status(a.app or None)

    if a.set_access:
        f = save_access(a.set_access, Path(a.prefix) if a.prefix else None)
        say(loc("rule saved:") + f" {a.set_access}  ({f})")
        say(loc("every install and update follows it, unless --access says otherwise"))
        return 0

    if a.all:
        a.app = sorted(x.name for x in APPS.iterdir() if x.is_dir())

    if not a.app:
        for p in sorted(x.name for x in APPS.iterdir() if x.is_dir()):
            say(" ", p)
        regra = saved_access()
        say(loc("\n  rule:") + f" --access {regra or 'tailnet'}"
            + ("" if regra else loc("  (default, never set)")))
        say(loc("  change it with:  qh --set-access <local|tailnet|both>"))
        fora = access_drift(regra or "tailnet")
        if fora:
            say(loc("  installed but not following it:") + f" {len(fora)}"
                + f" ({', '.join(fora[:4])}{', …' if len(fora) > 4 else ''})")
            say(loc("  bring them in line:  qh --all --update --apply"))
        # Only when there is something to join: telling someone already on a
        # tailnet how to join one is the kind of line that trains people to
        # stop reading the output.
        if any(not feito for feito, _, _ in tailscale_steps()):
            say(loc("  to join a tailnet:  qh tailscale"))
        return 0

    if a.purge and not a.remove:
        ap.error("--purge only makes sense with --remove")
    # Check the names BEFORE starting: with several services, finding out
    # halfway through that the third does not exist leaves the job half done.
    unknown = [x for x in a.app
               if x not in NOT_QUADLET and find_app(x) == (None, None)]
    if unknown:
        ap.error("not found in apps/: " + ", ".join(unknown)
                 + "  (run it with no arguments to see the list)")

    # Backup and restore always take the folder: the archive is the service's,
    # and restoring one piece of a stack over data the others share is how you
    # corrupt it. Remove is allowed on a single unit when that unit's volumes
    # are its own — media-stack's twelve each have a directory nobody else
    # touches, and refusing there was protecting nothing.
    picked = [x for x in a.app if find_app(x)[1]]
    if picked and (a.backup or a.restore):
        ap.error(f"{', '.join(picked)}: naming a single unit works for install, "
                 f"--update and --remove. Backup and restore act on the whole "
                 f"service's data — use the folder name.")
    if picked and a.remove:
        compartilham = [x for x in picked
                        if not Service(*[y for y in find_app(x)][:1],
                                       a.prefix, find_app(x)[1]).exclusive_volumes()]
        if compartilham:
            ap.error(f"{', '.join(compartilham)}: this unit's volumes are shared with "
                     f"the rest of the service — removing it alone would take their "
                     f"data too. Use the folder name.")

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
    # None means "not stated": an update then keeps the mode the host already
    # has, and a fresh install falls back to the default.
    access = "local" if a.local else a.access
    href_local = a.href_local or access == "local"
    failures, feitos, verbos = [], {}, {}
    for i, app in enumerate(a.app):
        if len(a.app) > 1:
            say(("\n" if i else "") + "─" * 62)
        rc = run_one(a, ap, app, access, href_local, feitos, verbos)
        if rc:
            failures.append(app)

    if len(a.app) > 1:
        say("\n" + "─" * 62)
        say(f"{len(a.app) - len(failures)}/{len(a.app)} ok"
              + (f" — failed: {', '.join(failures)}" if failures else ""))
    # Not for the entries that only print instructions: nothing was going to be
    # done for them with --apply either, so the line would be a wrong nudge.
    if a.apply:
        show_summary(feitos, verbos)
    elif any(x not in NOT_QUADLET for x in a.app):
        say("\nnothing was done. repeat with --apply")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

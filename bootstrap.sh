#!/usr/bin/env bash
# Gets this repository onto a fresh host and hands you install.py.
#
#   curl -fsSL https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/bootstrap.sh | bash
#   curl -fsSL .../bootstrap.sh | bash -s -- memos     # and show the plan for one service
#
# What it deliberately does NOT do:
#
#   - run as root. Every service here is rootless Podman under `systemd --user`;
#     nothing in this repository writes outside your home. A bootstrap asking
#     for sudo would be the wrong shape for what it installs.
#   - install packages. Which command that is depends on your distribution, and
#     on an immutable one it also needs a reboot — not a thing to trigger from
#     a pipe.
#   - install a service. `install.py` is dry-run by default on purpose: you read
#     the plan, then you run it with --apply. Piping to bash does not change that.
set -euo pipefail

REPO=${REPO:-https://github.com/wallacepnts/quadlet-homelab}
DEST=${DEST:-$HOME/quadlet-homelab}

say()  { printf '  %s\n' "$*"; }
fail() { printf '\n  %s\n' "$*" >&2; exit 1; }

# Portuguese when the environment asks for it; QH_LANG wins, so a single run can
# be forced either way. Each message is a variable, chosen once, because two
# blocks of assignments read better in shell than translating strings at print.
case "${QH_LANG:-${LC_ALL:-${LANG:-}}}" in
pt*)
    M_ROOT="não rode isto como root — ver o cabeçalho deste script."
    M_MISSING="faltando:"
    M_INSTALL1="Instale com o gerenciador de pacotes da sua distribuição e rode"
    M_INSTALL2="de novo. Em sistema imutável o comando é outro e exige reboot."
    M_DEPSOK="git, python3, podman: ok"
    M_OLD1="é antigo demais — 5.0 ou mais novo é obrigatório (Notify=healthy)."
    M_OLD2="atualize o podman, ou use uma distribuição que traga 5.x."
    M_NOSD="systemd --user não está rodando para este usuário (tente: loginctl enable-linger $USER)"
    M_SDOK="systemd --user: ok"
    M_DIRS="~/.config/containers/{systemd,secrets,env,volumes}: prontos"
    M_NOFF="não consegui avançar" ; M_NOFF2="— deixando como está"
    M_UPD="atualizado" ; M_CLONED="clonado em"
    M_NOTGIT="existe e não é um clone git — mova, ou defina DEST="
    M_TAKEN=": já há outro arquivo aí — deixado em paz"
    M_NOPATH="~/.local/bin ainda não está no PATH. Acrescente esta linha ao rc do seu shell:"
    M_PLAN="o plano de" ; M_PLAN2="(nada foi feito ainda):"
    M_TORUN="para executar:"
    M_NEXT="a seguir:"
    M_C1="  qh                 # os serviços"
    M_C2="  qh memos           # o plano de um, sem instalar"
    M_C3="  qh memos --apply   # fazer"
    M_ASK="Como os serviços devem ficar acessíveis?"
    M_A1="  1) só na LAN         porta no host, sem tailnet"
    M_A2="  2) só na tailnet     nome HTTPS próprio, porta fechada na LAN  [padrão]"
    M_A3="  3) ambos             na tailnet e na LAN"
    M_CHOICE="1, 2 ou 3 (Enter para o padrão):"
    M_SAVED="regra salva:"
    ;;
*)
    M_ROOT="do not run this as root — see the header of this script."
    M_MISSING="missing:"
    M_INSTALL1="Install them with your distribution's package manager, then run this"
    M_INSTALL2="again. On an immutable system the command differs and needs a reboot."
    M_DEPSOK="git, python3, podman: ok"
    M_OLD1="is too old — 5.0 or newer is required (Notify=healthy)."
    M_OLD2="upgrade podman, or use a distribution that ships 5.x."
    M_NOSD="systemd --user is not running for this user (try: loginctl enable-linger $USER)"
    M_SDOK="systemd --user: ok"
    M_DIRS="~/.config/containers/{systemd,secrets,env,volumes}: ready"
    M_NOFF="could not fast-forward" ; M_NOFF2="— leaving it alone"
    M_UPD="updated" ; M_CLONED="cloned into"
    M_NOTGIT="exists and is not a git clone — move it or set DEST="
    M_TAKEN=": a different file is already there — left alone"
    M_NOPATH="~/.local/bin is not in PATH yet. Add this line to your shell's rc file:"
    M_PLAN="the plan for" ; M_PLAN2="(nothing is done yet):"
    M_TORUN="to run it:"
    M_NEXT="next:"
    M_C1="  qh                 # the services"
    M_C2="  qh memos           # the plan for one, without installing"
    M_C3="  qh memos --apply   # do it"
    M_ASK="How should the services be reachable?"
    M_A1="  1) LAN only          a port on the host, no tailnet"
    M_A2="  2) tailnet only      its own HTTPS name, LAN port closed  [default]"
    M_A3="  3) both              on the tailnet and on the LAN"
    M_CHOICE="1, 2 or 3 (Enter for the default):"
    M_SAVED="rule saved:"
    ;;
esac

[ "$(id -u)" -ne 0 ] || fail "$M_ROOT"

printf '\nquadlet-homelab\n\n'

# 1. What has to be there already. Nothing here is installed for you: on an
#    immutable host that is a reboot, and it is your call to make.
missing=()
for c in git python3 podman; do command -v "$c" >/dev/null || missing+=("$c"); done
if [ ${#missing[@]} -gt 0 ]; then
    say "$M_MISSING ${missing[*]}"
    say ""
    say "$M_INSTALL1"
    say "$M_INSTALL2"
    exit 1
fi
say "$M_DEPSOK"

# 1b. Podman 5.0 is the real floor: `Notify=healthy` arrived there, and 80 of
#     the 88 units use it. On 4.x the start returns before the app is ready and
#     the install reports success it cannot know about.
pv=$(podman --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
if [ -n "$pv" ] && [ "${pv%%.*}" -lt 5 ]; then
    say "podman $pv $M_OLD1"
    fail "$M_OLD2"
fi
say "podman ${pv:-?}: ok"

# 2. `systemd --user` has to be live, or every `systemctl --user` below is a
#    confusing failure later instead of a clear one now.
systemctl --user show-environment >/dev/null 2>&1 \
    || fail "$M_NOSD"
say "$M_SDOK"

# 3. The four directories. This is the whole of "step zero" in the README.
mkdir -p "$HOME"/.config/containers/{systemd,secrets,env,volumes}
say "$M_DIRS"

# 4. The repository. Updating an existing clone is --ff-only so local edits are
#    never silently thrown away; a diverged clone is yours to sort out.
if [ -d "$DEST/.git" ]; then
    git -C "$DEST" pull --ff-only --quiet || say "$M_NOFF $DEST $M_NOFF2"
    say "$M_UPD $DEST"
else
    [ -e "$DEST" ] && fail "$DEST $M_NOTGIT."
    git clone --quiet "$REPO" "$DEST"
    say "$M_CLONED $DEST"
fi

cd "$DEST"

# 5. The three tools on PATH, so the repository's location stops mattering.
#    Only ever into ~/.local/bin: no sudo, nothing outside your home, and
#    nothing written to your shell's rc file — a bootstrap that edits how every
#    future shell starts is doing more than it was asked to. If PATH needs the
#    line, you get told, and you add it. Set NO_LINKS=1 to skip this entirely.
link() {
    local target="$DEST/$1" name=$2 dest="$HOME/.local/bin/$2" atual
    if [ -e "$dest" ]; then
        atual=$(readlink -f "$dest" 2>/dev/null)
        [ "$atual" = "$(readlink -f "$target")" ] && return   # já é este, nada a dizer
        # Another checkout of the same repository is not a conflict: the command
        # works, it just runs a different copy. Saying so on every run trains
        # people to skim past the line that does matter.
        [ "$(basename "$atual")" = "$1" ] && return
        say "$name$M_TAKEN"
        return
    fi
    ln -sfn "$target" "$dest"
    say "$name -> ${target/#$HOME/\~}"
}

if [ "${NO_LINKS:-}" != 1 ]; then
    mkdir -p "$HOME/.local/bin"
    printf '\n'
    link install.py qh
    link check.py   qh-check
    link updates.py qh-updates
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) say ""
           say "$M_NOPATH"
           say '  export PATH="$HOME/.local/bin:$PATH"' ;;
    esac
fi

# 5b. The rule every install and update follows. Asked once, changed whenever
#     with `qh --set-access`. Read from /dev/tty because under `curl | bash`
#     stdin is the script itself; with no terminal the default stands.
ACCESS_FILE="$HOME/.config/quadlet-homelab/access"
if [ ! -f "$ACCESS_FILE" ] && [ -r /dev/tty ]; then
    printf '\n'
    say "$M_ASK"
    say "$M_A1"
    say "$M_A2"
    say "$M_A3"
    printf '  %s ' "$M_CHOICE"
    read -r escolha < /dev/tty || escolha=""
    case "$escolha" in
        1) modo=local ;;
        3) modo=both ;;
        *) modo=tailnet ;;
    esac
    mkdir -p "$(dirname "$ACCESS_FILE")"
    printf '%s\n' "$modo" > "$ACCESS_FILE"
    say "$M_SAVED $modo"
fi

# 6. Hand over. With an argument, show that service's plan — still a dry-run.
printf '\n'
if [ $# -gt 0 ]; then
    say "$M_PLAN $1 $M_PLAN2"
    printf '\n'
    python3 install.py "$@"
    printf '\n'
    say "$M_TORUN  qh $* --apply"
else
    say "$M_NEXT"
    say "$M_C1"
    say "$M_C2"
    say "$M_C3"
fi
printf '\n'

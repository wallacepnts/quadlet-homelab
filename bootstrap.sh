#!/usr/bin/env bash
# Gets this repository onto a fresh host and starts its web panel, which is how you use it:
# install, update, back up, customize and remove services from a browser.
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
#   - install a service. The panel (or `qh`, which is its engine, dry-run by default)
#     shows what an install would do before it does it; nothing is installed from here.
#
# What it does start: the panel, as a `systemd --user` service of yours (NO_PANEL=1 skips it).
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
    M_OTHER="roda outra cópia — apague o link e rode de novo:"
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
    M_PASK="De onde você vai abrir o painel?"
    M_P1="  1) só desta máquina     (127.0.0.1; de outro computador, por ssh -L)  [padrão]"
    M_P2="  2) da rede local        (qualquer aparelho da LAN, com o token)"
    M_P3="  3) da tailnet           (precisa do Tailscale neste host)"
    M_PNOTS="o Tailscale não respondeu: o painel fica só nesta máquina."
    M_PUP="painel no ar:"
    M_PDOWN="o painel não subiu em 15 s — veja: journalctl --user -u qh-store -n 30"
    M_PTOKEN="login (o token):"
    M_PFW="se o firewall estiver ativo, libere a porta 8484 (ex.: sudo firewall-cmd --add-port=8484/tcp --permanent)"
    M_PLINGER="para o painel subir sozinho no boot: loginctl enable-linger $USER"
    M_POPEN="abra o painel no navegador e instale os apps por ele."
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
    M_OTHER="runs another copy — delete the link and run again:"
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
    M_PASK="Where will you open the panel from?"
    M_P1="  1) this machine only    (127.0.0.1; from another computer, over ssh -L)  [default]"
    M_P2="  2) the local network    (any device on the LAN, with the token)"
    M_P3="  3) the tailnet          (needs Tailscale on this host)"
    M_PNOTS="Tailscale did not answer: the panel stays on this machine only."
    M_PUP="panel is up:"
    M_PDOWN="the panel did not come up in 15 s — see: journalctl --user -u qh-store -n 30"
    M_PTOKEN="login (the token):"
    M_PFW="if a firewall is active, open port 8484 (e.g. sudo firewall-cmd --add-port=8484/tcp --permanent)"
    M_PLINGER="so the panel starts at boot on its own: loginctl enable-linger $USER"
    M_POPEN="open the panel in a browser and install apps from there."
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

# 1b. Podman 5.0 is the real floor: `Notify=healthy` arrived there, and
#     117 of the 125 units use it. On 4.x the start returns before the app is
#     ready and the install reports success it cannot know about.
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

# 5. The four tools on PATH, so the repository's location stops mattering.
#    Only ever into ~/.local/bin: no sudo, nothing outside your home, and
#    nothing written to your shell's rc file — a bootstrap that edits how every
#    future shell starts is doing more than it was asked to. If PATH needs the
#    line, you get told, and you add it. Set NO_LINKS=1 to skip this entirely.
link() {
    local target="$DEST/$1" name=$2 dest="$HOME/.local/bin/$2" atual
    if [ -e "$dest" ]; then
        atual=$(readlink -f "$dest" 2>/dev/null)
        [ "$atual" = "$(readlink -f "$target")" ] && return   # já é este, nada a dizer
        # Another checkout of the same repository is the quiet failure, not the
        # harmless case this once assumed: the command answers, out of a copy
        # this script never updates. One left 41 commits behind reported 44
        # services as outdated that were not. Name the copy that answers; the
        # link is still the user's to move.
        [ "$(basename "$atual")" = "$1" ] \
            && { say "$name $M_OTHER ${atual/#$HOME/\~}"; return; }
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
    link store.py   qh-store
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

# 6. The panel: a `systemd --user` service (not a Quadlet: it drives systemd and podman as you), started
#    now. Where it listens is asked once, when its unit does not exist yet; a re-run keeps the answer.
#    PANEL_DRY=1 only says what it would do (the tests use it).
PANEL_URL=""
setup_panel() {
    [ "${NO_PANEL:-}" = 1 ] || [ "${NO_LINKS:-}" = 1 ] && return 0
    local unit_dir="$HOME/.config/systemd/user" listen="" escolha="" ip=""
    if [ ! -f "$unit_dir/qh-store.service" ] && [ -r /dev/tty ]; then
        printf '\n'
        say "$M_PASK"; say "$M_P1"; say "$M_P2"; say "$M_P3"
        printf '  %s ' "$M_CHOICE"
        { read -r escolha < /dev/tty; } 2>/dev/null || escolha=""
    fi
    case "$escolha" in
        2) listen="0.0.0.0:8484" ;;
        3) ip=$(tailscale ip -4 2>/dev/null | head -1 || true)
           if [ -n "$ip" ]; then listen="127.0.0.1:8484,$ip:8484"; else say "$M_PNOTS"; fi ;;
    esac
    if [ "${PANEL_DRY:-}" = 1 ]; then
        say "panel: unit -> $unit_dir/qh-store.service  listen=${listen:-default}"
        return 0
    fi
    mkdir -p "$unit_dir"
    install -m 644 "$DEST/store/qh-store.service" "$unit_dir/qh-store.service"
    if [ -n "$listen" ]; then
        mkdir -p "$unit_dir/qh-store.service.d"
        printf '[Service]\nEnvironment=QH_STORE_LISTEN=%s\n' "$listen" > "$unit_dir/qh-store.service.d/listen.conf"
    fi
    systemctl --user daemon-reload
    systemctl --user enable qh-store.service >/dev/null 2>&1 || true
    systemctl --user restart qh-store.service
    local token="$HOME/.config/quadlet-homelab/store-token" i
    for i in $(seq 1 30); do
        [ -s "$token" ] && systemctl --user is-active --quiet qh-store.service && break
        sleep 0.5
    done
    if [ ! -s "$token" ] || ! systemctl --user is-active --quiet qh-store.service; then
        say "$M_PDOWN"; return 0
    fi
    # Where it answers, from what it was given (a re-run reads the drop-in back).
    [ -z "$listen" ] && listen=$(sed -n 's/^Environment=QH_STORE_LISTEN=//p' "$unit_dir/qh-store.service.d/listen.conf" 2>/dev/null | head -1)
    case "${listen:-127.0.0.1:8484}" in
        0.0.0.0:*) PANEL_URL="http://$(hostname -I 2>/dev/null | awk '{print $1}'):8484"; say "$M_PFW" ;;
        *,*) PANEL_URL="http://${listen##*,}" ;;
        *) PANEL_URL="http://${listen:-127.0.0.1:8484}" ;;
    esac
    printf '\n'
    say "$M_PUP $PANEL_URL"
    say "$M_PTOKEN $(cat "$token")"
    loginctl enable-linger "$USER" >/dev/null 2>&1 || say "$M_PLINGER"
}
setup_panel

# 7. Hand over. With the panel up, that is where to go; with an argument, a service's plan (a dry-run).
printf '\n'
if [ -n "$PANEL_URL" ] && [ $# -eq 0 ]; then
    say "$M_POPEN"
elif [ $# -gt 0 ]; then
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

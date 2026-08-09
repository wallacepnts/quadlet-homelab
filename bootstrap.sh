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
#   - install packages. On openSUSE MicroOS that is `transactional-update` plus
#     a reboot (rule 21), which is not a thing to trigger from a pipe.
#   - install a service. `install.py` is dry-run by default on purpose: you read
#     the plan, then you run it with --apply. Piping to bash does not change that.
set -euo pipefail

REPO=${REPO:-https://github.com/wallacepnts/quadlet-homelab}
DEST=${DEST:-$HOME/quadlet-homelab}

say()  { printf '  %s\n' "$*"; }
fail() { printf '\n  %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || fail "do not run this as root — see the header of this script."

printf '\nquadlet-homelab\n\n'

# 1. What has to be there already. Nothing here is installed for you: on an
#    immutable host that is a reboot, and it is your call to make.
missing=()
for c in git python3 podman; do command -v "$c" >/dev/null || missing+=("$c"); done
if [ ${#missing[@]} -gt 0 ]; then
    say "missing: ${missing[*]}"
    say ""
    say "On openSUSE MicroOS (needs a reboot, rule 21):"
    say "  sudo transactional-update pkg install ${missing[*]}"
    say "  sudo systemctl reboot"
    fail "install them, then run this again."
fi
say "git, python3, podman: ok"

# 2. `systemd --user` has to be live, or every `systemctl --user` below is a
#    confusing failure later instead of a clear one now.
systemctl --user show-environment >/dev/null 2>&1 \
    || fail "systemd --user is not running for this user (try: loginctl enable-linger $USER)"
say "systemd --user: ok"

# 3. The four directories. This is the whole of "step zero" in the README.
mkdir -p "$HOME"/.config/containers/{systemd,secrets,env,volumes}
say "~/.config/containers/{systemd,secrets,env,volumes}: ready"

# 4. The repository. Updating an existing clone is --ff-only so local edits are
#    never silently thrown away; a diverged clone is yours to sort out.
if [ -d "$DEST/.git" ]; then
    git -C "$DEST" pull --ff-only --quiet || say "could not fast-forward $DEST — leaving it alone"
    say "updated $DEST"
else
    [ -e "$DEST" ] && fail "$DEST exists and is not a git clone — move it or set DEST=."
    git clone --quiet "$REPO" "$DEST"
    say "cloned into $DEST"
fi

cd "$DEST"

# 5. Hand over. With an argument, show that service's plan — still a dry-run.
printf '\n'
if [ $# -gt 0 ]; then
    say "the plan for $1 (nothing is done yet):"
    printf '\n'
    python3 install.py "$@"
    printf '\n'
    say "to run it:  cd $DEST && python3 install.py $* --apply"
else
    say "next:"
    say "  cd $DEST"
    say "  python3 install.py --list          # the services"
    say "  python3 install.py memos           # the plan for one, without doing it"
    say "  python3 install.py memos --apply   # do it"
fi
printf '\n'

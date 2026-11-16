# Instagram Monitor

<img src="https://api.iconify.design/mdi/instagram.svg?color=%23E1306C" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An OSINT suite for real-time Instagram monitoring.
[instagram_monitor](https://github.com/misiektoja/instagram_monitor) tracks
new posts, stories, follower changes, profile picture updates and bio
modifications — all without using the official API. It can monitor public
accounts anonymously, or log in with a session to access stories and reels.

The web dashboard is exposed through tsdproxy, giving you a live activity feed
and remote controls from any device on the tailnet.

## First run

After the install, run the setup wizard once to create the config and `.env`
inside the data volume:

```bash
podman run -it --rm \
  -v ~/.config/containers/volumes/instagram-monitor/data:/data:Z \
  -v ~/.config/containers/volumes/instagram-monitor/session:/home/instagram/.config/instaloader:Z \
  --user 10001:10001 \
  docker.io/misiektoja/instagram-monitor:v4.0.2 --setup
```

The wizard asks for target usernames, notification settings and optionally an
Instagram session (for stories and private-account access). Once done, restart
the service:

## Files

```
instagram-monitor.container   unit
instagram_monitor.conf        seed config (WEB_DASHBOARD_ALLOWED_HOSTS)
install.ini                   config recipe and where updates come from
```

Data in `~/.config/containers/volumes/instagram-monitor/data` (config, `.env`,
downloaded media). Instaloader session in
`~/.config/containers/volumes/instagram-monitor/session`. Port **8128** on the
LAN, web dashboard at `https://instagram-monitor.<your-tailnet>.ts.net`.

## Setup wizard

The tool manages its own config: a `.env` file for secrets (Instagram session
password, SMTP password, webhook URLs) and an `instagram_monitor.conf` for
targets and behaviour. Both live in the data volume and are created by the
`--setup` wizard. No podman secrets are used — the tool reads its own `.env`
from `/data/.env`.

To re-run the wizard (add targets, change notifications):

```bash
systemctl --user stop instagram-monitor
podman run -it --rm \
  -v ~/.config/containers/volumes/instagram-monitor/data:/data:Z \
  -v ~/.config/containers/volumes/instagram-monitor/session:/home/instagram/.config/instaloader:Z \
  --user 10001:10001 \
  docker.io/misiektoja/instagram-monitor:v4.0.2 --setup
systemctl --user start instagram-monitor
```

## Instagram session

Without a login, the tool monitors public accounts only. To access stories,
reels, and follower lists, import a browser session:

```bash
podman run -it --rm \
  -v ~/.config/containers/volumes/instagram-monitor/data:/data:Z \
  -v ~/.config/containers/volumes/instagram-monitor/session:/home/instagram/.config/instaloader:Z \
  --user 10001:10001 \
  docker.io/misiektoja/instagram-monitor:v4.0.2 \
  --import-browser-session --browser firefox
```

Firefox sessions can be imported from inside the container. Chromium-based
browsers do not work in the container — use password login instead, or export
cookies manually.

## Hardening

Everything, measured on `v4.0.2`: read-only root with `/tmp`, no capabilities,
`User=10001` (the image's built-in `instagram` user). `PodmanArgs=--init`
because the Python process spawns children (instaloader sessions) that need
proper zombie reaping — the upstream compose sets `init: true`.

## Backup

The data volume holds the config, `.env`, and downloaded media. The session
volume holds the instaloader cookie — both are needed for a full restore.

## Credits

[misiektoja/instagram_monitor](https://github.com/misiektoja/instagram_monitor) — MIT.

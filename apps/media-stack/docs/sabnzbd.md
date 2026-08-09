# SABnzbd

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sabnzbd.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/sabnzbd.md)**

[< Media Stack](../README.md)

Downloads from Usenet. Needs a paid provider — Usenet is not free.

Port **8081**, unit `media-stack-sabnzbd`.

The wizard asks for the provider's server, user and password. Then set the folders to `/data/downloads`, so the *arr apps file the result with a rename instead of a copy.

The interface is on 8081 on the host and on 8080 inside the container — that is the address the *arr apps want.

## Commands

```bash
systemctl --user status media-stack-sabnzbd
podman logs -f sabnzbd
qh media-stack-sabnzbd --update --apply
```

## Credits

[SABnzbd](https://github.com/sabnzbd/sabnzbd) — GPL-2.0

[Official documentation](https://sabnzbd.org/wiki/)

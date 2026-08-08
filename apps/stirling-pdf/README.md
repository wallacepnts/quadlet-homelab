# Stirling-PDF — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF)
(juntar, dividir, converter, OCR, assinar e comprimir PDF, tudo local)
via Podman Quadlet, usando a imagem oficial
`docker.io/stirlingtools/stirling-pdf`.

## Architecture

A single container (Spring Boot + LibreOffice + Tesseract embedded). Three
volumes:

| Volume | What for |
| --- | --- |
| `/configs` | settings.yml, the user database, session keys |
| `/usr/share/tessdata` | extra OCR languages (downloaded by you) |
| `/logs` | the application's log |

Nothing leaves the machine — that is the project's point: it replaces the
"online PDF" sites where you upload your document to a third party.

### Sobre a variante da imagem

Upstream publishes three: the default, `-fat` (everything preinstalled,
~4 GB) and `-ultra-lite` (basic operations only, with no OCR or Office
conversion). This repository uses **the default one**, and the
`wud.tag.include` in the unit exists
justamente pra impedir que o [wud](../wud/) sinalize uma tag `-fat` como
an "update" to the one we use.

### Sobre as capabilities

This is the service that needed the most capabilities in the repository:
five. The entrypoint runs `setpriv` to switch user and does a `chown` on
`/pipeline` e `/configs` no start, e o kit usual do repo
(`CHOWN,SETUID,SETGID`) is not enough — without `DAC_OVERRIDE` and `FOWNER`
the
imagem morre com `setpriv: setresuid failed: Operation not permitted`.
`ReadOnly=true` was refused for the same reason. This is measured, not
copied (see CLAUDE.md, "Hardening a new service").

## Files

```
stirling-pdf.container   # main unit
.env.example             # configuration variables
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py stirling-pdf            # dry-run: shows what it will do
python3 install.py stirling-pdf --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8095` (ou via [tsdproxy](../tsdproxy/) em
`https://stirling-pdf.<your-tailnet>.ts.net`).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/stirling-pdf/stirling-pdf.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/stirling-pdf/{config,tessdata,logs}

# 3. Environment variables
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/stirling-pdf.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/stirling-pdf/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start stirling-pdf
```

Open `http://<host-ip>:8095` (or through [tsdproxy](../tsdproxy/) at
`https://stirling-pdf.<your-tailnet>.ts.net`).

**First login:** `admin` / `stirling`. The `.env.example` already ships
`SECURITY_ENABLE_LOGIN=true`, so the UI is not left open — **change the
password on first access** (Settings → Account).

</details>

## OCR in another language

The default image ships English. For OCR in Portuguese (or any other
language), download Tesseract's training data into the `tessdata` volume:

```bash
wget -P ~/.config/containers/volumes/stirling-pdf/tessdata/ \
  https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata
systemctl --user restart stirling-pdf
```

O idioma aparece na lista da ferramenta de OCR depois do restart.

## Auto-update

No `AutoUpdate=` — an explicit tag (`2.14.3`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). O `wud.tag.include` restringe o aviso do [wud](../wud/) a
`X.Y.Z` puro, filtrando as variantes `-fat`/`-ultra-lite`.

## Backup & recovery

```bash
systemctl --user stop stirling-pdf
tar -czf stirling-pdf-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes stirling-pdf
systemctl --user start stirling-pdf
```

A deliberately small backup: the processed PDFs are not kept on the server,
the result goes straight to the browser's download.

## Useful commands

```bash
systemctl --user status stirling-pdf
podman logs -f stirling-pdf
curl -s http://127.0.0.1:8095/api/v1/info/status   # {"version":"...","status":"UP"}
```

## Credits

Quadlet deploy based on
[Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF) da
[Stirling-Tools](https://github.com/Stirling-Tools) (MIT).

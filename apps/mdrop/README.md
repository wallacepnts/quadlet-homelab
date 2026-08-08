# mdrop — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [mdrop](https://github.com/samapriya/mdrop) (interface web para
o [MarkItDown](https://github.com/microsoft/markitdown) da Microsoft) via
Podman Quadlet, usando a imagem oficial `docker.io/samapriya/mdrop`.

Arrasta o arquivo, recebe Markdown. Converte PDF, Word, Excel,
PowerPoint, images (with OCR) and audio (with transcription).

## Why this and not markitdown directly

[markitdown](https://github.com/microsoft/markitdown) cannot be deployed as a
service in this repository, for three reasons:

- Microsoft **publishes no image** — upstream tells you to build
  localmente, o que quebra o modelo daqui (unit baixada por `wget`
  referenciando imagem publicada e pinada);
- the `ENTRYPOINT` is `markitdown`: it is a **CLI**, not a server;
- the server variant (`markitdown-mcp`) is documented by the
  upstream como local-use-only, com *"DO NOT bind the server to other
  interfaces"* — because `convert_to_markdown(uri)` accepts `file:` (reading
  an arbitrary file from inside the container) and `http:` (SSRF from the
  sua rede).

mdrop solves all three: it publishes an image, it is a genuine HTTP server,
and the interface only accepts an **upload**, not an arbitrary URI.

## Architecture

A single container (FastAPI/uvicorn). **No volume, no database, no
session.** The conversion workspace is a `Tmpfs` — the file you send stays in
RAM and
nunca toca o disco do host. Confirmado com `podman inspect`: o container
it has no mount at all.

The practical consequence: **there is no backup to take**, and reinstalling
is the
"restore".

### Pinado por digest

Upstream publishes only `latest` and `main`, with no versioned tag and no
GitHub release. Since rule 9 asks for a fixed version, the unit pins by
**digest** —
mesmo tratamento que o Postgres e o valkey do [immich](../immich/)
get. That is also why there is no `wud.watch`: there is no tag to compare.

Pra atualizar, conferir o projeto e trocar o digest:

```bash
podman pull docker.io/samapriya/mdrop:latest
podman image inspect docker.io/samapriya/mdrop:latest --format '{{index .RepoDigests 0}}'
```

## Files

```
mdrop.container   # main unit
```

## Installation

```bash
python3 install.py mdrop            # dry-run: shows what it will do
python3 install.py mdrop --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8292` (ou via [tsdproxy](../tsdproxy/) em
`https://mdrop.<your-tailnet>.ts.net`).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/mdrop/mdrop.container

# 2. Start it — sem mkdir, sem secret, sem env
systemctl --user daemon-reload
systemctl --user start mdrop
```

Open `http://<host-ip>:8292` (ou via [tsdproxy](../tsdproxy/) em
`https://mdrop.<your-tailnet>.ts.net`).

</details>

## Security

**There is no authentication** — the project's own README says so and
recommends a VPN or an authenticating proxy in front. Here the tailnet plays
the VPN's part; to require a login, the route is
[Authentik](../authentik/).

The design helps: nothing is written, nothing is logged beyond the file's
name and size, and there is no arbitrary URI — upload only. Even so, what you
convert passes through the process, so the same care as
[stirling-pdf](../stirling-pdf/) applies: the whole point is not sending a
document
pra site de terceiro que ele existe.

### O tamanho do `/tmp/mdrop`

`1G` in RAM, like the official compose. It is a ceiling, not a reservation —
it only occupies what the file being converted uses. Lower it if you only
convert small documents, or if the machine is tight on memory;
[rule 20](../../docs/conventions.md) explains why a `Tmpfs` without `size=` is
dangerous.

## Auto-update

Sem `AutoUpdate=` e sem `wud.watch` — ver "Pinado por digest" acima.

## Backup & recovery

None. There is no state.

## Useful commands

```bash
systemctl --user status mdrop
podman logs -f mdrop
# converter pela linha de comando
curl -F "file=@documento.pdf" http://127.0.0.1:8292/convert
```

## Credits

Quadlet deploy based on [mdrop](https://github.com/samapriya/mdrop) de
[samapriya](https://github.com/samapriya) (MIT), que embrulha o
[MarkItDown](https://github.com/microsoft/markitdown) da Microsoft.

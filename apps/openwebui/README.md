# Open WebUI + Ollama — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An [Open WebUI](https://github.com/open-webui/open-webui) (a web chat
interface for LLMs) deploy alongside [Ollama](https://ollama.com) (the local
LLM server it uses as a backend), via Podman Quadlet — migrated from the
project's official
[`docker-compose.yaml`](https://github.com/open-webui/open-webui/blob/main/docker-compose.yaml)
(the variant with the two services separate, not the `:ollama` image that
embeds both in a single container — see the comparison below).

## Comparing the Open WebUI image variants

| Tag | What it is | Why (not) use it here |
| --- | --- | --- |
| **`:main`** (used here) | Open WebUI only, talking to an external Ollama through `OLLAMA_BASE_URL` | It pairs with this directory's `openwebui-ollama.container` — two containers, each with its own lifecycle, updates and logs |
| `:ollama` | Open WebUI **plus Ollama embedded in the same container** | The project's official compose (linked above) no longer uses that variant — it prefers two separate services, the same choice made here. A single container makes it harder to update or restart one without the other, and mixes both sets of logs |
| `:cuda` | The same base as `:main`, with the CUDA Toolkit embedded to GPU-accelerate Open WebUI's *own internal* tasks (local embedding, Whisper speech-to-text, reranking) — **it has nothing to do with Ollama's GPU** | This host is CPU-only by decision (no `nvidia-container-toolkit`/CDI configured — see "Enabling an NVIDIA GPU" below). If the GPU is enabled, that tag becomes worthwhile for the embedding and speech tasks — change `Image=` in `openwebui.container` to `ghcr.io/open-webui/open-webui:v0.11.0-cuda` and add `PodmanArgs=--gpus=all` |
| `:dev` | A build of the main branch, with no release tag | Out of the question for stable home use ([rule 9](../../docs/conventions.md)) |

## Architecture

Two containers on the same network (`openwebui-net.network`):

- `ollama` — the LLM server itself, with an HTTP API on port `11434` (also
  published on the host, for direct use via `podman exec ollama ollama run
  <model>` or the API without going through Open WebUI).
- `openwebui` — the web interface; `Requires=`/`After=openwebui-ollama.service`
  in `[Unit]` guarantees Ollama is already up before it tries to talk to
  `http://ollama:11434` (the container's name, resolved through Podman's
  internal DNS — it does not change with the file or unit name).

**CPU-only by default** — with no GPU it runs on any host, more slowly for
large models. See "Enabling an NVIDIA GPU"/"Enabling an AMD GPU (ROCm)" below.

Open WebUI's first start downloads a default embedding model
(`sentence-transformers/all-MiniLM-L6-v2`, used for RAG and semantic search)
straight from Hugging Face — tested in practice, that alone takes more than
60s; hence the generous `HealthStartPeriod`/`TimeoutStartSec` in that
`.container`.

`WEBUI_SECRET_KEY` as a secret (rules 2 and 15 of the conventions) — without
it being fixed, Open WebUI generates a new key on every container restart and
invalidates everyone's logged-in session (unlike the official compose, which
leaves it blank).

## Files

```
openwebui-net.network     # the bridge network shared by both
openwebui-ollama.container # the backend — the LLM server
openwebui.container       # the web interface
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py openwebui            # dry-run: shows what it will do
python3 install.py openwebui --apply
```

It brings the whole stack up (Open WebUI + Ollama) — `Requires=` pulls the
chain. For the local network only, `--access local`; on the tailnet and the
LAN, `--access both`. Adding `--href-local` points the dashboard link at the
LAN. See [Installing and operating](../../docs/installing.md).

Open the Open WebUI at `http://<host-ip>:3003` (or through
[tsdproxy](../tsdproxy/) at `https://openwebui.<your-tailnet>.ts.net`) and
create the account on first access — **the first user to sign up automatically
becomes admin**. Once that account exists, turn open signup off in Admin Panel
→ Settings → General → "Enable New Sign Ups", otherwise anyone who reaches the
URL can create an account of their own.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd/openwebui
wget -P ~/.config/containers/systemd/openwebui/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/openwebui-net.network \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/openwebui-ollama.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/openwebui.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/openwebui/{ollama,webui}

# 3. Non-secret env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/openwebui.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/.env.example

# 4. Secret — the key used to sign Open WebUI's login sessions
mkdir -p ~/.config/containers/secrets/openwebui
python3 -c "import secrets; print(secrets.token_hex(32))" \
  > ~/.config/containers/secrets/openwebui/secret-key.txt
chmod 600 ~/.config/containers/secrets/openwebui/secret-key.txt
podman secret create openwebui-secret-key \
  ~/.config/containers/secrets/openwebui/secret-key.txt

# 5. Start it (Ollama first — Open WebUI brings it up by itself via
#    Requires=, but both can be started at once through the main unit)
systemctl --user daemon-reload
systemctl --user start openwebui
```

Pull a model and test it straight through Ollama (optional; Open WebUI can
also pull models through its own UI):

```bash
podman exec -it ollama ollama pull llama3.2
```

Open the Open WebUI at `http://<host-ip>:3003` (or through
[tsdproxy](../tsdproxy/) at `https://openwebui.<your-tailnet>.ts.net`) and
create the account on first access — **the first user to sign up automatically
becomes admin**. Once that account exists, turn open signup off in Admin Panel
→ Settings → General → "Enable New Sign Ups", otherwise anyone who reaches the
URL can create an account of their own.

Ollama's API on its own (without going through Open WebUI) at
`http://<host-ip>:11434`.

</details>

## Enabling an NVIDIA GPU

This requires the **NVIDIA Container Toolkit** configured for Podman (it
generates a CDI — Container Device Interface — spec that rootless Podman uses
to expose the GPU without running as root). It is not set up by default here
because it is a change to the host's packages, outside the scope of a
`.container` on its own.

```bash
# 1. Install the toolkit (openSUSE — add NVIDIA's official repo first if you
#    do not have it; the names vary by distro, see
#    https://github.com/NVIDIA/nvidia-container-toolkit)
sudo zypper install nvidia-container-toolkit

# 2. Generate the CDI spec (it lets rootless Podman see the GPU without root)
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml

# 3. Check the device shows up
nvidia-ctk cdi list
```

Then add this to **`openwebui-ollama.container`** (the `[Container]`
section) — it accelerates Ollama itself, the pair's main GPU consumer:

```ini
PodmanArgs=--gpus=all
```

Optionally, **`openwebui.container`** can use the GPU for its own internal
tasks too (local embedding, Whisper) — in that case change `Image=` to
`ghcr.io/open-webui/open-webui:v0.11.0-cuda` and add the same
`PodmanArgs=--gpus=all`.

```bash
systemctl --user daemon-reload
systemctl --user restart openwebui-ollama openwebui
podman exec ollama ollama run llama3.2 --verbose   # check for a much higher "eval rate"
```

It keeps using the same base Ollama image (`ollama/ollama`, no suffix) — it
detects and uses the GPU by itself once Podman can expose the device.

## Enabling an AMD GPU (ROCm)

Swap the image in **`openwebui-ollama.container`** for
`docker.io/ollama/ollama:0.32.6-rocm` (the same base version, the ROCm
variant) and expose the kernel's devices directly (no CDI, simpler than the
NVIDIA route):

```ini
Image=docker.io/ollama/ollama:0.32.6-rocm
AddDevice=/dev/kfd
AddDevice=/dev/dri
```

```bash
systemctl --user daemon-reload
systemctl --user restart openwebui-ollama
```

It requires the ROCm driver installed on the host (the `amdgpu` kernel
module plus a working `rocm-smi`) — outside this `.container`'s scope, see
[AMD's official documentation](https://rocm.docs.amd.com).

## Auto-update

No `AutoUpdate=` on either — explicit tags (`0.32.6`/`v0.11.0`), bumped by
hand ([rule 9](../../docs/conventions.md)). Both images have a real healthcheck
(`ollama list` and the `/health` endpoint, tested in practice) —
`AutoUpdate=registry` could be enabled with working rollback on either, but it
is kept manual as this repository's default.

## Backup & recovery

```bash
systemctl --user stop openwebui openwebui-ollama
tar -czf openwebui-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes openwebui
systemctl --user start openwebui-ollama openwebui
```

Downloaded models (`openwebui/ollama/`) tend to be large (several GB each) —
consider excluding them from the routine backup tarball and simply pulling
them again (`ollama pull`) if you need to restore, rather than keeping a copy.

## Useful commands

```bash
systemctl --user status openwebui-ollama openwebui
podman logs -f ollama
podman logs -f openwebui
podman exec ollama ollama list
podman exec -it ollama ollama run <model>
podman exec openwebui curl -fsS http://127.0.0.1:8080/health
```

## Credits

Quadlet deploy based on [Ollama](https://github.com/ollama/ollama)
(MIT) and [Open WebUI](https://github.com/open-webui/open-webui)
(BSD-3-Clause).

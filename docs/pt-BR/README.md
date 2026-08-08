# quadlet-homelab

**[🇬🇧 Read in English](../../README.md)**

Coleção pessoal de deploys via [Podman Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
(rootless), um serviço por pasta. Este README é o padrão de referência —
regras e exemplos verificados na prática, pra seguir em qualquer serviço
novo adicionado aqui.

## Serviços neste repositório

| Logo | Aplicativo | Versão | Descrição |
| --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/actual-budget.svg" width="48" height="48" alt=""> | [Actual Budget](../../apps/actual-budget/README.pt-BR.md) | `latest` (auto-update) | Rápido e focado em privacidade pra gerenciar finanças pessoais, usando a metodologia de Orçamento de Envelope |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/adguard-home.svg" width="48" height="48" alt=""> | [AdGuard Home](../../apps/adguardhome/README.pt-BR.md) | `v0.107.78` | Servidor DNS recursivo com bloqueio de anúncios e rastreadores pra toda a rede |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/anytype.svg" width="48" height="48" alt=""> | [any-sync-bundle](../../apps/any-sync-bundle/README.pt-BR.md) | `1.5.0-2026-07-17` | Backend do protocolo Any-Sync, que sincroniza os dados do Anytype entre dispositivos sem depender da nuvem da empresa |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/audiobookshelf.svg" width="48" height="48" alt=""> | [Audiobookshelf](../../apps/audiobookshelf/README.pt-BR.md) | `2.36.0` | Servidor de audiolivros e podcasts, com progresso sincronizado entre dispositivos |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/authentik.svg" width="48" height="48" alt=""> | [Authentik](../../apps/authentik/README.pt-BR.md) | `2026.5.6` | Servidor de identidade (SSO, MFA, OIDC/SAML) — só o core implantado, sem forward-auth via tsdproxy ainda (ver README) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/beszel.svg" width="48" height="48" alt=""> | [Beszel](../../apps/beszel/README.pt-BR.md) | `0.18.7` | Dashboard leve de monitoramento de recursos (CPU/RAM/disco/rede/containers) deste host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/calibre-web.svg" width="48" height="48" alt=""> | [Calibre-Web-Automated](../../apps/calibre-web-automated/README.pt-BR.md) | `v4.0.6` | Biblioteca de ebooks com conversão, metadados e capas automáticas via Calibre, com leitura direto no navegador |
| <img src="https://cdn.simpleicons.org/gnubash" width="48" height="48" alt=""> | [CookCLI](../../apps/cookcli/README.pt-BR.md) | `0.32.1` | Receitas em texto puro no formato CookLang — versionáveis em git, sem banco e sem formulário |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/copyparty.svg" width="48" height="48" alt=""> | [Copyparty](../../apps/copyparty/README.pt-BR.md) | `1.20.20` | Servidor de arquivos com upload pelo navegador ou celular, retomada de transferência e WebDAV |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/donetick.svg" width="48" height="48" alt=""> | [Donetick](../../apps/donetick/README.pt-BR.md) | `v0.1.76` | Tarefas domésticas recorrentes — quem faz, com que frequência e quando vence |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/freshrss.svg" width="48" height="48" alt=""> | [FreshRSS](../../apps/freshrss/README.pt-BR.md) | `1.29.1-alpine` | Agregador de feeds RSS/Atom self-hosted, com API compatível pra apps móveis |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/frigate.svg" width="48" height="48" alt=""> | [Frigate](../../apps/frigate/README.pt-BR.md) | `0.17.2` | NVR com detecção de objetos por IA — CPU-only por padrão, sem câmera configurada ainda (ver README) |
| <img src="https://cdn.simpleicons.org/ghost" width="48" height="48" alt=""> | [Ghost](../../apps/ghost/README.pt-BR.md) | `6.56.0-alpine` | Blog/newsletter self-hosted (SQLite, modo development — ver README) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gitea.svg" width="48" height="48" alt=""> | [Gitea](../../apps/gitea/README.pt-BR.md) | `1.27.1` | Servidor Git leve e completo — repositórios, issues, pull requests e CI numa interface só |
| <img src="https://cdn.jsdelivr.net/gh/NousResearch/hermes-agent@main/website/static/img/logo.png" width="48" height="48" alt=""> | [Hermes Agent](../../apps/hermes-agent/README.pt-BR.md) | `v2026.8.3` | Agente de IA pessoal com habilidades e memória, expondo uma API compatível com a da OpenAI pros outros serviços chamarem |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/homebox.svg" width="48" height="48" alt=""> | [HomeBox](../../apps/homebox/README.pt-BR.md) | `0.26.2` | Inventário doméstico — o que você tem, onde está, nota fiscal, manual e garantia, com busca e etiquetas |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/home-assistant.svg" width="48" height="48" alt=""> | [Home Assistant](../../apps/home-assistant/README.pt-BR.md) | `2026.8.1` | Hub central de automação residencial, integra dispositivos de qualquer fabricante num painel só |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/homepage.png" width="48" height="48" alt=""> | [homepage](../../apps/homepage/README.pt-BR.md) | `latest` (auto-update) | Dashboard que descobre e organiza os outros containers sozinho via labels, sem editar config a cada serviço novo |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/immich.svg" width="48" height="48" alt=""> | [Immich](../../apps/immich/README.pt-BR.md) | `v3.1.0` | Backup e organização de fotos/vídeos, com reconhecimento facial e busca smart |
| <img src="https://cdn.simpleicons.org/invoiceninja" width="48" height="48" alt=""> | [Invio](../../apps/invio/README.pt-BR.md) | `v2.1.1` | Emissão e controle de faturas self-hosted, com SQLite e sem depender de serviço externo |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/karakeep.svg" width="48" height="48" alt=""> | [Karakeep](../../apps/karakeep/README.pt-BR.md) | `0.33.1` | Gerenciador de bookmarks com busca full-text e arquivamento automático do conteúdo de cada página salva |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/lubelogger.png" width="48" height="48" alt=""> | [LubeLogger](../../apps/lubelogger/README.pt-BR.md) | `v1.7.0` | Registro de manutenção veicular — trocas de óleo, revisões, gastos e lembretes, por veículo |
| <img src="https://cdn.simpleicons.org/markdown" width="48" height="48" alt=""> | [mdrop](../../apps/mdrop/README.pt-BR.md) | `latest` (pinado por digest) | Converte PDF, Office, imagem e áudio para Markdown pela web, sem estado e sem sair da máquina |
|  | [Media Stack](../../apps/media-stack/README.pt-BR.md) | — | Jellyfin, Dispatcharr, Downtify, Prowlarr, Sonarr, Radarr, Lidarr, Bazarr, Seerr, Gluetun, Deluge, SABnzbd — servidor de mídia + automação, raiz de dados compartilhada, cada app com sua própria versão |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/memos.svg" width="48" height="48" alt=""> | [Memos](../../apps/memos/README.pt-BR.md) | `0.30.0` | Notas rápidas, self-hosted e markdown-nativo |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/metube.svg" width="48" height="48" alt=""> | [MeTube](../../apps/metube/README.pt-BR.md) | `2026.08.04` | Interface web do yt-dlp — cola a URL e o vídeo cai no disco |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/monica.svg" width="48" height="48" alt=""> | [Monica](../../apps/monica/README.pt-BR.md) | `main` (sem tag fixa, ver README) | CRM pessoal — histórico de relacionamentos, contatos, lembretes |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/n8n.svg" width="48" height="48" alt=""> | [n8n](../../apps/n8n/README.pt-BR.md) | `2.33.7` | Automação de workflows via editor visual de nós |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/netbootxyz.svg" width="48" height="48" alt=""> | [netboot.xyz](../../apps/netbootxyz/README.pt-BR.md) | `0.7.6-nbxyz23` | Menu de boot pela rede (PXE) pra instalar ou testar distros e ferramentas sem gravar pendrive |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/nginx.svg" width="48" height="48" alt=""> | [nginx](../../apps/nginx/README.pt-BR.md) | `1.30.4-alpine` | Servidor de arquivos estáticos |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/node-red.svg" width="48" height="48" alt=""> | [Node-RED](../../apps/node-red/README.pt-BR.md) | `5.0.4-minimal` | Automação de fluxos via editor visual de nós |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/ntfy.svg" width="48" height="48" alt=""> | [ntfy](../../apps/ntfy/README.pt-BR.md) | `v2.27.0` | Servidor de notificações push — destino dos alertas do uptime-kuma, wud e zerobyte, com app no celular |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/open-webui.svg" width="48" height="48" alt=""> | [Open WebUI](../../apps/openwebui/README.pt-BR.md) | `v0.11.0` (Open WebUI) + `0.32.6` (Ollama) | Interface de chat web + servidor de LLMs locais, CPU-only por padrão (opções de GPU NVIDIA/AMD documentadas) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/omni-tools.png" width="48" height="48" alt=""> | [Omni Tools](../../apps/omni-tools/README.pt-BR.md) | `0.6.0` | Conversores, geradores e calculadoras que rodam no navegador — nada é enviado ao servidor |
| <img src="https://cdn.jsdelivr.net/gh/rmyndharis/OpenWA@main/docs/logo/openwa.svg" width="48" height="48" alt=""> | [OpenWA](../../apps/openwa/README.pt-BR.md) | `0.14.6` | Gateway de API do WhatsApp — transforma a conta em REST + webhooks, pro n8n e o Home Assistant usarem |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owncloud.svg" width="48" height="48" alt=""> | [ownCloud](../../apps/owncloud/README.pt-BR.md) | `11.0.0-20260802` | Sincronização e compartilhamento de arquivos em nuvem própria |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owntracks.svg" width="48" height="48" alt=""> | [OwnTracks](../../apps/owntracks/README.pt-BR.md) | `1.0.1` | Rastreamento de localização pessoal via app de celular, com broker MQTT próprio e histórico de posições |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/paperless-ngx.svg" width="48" height="48" alt=""> | [Paperless-ngx](../../apps/paperless-ngx/README.pt-BR.md) | `3.0.5` | Digitaliza, faz OCR e indexa documentos automaticamente, com busca full-text pra nunca mais procurar papel |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/proxmox.svg" width="48" height="48" alt=""> | [Proxmox VE](../../apps/proxmox/README.pt-BR.md) | `9.2.9` | O hypervisor Proxmox num container, pra experimentar sem dedicar uma máquina — roda privileged |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radicale.svg" width="48" height="48" alt=""> | [Radicale](../../apps/radicale/README.pt-BR.md) | `3.7.6.0` | Servidor CalDAV/CardDAV leve e minimalista |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/stirling-pdf.svg" width="48" height="48" alt=""> | [Stirling-PDF](../../apps/stirling-pdf/README.pt-BR.md) | `2.14.3` | Manipulação de PDF local — juntar, dividir, converter, OCR e assinar, no lugar dos sites de "PDF online" |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/syncthing.svg" width="48" height="48" alt=""> | [Syncthing](../../apps/syncthing/README.pt-BR.md) | `2.1.3` | Sincronização de arquivos P2P entre dispositivos, sem servidor central |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/tailscale.svg" width="48" height="48" alt=""> | [tsdproxy](../../apps/tsdproxy/README.pt-BR.md) | `2` | Publica containers na tailnet automaticamente, só com labels — sem configurar proxy manualmente por serviço |
| <img src="https://cdn.jsdelivr.net/gh/containers/containertoolbx.org@main/apple-touch-icon.png" width="48" height="48" alt=""> | [Toolbx](../../apps/toolbx/README.pt-BR.md) | — | Shells descartáveis de Arch, Fedora, RHEL e Ubuntu, nas imagens oficiais do Toolbx — um lugar pra instalar ferramenta avulsa que não é o host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/traccar.svg" width="48" height="48" alt=""> | [Traccar](../../apps/traccar/README.pt-BR.md) | `6.14.5` | Rastreamento de GPS — mapa ao vivo, histórico, geocercas e relatórios, com app no celular |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="48" height="48" alt=""> | [VM](../../apps/vm/README.pt-BR.md) | — | Windows, macOS, ZimaOS e 23 distros Linux como VMs em containers, vistas pelo navegador — exige KVM no host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/uptime-kuma.svg" width="48" height="48" alt=""> | [Uptime Kuma](../../apps/uptime-kuma/README.pt-BR.md) | `2.5.0` | Monitor de disponibilidade dos outros serviços e da tailnet, com histórico e notificação |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/vaultwarden.svg" width="48" height="48" alt=""> | [Vaultwarden](../../apps/vaultwarden/README.pt-BR.md) | `1.37.1-alpine` | Cofre de senhas compatível com o protocolo do Bitwarden, leve o bastante pra rodar em qualquer lugar |
| <img src="https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg" width="48" height="48" alt=""> | [VaultZap](../../apps/vaultzap/README.pt-BR.md) | `latest` (auto-update) | Arquivo local e navegável de conversas exportadas do WhatsApp — busca, galeria e calendário, 100% offline |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/wger.svg" width="48" height="48" alt=""> | [wger](../../apps/wger/README.pt-BR.md) | `2.6.0` | Planejamento e acompanhamento de treinos, com banco de exercícios e medidas corporais |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zigbee2mqtt.svg" width="48" height="48" alt=""> | [Zigbee2MQTT](../../apps/zigbee2mqtt/README.pt-BR.md) | `2.13.0` | Ponte entre dispositivos Zigbee e MQTT, sem hub proprietário — sem coordenador ligado ainda (ver README) |
| <img src="https://cdn.jsdelivr.net/gh/getwud/wud@main/ui/public/img/icons/android-chrome-512x512.png" width="48" height="48" alt=""> | [WUD (What's Up Docker)](../../apps/wud/README.pt-BR.md) | `8.3.1` | Monitora as atualizações de imagem disponíveis pros containers, sem aplicar nada sozinho — só avisa |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/zerobyte.png" width="48" height="48" alt=""> | [Zerobyte](../../apps/zerobyte/README.pt-BR.md) | `v0.41.0` | Automatiza backup (via Restic) dos dados de todos os outros serviços deste repositório |

**AutoUpdate ligado**: [Actual Budget](../../apps/actual-budget/README.pt-BR.md), [homepage](../../apps/homepage/README.pt-BR.md), [VaultZap](../../apps/vaultzap/README.pt-BR.md)
— todo o resto usa tag explícita + bump manual (padrão deste repositório,
regra 9). Critério de quando ativar e por que a maioria fica desligada:
ver seção [Auto-update](./auto-update.md).

A coluna Versão espelha a tag em `Image=` do `.container` de cada
serviço — atualizar aqui junto de qualquer bump manual, não é gerado
automaticamente.

## Num servidor ARM

**79 das 81 imagens daqui publicam variante `arm64`.** Esses serviços instalam
sem alteração nenhuma — o Podman escolhe o manifesto certo sozinho, e o
`install.py <app> --apply` funciona igual ao x86.

Duas imagens são só `amd64`, e levam o serviço delas junto:

| Imagem | Serviço | Por quê |
| --- | --- | --- |
| `dockurr/macos` | `vm-macos` | sem build ARM; ela emula um Mac Intel, e macOS em ARM é outra máquina |
| `quay.io/toolbx/arch-toolbox` | `toolbx-arch` | o Arch Linux não tem porte ARM oficial |

**Ter imagem compatível não resolve tudo nos serviços de VM.** O KVM só acelera
convidado da mesma arquitetura, então quem decide é o convidado, não a imagem —
e convidado x86 num host ARM cai em emulação e fica lento a ponto de ser
inviável. Por isso o `apps/vm` traz uma unit por combinação:

| Host | Windows | Linux | macOS |
| --- | --- | --- | --- |
| x86_64 | `vm-windows` | `vm-qemu` | `vm-macos` |
| ARM64 | `vm-windows-arm` | [qemus/qemu-arm](https://github.com/qemus/qemu-arm/), não empacotado aqui | — |

O `vm-windows-arm` foi escrito a partir da documentação do upstream, não
medido: aqui não existe host ARM pra testá-lo.

Pra conferir qualquer imagem antes de escolher um host:

```bash
podman manifest inspect docker.io/library/postgres:16-alpine \
  | python3 -c "import sys,json;print(sorted({m['platform']['architecture'] for m in json.load(sys.stdin)['manifests'] if m['platform']['architecture']!='unknown'}))"
```

O Docker Hub limita consulta anônima de manifesto, então uma leva dessas começa
a falhar no meio — espaçar, ou consultar a API de registry direto.

## Documentação

| | |
| --- | --- |
| [Instalando e operando](./instalacao.md) | o `install.py`: instalar, atualizar, backup, restaurar, remover |
| [Recuperação e migração](./recuperacao.md) | a máquina morreu, ou mudar de servidor |
| [Ferramentas](./ferramentas.md) | `check.py` e `updates.py`, e o que o CI roda |
| [Convenções](./convencoes.md) | as 22 regras, cada uma com o caso real que a originou |
| [Referência](./referencia.md) | onde cada arquivo mora e um `.container` comentado |
| [Auto-update](./auto-update.md) | por que quase tudo aqui atualiza na mão |

A **instalação manual** de cada serviço está no README dele, num bloco
recolhível *"Instalação manual (avançado)"* — os mesmos passos que o
`install.py` executa, um a um.

## Início rápido

```bash
# 1. as pastas do Podman (o único passo obrigatório)
mkdir -p ~/.config/containers/{systemd,secrets,env,volumes}

# 2. instalar um serviço
python3 install.py memos --apply
```

Tailscale e tsdproxy são **opcionais** — ver
[Passo zero](#passo-zero-preparar-o-host). Sem eles, `--access local`.

## Passo zero: preparar o host

**O mínimo, e é só isto:**

```bash
mkdir -p ~/.config/containers/{systemd,secrets,env,volumes}
```

Todo serviço deste repositório publica uma porta no host. Com as pastas
criadas e o Podman rootless funcionando, dá pra instalar qualquer um e
acessar em `http://<ip-do-host>:<porta>` — nada aqui exige rede externa,
domínio ou certificado.

### Opcional: a tailnet

O [Tailscale](https://tailscale.com) e o [tsdproxy](../../apps/tsdproxy/README.pt-BR.md) são
**opcionais**. Eles resolvem duas coisas: acessar de fora de casa sem
abrir porta no roteador, e ter HTTPS de verdade por serviço (o que
importa pra app que usa WebCrypto — o [Vaultwarden](../../apps/vaultwarden/README.pt-BR.md)
só descriptografa a sessão em contexto seguro).

Quem quiser, nesta ordem:

**1. Tailscale, e não por Quadlet.** Ele precisa integrar com o
`systemd-resolved` do host pro MagicDNS funcionar, e container não
compartilha D-Bus/mount namespace com o host (regra 21). No MicroOS:

```bash
sudo transactional-update pkg install tailscale
sudo systemctl reboot            # transactional-update só aplica no próximo boot
sudo systemctl enable --now tailscaled
sudo tailscale up
```

**2. A variável `TAILNET`**, que resolve os `homepage.href` de todas as
units (regra 19):

```bash
mkdir -p ~/.config/environment.d
echo 'TAILNET=<your-tailnet>' > ~/.config/environment.d/tailnet.conf
systemctl --user daemon-reload
```

**3. O [tsdproxy](../../apps/tsdproxy/README.pt-BR.md)**, que publica todo o resto na tailnet
automaticamente por label:

```bash
python3 install.py tsdproxy --apply
```

`python3 install.py tailscale` repete essas instruções, já que o Tailscale
não tem pasta em `apps/`.

### Instalando sem tailnet

Só uma coisa quebra sem ela: o `homepage.href` das units aponta pra um
domínio `.ts.net` que não existe, e o link do dashboard morre. O
`--local` troca esse label pelo endereço da LAN na hora de copiar:

```bash
python3 install.py memos --apply --local
# Label=homepage.href=http://192.168.1.12:5230
```

Ele também **comenta** as labels de `tsdproxy.*` (comenta, não apaga), então
ligar a tailnet depois é reinstalar o serviço sem `--local`, não editar unit
na mão. Pra manter o nó do tsdproxy e só trocar o link do dashboard, use
`--href-local` sozinho. Os `.env.example` que citam `<your-tailnet>`
(vaultwarden, gitea, karakeep e outros 14) continuam pedindo revisão à
mão: são `DOMAIN`/`ALLOWED_HOSTS` que o próprio app grava no banco.

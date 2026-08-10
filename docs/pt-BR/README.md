# Quadlet Homelab

**[🇺🇸 Read in English](../../README.md)**

63 serviços self-hosted como units do [Podman Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html),
rootless, um serviço por pasta.

## Início rápido

```bash
curl -fsSL https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/bootstrap.sh | bash
```

Debian e Ubuntu não trazem `curl` nem `wget` numa instalação crua — medido nas
imagens base dos dois. Ali você vai instalar pacote de qualquer forma, então
instale o `git`, que o bootstrap exige de toda maneira:

```bash
git clone https://github.com/wallacepnts/quadlet-homelab
bash quadlet-homelab/bootstrap.sh
```

Ele confere git/python3/podman e o `systemd --user`, cria as pastas do Podman,
clona o repositório em `~/quadlet-homelab` e liga `qh`, `qh-check` e
`qh-updates` em `~/.local/bin`. Sem `sudo`, sem instalar pacote, sem subir
serviço.

Depois:

```bash
qh                   # os serviços
qh memos             # o plano de um, sem instalar
qh memos --apply     # fazer
```

Todo serviço fica acessível em `http://<ip-do-host>:<porta>` sem mais nada
configurado — sem domínio, sem certificado, sem mexer no roteador.

## Atualizando

Duas coisas diferentes, nesta ordem.

**O repositório** — as units e as receitas. Rodar o mesmo comando de novo, ou
dar pull no clone; dá no mesmo:

```bash
curl -fsSL https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/bootstrap.sh | bash
```

Ele avança o clone e refaz os links. Clone que divergiu é deixado em paz e
avisado, então edição local sua nunca é descartada.

**Os serviços no host** — nada se move até você mandar. Unit mais nova no
repositório não muda o arquivo já instalado:

```bash
qh-updates                     # quais imagens estão atrás da release do upstream
qh memos --update --apply      # um serviço
qh --all --update --apply      # depois de uma leva de bumps
```

O `--update` recopia as units, puxa a imagem e reinicia. Não toca em volume,
`.env` nem secret. Serviço que já está em dia é pulado — e isso inclui o
container em execução, não só o arquivo: o Quadlet grava as labels na
criação, então uma unit certa no disco pode estar rodando num container com
as anteriores. Tag móvel (`latest`) é sempre puxada. Para passar por cima,
use `--reinstall`.

## Requisitos

- **Podman 5.0 ou mais novo.** É a régua de verdade: o `Notify=healthy` chegou
  nessa versão, e 91 das 99 units usam. No 4.x o start volta antes de o app
  estar pronto, e a instalação relata um sucesso que ela não tem como saber.
- **systemd com sessão de usuário** e cgroups v2.
- **SELinux**, se a sua distribuição tiver. As units trazem `:Z` em 125 linhas
  de volume; onde não há SELinux elas são ignoradas e nada quebra, mas o
  isolamento por container que elas pedem também não existe.
- `/dev/kvm`, só para os seis serviços de VM.

```bash
podman --version
```

Medido, instalando o podman em cada uma e lendo a versão:

| Distribuição | Podman | |
| --- | --- | --- |
| Arch | 6.0.2 | funciona |
| openSUSE Tumbleweed, Slowroll | 6.0.2 | funciona |
| openSUSE MicroOS, Aeon, Kalpa | 5.8 | funciona |
| Fedora 42 | 5.8.2 | funciona |
| Debian 13 | 5.4.2 | funciona |
| openSUSE Leap 16.0 | 5.4.2 | funciona |
| Ubuntu 25.04 | 5.4.1 | funciona |
| Ubuntu 24.04 LTS | 4.9.3 | **antiga demais** |
| openSUSE Leap 15.6 | 4.9.5 | **antiga demais** |
| Debian 12 | 4.3.1 | **antiga demais** |

Aeon e Kalpa são MicroOS com desktop e compartilham os repositórios dele. O
Leap Micro segue a geração do Leap que o originou, então a linha 5.x herda o
problema do Leap 15 — ele não publica imagem de container e não foi medido
aqui.

## Serviços

| Logo | Aplicativo | Versão | Descrição |
| --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/actual-budget.svg" width="48" height="48" alt=""> | [Actual Budget](../../apps/actual-budget/README.pt-BR.md) | `latest` (auto-update) | Rápido e focado em privacidade pra gerenciar finanças pessoais, usando a metodologia de Orçamento de Envelope |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/adguard-home.svg" width="48" height="48" alt=""> | [AdGuard Home](../../apps/adguardhome/README.pt-BR.md) | `v0.107.78` | Servidor DNS recursivo com bloqueio de anúncios e rastreadores pra toda a rede |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/anytype.svg" width="48" height="48" alt=""> | [any-sync-bundle](../../apps/any-sync-bundle/README.pt-BR.md) | `1.5.0-2026-07-17` | Backend do protocolo Any-Sync, que sincroniza os dados do Anytype entre dispositivos sem depender da nuvem da empresa |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/audiobookshelf.svg" width="48" height="48" alt=""> | [Audiobookshelf](../../apps/audiobookshelf/README.pt-BR.md) | `2.36.0` | Servidor de audiolivros e podcasts, com progresso sincronizado entre dispositivos |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/authentik.svg" width="48" height="48" alt=""> | [Authentik](../../apps/authentik/README.pt-BR.md) | `2026.5.6` | Servidor de identidade (SSO, MFA, OIDC/SAML) — só o core implantado, sem forward-auth via tsdproxy ainda (ver README) |
| <img src="https://api.iconify.design/mdi/check-circle-outline.svg?color=%23888888" width="48" height="48" alt=""> | [Beaver Habits](../../apps/beaverhabits/README.pt-BR.md) | `0.10.0` | Acompanhamento de hábitos sem metas e sem cobrança de sequência — você marca o dia e segue |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/beszel.svg" width="48" height="48" alt=""> | [Beszel](../../apps/beszel/README.pt-BR.md) | `0.18.7` | Dashboard leve de monitoramento de recursos (CPU/RAM/disco/rede/containers) deste host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/calibre-web.svg" width="48" height="48" alt=""> | [Calibre-Web-Automated](../../apps/calibre-web-automated/README.pt-BR.md) | `v4.0.6` | Biblioteca de ebooks com conversão, metadados e capas automáticas via Calibre, com leitura direto no navegador |
| <img src="https://cdn.simpleicons.org/gnubash" width="48" height="48" alt=""> | [CookCLI](../../apps/cookcli/README.pt-BR.md) | `0.32.1` | Receitas em texto puro no formato CookLang — versionáveis em git, sem banco e sem formulário |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/copyparty.svg" width="48" height="48" alt=""> | [Copyparty](../../apps/copyparty/README.pt-BR.md) | `1.20.20` | Servidor de arquivos com upload pelo navegador ou celular, retomada de transferência e WebDAV |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/donetick.svg" width="48" height="48" alt=""> | [Donetick](../../apps/donetick/README.pt-BR.md) | `v0.1.76` | Tarefas domésticas recorrentes — quem faz, com que frequência e quando vence |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/excalidraw.svg" width="48" height="48" alt=""> | [ExcaliDash](../../apps/excalidash/README.pt-BR.md) | `0.5.1` | Painel para desenhos do Excalidraw — pastas, compartilhamento e multiusuário, no seu armazenamento |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/filebrowser-quantum.svg" width="48" height="48" alt=""> | [FileBrowser Quantum](../../apps/filebrowser/README.pt-BR.md) | `1.5.1-stable` | Gerenciador de arquivos web — busca, miniaturas, WebDAV e um shell sobre um diretório que você escolhe |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/freshrss.svg" width="48" height="48" alt=""> | [FreshRSS](../../apps/freshrss/README.pt-BR.md) | `1.29.1-alpine` | Agregador de feeds RSS/Atom self-hosted, com API compatível pra apps móveis |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/frigate.png" width="48" height="48" alt=""> | [Frigate](../../apps/frigate/README.pt-BR.md) | `0.17.2` | NVR com detecção de objetos por IA — CPU-only por padrão, sem câmera configurada ainda (ver README) |
| <img src="https://cdn.simpleicons.org/ghost" width="48" height="48" alt=""> | [Ghost](../../apps/ghost/README.pt-BR.md) | `6.56.0-alpine` | Blog/newsletter self-hosted (SQLite, modo development — ver README) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gitea.svg" width="48" height="48" alt=""> | [Gitea](../../apps/gitea/README.pt-BR.md) | `1.27.1` | Servidor Git leve e completo — repositórios, issues, pull requests e CI numa interface só |
| <img src="https://cdn.jsdelivr.net/gh/NousResearch/hermes-agent@main/website/static/img/logo.png" width="48" height="48" alt=""> | [Hermes Agent](../../apps/hermes-agent/README.pt-BR.md) | `v2026.8.3` | Agente de IA pessoal com habilidades e memória, expondo uma API compatível com a da OpenAI pros outros serviços chamarem |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/homebox.svg" width="48" height="48" alt=""> | [HomeBox](../../apps/homebox/README.pt-BR.md) | `0.26.2` | Inventário doméstico — o que você tem, onde está, nota fiscal, manual e garantia, com busca e etiquetas |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/grafana.svg" width="48" height="48" alt=""> | [Grafana](../../apps/grafana/README.pt-BR.md) | `13.1.3` | Painéis sobre o que você apontar — ele não traz dado nenhum próprio |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/grafana.svg" width="48" height="48" alt=""> | [Grafana](../../apps/grafana/README.pt-BR.md) | `13.1.3` | Painéis sobre o que você apontar — ele não traz dado nenhum próprio |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/home-assistant.svg" width="48" height="48" alt=""> | [Home Assistant](../../apps/home-assistant/README.pt-BR.md) | `2026.8.1` | Hub central de automação residencial, integra dispositivos de qualquer fabricante num painel só |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/homepage.png" width="48" height="48" alt=""> | [homepage](../../apps/homepage/README.pt-BR.md) | `latest` (auto-update) | Dashboard que descobre e organiza os outros containers sozinho via labels, sem editar config a cada serviço novo |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/immich.svg" width="48" height="48" alt=""> | [Immich](../../apps/immich/README.pt-BR.md) | `v3.1.0` | Backup e organização de fotos/vídeos, com reconhecimento facial e busca smart |
| <img src="https://cdn.simpleicons.org/invoiceninja/888888" width="48" height="48" alt=""> | [Invio](../../apps/invio/README.pt-BR.md) | `v2.1.1` | Emissão e controle de faturas self-hosted, com SQLite e sem depender de serviço externo |
| <img src="https://api.iconify.design/mdi/microphone-variant.svg?color=%23888888" width="48" height="48" alt=""> | [Karaoke Eternal](../../apps/karaoke-eternal/README.pt-BR.md) | `2.0.2` | Karaokê com a sua própria biblioteca — cada um enfileira do celular, uma tela reproduz |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/karakeep.svg" width="48" height="48" alt=""> | [Karakeep](../../apps/karakeep/README.pt-BR.md) | `0.33.1` | Gerenciador de bookmarks com busca full-text e arquivamento automático do conteúdo de cada página salva |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/lubelogger.png" width="48" height="48" alt=""> | [LubeLogger](../../apps/lubelogger/README.pt-BR.md) | `v1.7.0` | Registro de manutenção veicular — trocas de óleo, revisões, gastos e lembretes, por veículo |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/mailpit.svg" width="48" height="48" alt=""> | [Mailpit](../../apps/mailpit/README.pt-BR.md) | `v1.30.7` | Servidor SMTP que captura tudo que seus apps enviam, para ler no navegador em vez de numa caixa de entrada de verdade |
| <img src="https://cdn.simpleicons.org/markdown/888888" width="48" height="48" alt=""> | [mdrop](../../apps/mdrop/README.pt-BR.md) | `latest` (pinado por digest) | Converte PDF, Office, imagem e áudio para Markdown pela web, sem estado e sem sair da máquina |
| <img src="https://api.iconify.design/mdi/multimedia.svg?color=%23888888" width="48" height="48" alt=""> | [Media Stack](../../apps/media-stack/README.pt-BR.md) | — | Jellyfin, Navidrome, Seerr, Prowlarr, Sonarr, Radarr, Lidarr, Bazarr, SABnzbd, Deluge, Dispatcharr, Downtify e um Gluetun opcional — servidor de mídia + automação, raiz de dados compartilhada, cada app com sua própria versão |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/memos.svg" width="48" height="48" alt=""> | [Memos](../../apps/memos/README.pt-BR.md) | `0.30.0` | Notas rápidas, self-hosted e markdown-nativo |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/metube.svg" width="48" height="48" alt=""> | [MeTube](../../apps/metube/README.pt-BR.md) | `2026.08.04` | Interface web do yt-dlp — cola a URL e o vídeo cai no disco |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/monica.svg" width="48" height="48" alt=""> | [Monica](../../apps/monica/README.pt-BR.md) | `main` (sem tag fixa, ver README) | CRM pessoal — histórico de relacionamentos, contatos, lembretes |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/n8n.svg" width="48" height="48" alt=""> | [n8n](../../apps/n8n/README.pt-BR.md) | `2.33.7` | Automação de workflows via editor visual de nós |
| <img src="https://api.iconify.design/mdi/web-box.svg?color=%23888888" width="48" height="48" alt=""> | [neko](../../apps/neko/README.pt-BR.md) | `3.1.5` | Um navegador rodando no servidor, transmitido para o seu — controle compartilhado, e nada do que ele abre toca a sua máquina |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/netbootxyz.svg" width="48" height="48" alt=""> | [netboot.xyz](../../apps/netbootxyz/README.pt-BR.md) | `0.7.6-nbxyz23` | Menu de boot pela rede (PXE) pra instalar ou testar distros e ferramentas sem gravar pendrive |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/nginx.svg" width="48" height="48" alt=""> | [nginx](../../apps/nginx/README.pt-BR.md) | `1.30.4-alpine` | Servidor de arquivos estáticos |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/node-red.svg" width="48" height="48" alt=""> | [Node-RED](../../apps/node-red/README.pt-BR.md) | `5.0.4-minimal` | Automação de fluxos via editor visual de nós |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/ntfy.svg" width="48" height="48" alt=""> | [ntfy](../../apps/ntfy/README.pt-BR.md) | `v2.27.0` | Servidor de notificações push — destino dos alertas do uptime-kuma, wud e zerobyte, com app no celular |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/open-webui.svg" width="48" height="48" alt=""> | [Open WebUI](../../apps/openwebui/README.pt-BR.md) | `v0.11.0` (Open WebUI) + `0.32.6` (Ollama) | Interface de chat web + servidor de LLMs locais, CPU-only por padrão (opções de GPU NVIDIA/AMD documentadas) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/omni-tools.png" width="48" height="48" alt=""> | [Omni Tools](../../apps/omni-tools/README.pt-BR.md) | `0.6.0` | Conversores, geradores e calculadoras que rodam no navegador — nada é enviado ao servidor |
| <img src="https://cdn.jsdelivr.net/gh/rmyndharis/OpenWA@main/docs/logo/openwa.svg" width="48" height="48" alt=""> | [OpenWA](../../apps/openwa/README.pt-BR.md) | `0.15.0` | Gateway de API do WhatsApp — transforma a conta em REST + webhooks, pro n8n e o Home Assistant usarem |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owncloud.svg" width="48" height="48" alt=""> | [ownCloud](../../apps/owncloud/README.pt-BR.md) | `11.0.0-20260802` | Sincronização e compartilhamento de arquivos em nuvem própria |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owntracks.svg" width="48" height="48" alt=""> | [OwnTracks](../../apps/owntracks/README.pt-BR.md) | `1.0.2` | Rastreamento de localização pessoal via app de celular, com broker MQTT próprio e histórico de posições |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/paperless-ngx.svg" width="48" height="48" alt=""> | [Paperless-ngx](../../apps/paperless-ngx/README.pt-BR.md) | `3.0.5` | Digitaliza, faz OCR e indexa documentos automaticamente, com busca full-text pra nunca mais procurar papel |
| <img src="https://api.iconify.design/mdi/email-fast.svg?color=%23888888" width="48" height="48" alt=""> | [Postfix](../../apps/postfix/README.pt-BR.md) | `v5.1.0` | Relay SMTP para os outros containers — eles entregam num lugar só, e a credencial do provedor fica só aqui |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prometheus.svg" width="48" height="48" alt=""> | [Prometheus](../../apps/prometheus/README.pt-BR.md) | `v3.13.2` | Coleta métricas em intervalo e guarda o histórico — a fonte de dados que o Grafana desenha |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/proxmox.svg" width="48" height="48" alt=""> | [Proxmox VE](../../apps/proxmox/README.pt-BR.md) | `9.2.9` | O hypervisor Proxmox num container, pra experimentar sem dedicar uma máquina — roda privileged |
| <img src="https://api.iconify.design/mdi/gamepad-variant.svg?color=%23888888" width="48" height="48" alt=""> | [Retrom](../../apps/retrom/README.pt-BR.md) | `0.8.4` | Biblioteca de jogos para emulação — uma coleção só, jogada no navegador ou pelo cliente de desktop |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radicale.svg" width="48" height="48" alt=""> | [Radicale](../../apps/radicale/README.pt-BR.md) | `v0.26.0` | Servidor CalDAV/CardDAV leve e minimalista, no rebuild que traz o script do calendário de aniversários (Radicale 3.7.6.0 dentro) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/stirling-pdf.svg" width="48" height="48" alt=""> | [Stirling-PDF](../../apps/stirling-pdf/README.pt-BR.md) | `2.14.3` | Manipulação de PDF local — juntar, dividir, converter, OCR e assinar, no lugar dos sites de "PDF online" |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/syncthing.svg" width="48" height="48" alt=""> | [Syncthing](../../apps/syncthing/README.pt-BR.md) | `2.1.3` | Sincronização de arquivos P2P entre dispositivos, sem servidor central |
| <img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/tsdproxy.svg" width="48" height="48" alt=""> | [tsdproxy](../../apps/tsdproxy/README.pt-BR.md) | `2` | Publica containers na tailnet automaticamente, só com labels — sem configurar proxy manualmente por serviço |
| <img src="https://cdn.jsdelivr.net/gh/containers/containertoolbx.org@main/apple-touch-icon.png" width="48" height="48" alt=""> | [Toolbx](../../apps/toolbx/README.pt-BR.md) | — | Shells descartáveis de Arch, Fedora, RHEL e Ubuntu, nas imagens oficiais do Toolbx — um lugar pra instalar ferramenta avulsa que não é o host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/traccar.svg" width="48" height="48" alt=""> | [Traccar](../../apps/traccar/README.pt-BR.md) | `6.14.5` | Rastreamento de GPS — mapa ao vivo, histórico, geocercas e relatórios, com app no celular |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="48" height="48" alt=""> | [VM](../../apps/vm/README.pt-BR.md) | — | Windows, macOS, ChromeOS Flex, ZimaOS e 23 distros Linux como VMs em containers, vistas pelo navegador — exige KVM no host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/uptime-kuma.svg" width="48" height="48" alt=""> | [Uptime Kuma](../../apps/uptime-kuma/README.pt-BR.md) | `2.5.0` | Monitor de disponibilidade dos outros serviços e da tailnet, com histórico e notificação |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/vaultwarden.png" width="48" height="48" alt=""> | [Vaultwarden](../../apps/vaultwarden/README.pt-BR.md) | `1.37.1-alpine` | Cofre de senhas compatível com o protocolo do Bitwarden, leve o bastante pra rodar em qualquer lugar |
| <img src="https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg" width="48" height="48" alt=""> | [VaultZap](../../apps/vaultzap/README.pt-BR.md) | `latest` (auto-update) | Arquivo local e navegável de conversas exportadas do WhatsApp — busca, galeria e calendário, 100% offline |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/wger.svg" width="48" height="48" alt=""> | [wger](../../apps/wger/README.pt-BR.md) | `2.6.0` | Planejamento e acompanhamento de treinos, com banco de exercícios e medidas corporais |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zigbee2mqtt.svg" width="48" height="48" alt=""> | [Zigbee2MQTT](../../apps/zigbee2mqtt/README.pt-BR.md) | `2.13.0` | Ponte entre dispositivos Zigbee e MQTT, sem hub proprietário — sem coordenador ligado ainda (ver README) |
| <img src="https://cdn.jsdelivr.net/gh/getwud/wud@main/ui/public/img/icons/android-chrome-512x512.png" width="48" height="48" alt=""> | [WUD (What's Up Docker)](../../apps/wud/README.pt-BR.md) | `8.3.1` | Monitora as atualizações de imagem disponíveis pros containers, sem aplicar nada sozinho — só avisa |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/zerobyte.png" width="48" height="48" alt=""> | [Zerobyte](../../apps/zerobyte/README.pt-BR.md) | `v0.41.0` | Automatiza backup (via Restic) dos dados de todos os outros serviços deste repositório |

**AutoUpdate ligado**: Actual Budget, homepage, VaultZap. Todo o resto tem tag
fixa e é atualizado na mão.

## Opcional: a tailnet

O [Tailscale](https://tailscale.com) com o tsdproxy dá a cada serviço um nome
HTTPS próprio, alcançável de qualquer lugar sem abrir porta. O Vaultwarden
precisa disso — ele só decifra a sessão em contexto seguro.

O `qh tailscale` confere os três passos abaixo no host e mostra só o que
falta.

Instalar o Tailscale pela sua distribuição (ver
[tailscale.com/download](https://tailscale.com/download)) e depois:

```bash
sudo systemctl enable --now tailscaled
sudo tailscale up

mkdir -p ~/.config/environment.d
echo 'TAILNET=<your-tailnet>' > ~/.config/environment.d/tailnet.conf
systemctl --user daemon-reload

qh tsdproxy --apply
```

Sem tailnet, defina a regra uma vez e toda instalação a segue:

```bash
qh --set-access local
```

Ele aponta o link do dashboard pro endereço da LAN e comenta as labels
`tsdproxy.*` em vez de apagá-las. Ligar depois é uma atualização, que preserva
os dados:

```bash
qh --all --update --apply --access tailnet
```

## Num servidor ARM

Quase toda imagem aqui publica variante `arm64` e instala sem mudança. Três
não publicam, e levam o serviço junto:

| Imagem | Serviço |
| --- | --- |
| `dockurr/macos` | `vm-macos` |
| `dockurr/chromeos` | `vm-chromeos` |
| `quay.io/toolbx/arch-toolbox` | `toolbx-arch` |

Nos serviços de VM quem decide é o convidado, não a imagem: o KVM só acelera
convidado da mesma arquitetura. O `apps/vm` traz `vm-windows` pra x86_64 e
`vm-windows-arm` pra ARM64.

## Documentação

| | |
| --- | --- |
| [Instalando e operando](./instalacao.md) | instalar, atualizar, backup, restaurar, remover |
| [Recuperação e migração](./recuperacao.md) | a máquina morreu, ou você está mudando de host |
| [Referência](./referencia.md) | onde cada arquivo mora, e um `.container` anotado |
| [Auto-update](./auto-update.md) | por que quase tudo atualiza na mão |
| [Ferramentas](./ferramentas.md) | `qh-check` e `qh-updates` |

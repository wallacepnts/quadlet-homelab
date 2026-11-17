# Quadlet Homelab

**[🇺🇸 Read in English](../../README.md)**

83 serviços self-hosted como units do [Podman Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html),
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
clona o repositório em `~/quadlet-homelab`, liga as ferramentas em `~/.local/bin` e
**sobe o painel web** como um serviço `systemd --user` seu. Sem `sudo`, sem instalar
pacote. Pergunta uma vez de onde você vai abrir o painel (só desta máquina, da rede local
ou da tailnet) e termina mostrando o endereço e o token de login:

```
  painel no ar: http://127.0.0.1:8484
  login (o token): …
```

**Abra esse endereço num navegador: é assim que se usa isto.** O painel tem a Loja (os 83
serviços, por categoria, com capturas de tela) e Meus apps (o que está instalado, como um
lançador). Por ele você instala um app (só pergunta o que aquele app precisa, e deixa
personalizar portas, volumes e variáveis antes, ou experimentar por algumas horas), atualiza com
um botão, faz backup, restaura, muda as configurações, lê os logs ao vivo, abre um console no
container, pausa, para ou remove, e vê a carga, a memória e a temperatura do host. Cada botão
roda o mesmo motor `qh` que um terminal rodaria; nada no painel é uma segunda implementação.

Todo serviço fica acessível em `http://<ip-do-host>:<porta>` sem mais nada
configurado — sem domínio, sem certificado, sem mexer no roteador.

<details>
<summary>O terminal, se você preferir (avançado)</summary>

```bash
qh                   # os serviços
qh memos             # o plano de um, sem instalar
qh memos --apply     # fazer
```

[Instalar e operar](./instalacao.md) lista todos os modos.
</details>

## Atualizando

Duas coisas diferentes, nesta ordem.

**O repositório** — as units e as receitas. Rodar o mesmo comando de novo, ou
dar pull no clone; dá no mesmo:

```bash
curl -fsSL https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/bootstrap.sh | bash
```

Ele avança o clone e cria os links que faltam — link que já aponta pra outro
clone ele nomeia, não move. Clone que divergiu é deixado em paz e avisado,
então edição local sua nunca é descartada.

**Os serviços no host** — nada se move até você mandar. No painel, um app com release
nova mostra o botão **Atualizar para X**, e Meus apps tem **Atualizar todos** para os que
têm algo a pegar (cada um reinicia; uma falha não interrompe os outros). Unit mais nova no
repositório não muda o arquivo já instalado. O mesmo, num terminal:

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
  nessa versão, e 117 das 125 units usam. No 4.x o start volta antes de o app
  estar pronto, e a instalação relata um sucesso que ela não tem como saber.
- **systemd com sessão de usuário** e cgroups v2.
- **`network-online.target` alcançado no boot.** O Quadlet ordena toda unit que
  gera atrás do `podman-user-wait-network-online.service`, que gira em
  `until systemctl is-active network-online.target` até o timeout de 90s. Um
  target só é ativado quando alguém o requer, e desktop muitas vezes não requer
  nada — medido no Tumbleweed com KDE, onde o único que pedia era um oneshot já
  terminado. A dependência é `Wants=`, então o serviço sobe: noventa segundos
  atrasado, em cada start.
  `sudo systemctl add-wants multi-user.target network-online.target` resolve, e
  o boot passa a esperar o `NetworkManager-wait-online` — segundos quando a
  máquina tem rede, `NM_ONLINE_TIMEOUT` quando não tem.
- **SELinux**, se a sua distribuição tiver. As units trazem `:Z` em 125 linhas
  de volume; onde não há SELinux elas são ignoradas e nada quebra, mas o
  isolamento por container que elas pedem também não existe. As seis units que
  montam o socket do Podman precisam de mais que rótulo — só `:z` as deixa
  saudáveis e cegas, sem enxergar container nenhum, então elas declaram
  `SecurityLabelType=container_runtime_t` (regra 16 das convenções).
- `/dev/kvm` para os seis serviços de VM, e `/dev/net/tun` para esses mais o
  gluetun. Os dois são `0666` numa instalação usual, então o rootless os
  alcança sem mudar grupo nenhum.
- `/dev/dri`, só para o `vm-chromeos`, que repassa a GPU do host. Esse é
  `0660 root:render`, e funciona sem você entrar nesse grupo apenas porque o
  logind põe uma ACL nele para a **sessão ativa**. Um host headless rodando
  com `enable-linger` e sem seat pode não ter essa ACL, e o sintoma é um
  container que sobe e renderiza por software. Confira com
  `getfacl /dev/dri/renderD128` antes de culpar a imagem.

```bash
podman --version
systemctl is-active network-online.target
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

<!-- services:begin (generated from apps/*/app.json: python3 check.py --readme) -->

| Logo | Aplicativo | Descrição |
| --- | --- | --- |
| <img src="../../apps/actual-budget/icon.svg" width="48" height="48" alt=""> | [Actual Budget](../../apps/actual-budget) | A simple tool to plan and track your money. |
| <img src="../../apps/adguardhome/icon.svg" width="48" height="48" alt=""> | [AdGuard Home](../../apps/adguardhome) | Blocks ads and trackers on your whole network. |
| <img src="../../apps/anki/icon.svg" width="48" height="48" alt=""> | [Anki](../../apps/anki) | A sync server for your Anki flashcards. |
| <img src="../../apps/any-sync-bundle/icon.svg" width="48" height="48" alt=""> | [any-sync-bundle](../../apps/any-sync-bundle) | A sync server for the Anytype app. |
| <img src="../../apps/audiobookshelf/icon.svg" width="48" height="48" alt=""> | [Audiobookshelf](../../apps/audiobookshelf) | A server for your audiobooks and podcasts. |
| <img src="../../apps/authentik/icon.svg" width="48" height="48" alt=""> | [Authentik](../../apps/authentik) | A login and single sign-on server. |
| <img src="../../apps/beaverhabits/icon.png" width="48" height="48" alt=""> | [Beaver Habits](../../apps/beaverhabits) | A simple habit tracker. |
| <img src="../../apps/beszel/icon.svg" width="48" height="48" alt=""> | [Beszel](../../apps/beszel) | Shows how busy your server is. |
| <img src="../../apps/calibre-web-automated/icon.svg" width="48" height="48" alt=""> | [Calibre-Web-Automated](../../apps/calibre-web-automated) | Read and manage your ebook library in the browser. |
| <img src="../../apps/casa/icon.svg" width="48" height="48" alt=""> | [CasaOS](../../apps/casa) | A home server dashboard. |
| <img src="../../apps/changedetection/icon.svg" width="48" height="48" alt=""> | [changedetection.io](../../apps/changedetection) | Tells you when a web page changes. |
| <img src="../../apps/collabora/icon.svg" width="48" height="48" alt=""> | [Collabora](../../apps/collabora) | Edit documents in your browser. |
| <img src="../../apps/cookcli/icon.svg" width="48" height="48" alt=""> | [CookCLI](../../apps/cookcli) | Keep your recipes as plain text files. |
| <img src="../../apps/copyparty/icon.svg" width="48" height="48" alt=""> | [Copyparty](../../apps/copyparty) | A file server you can upload to from any device. |
| <img src="../../apps/docuseal/icon.svg" width="48" height="48" alt=""> | [DocuSeal](../../apps/docuseal) | Sign documents on your own server. |
| <img src="../../apps/donetick/icon.svg" width="48" height="48" alt=""> | [Donetick](../../apps/donetick) | Keep track of household chores. |
| <img src="../../apps/dozzle/icon.svg" width="48" height="48" alt=""> | [Dozzle](../../apps/dozzle) | Read your containers' logs in the browser. |
| <img src="../../apps/excalidash/icon.svg" width="48" height="48" alt=""> | [ExcaliDash](../../apps/excalidash) | A place to organize and share Excalidraw drawings. |
| <img src="../../apps/faved/icon.svg" width="48" height="48" alt=""> | [Faved](../../apps/faved) | A simple place to save bookmarks. |
| <img src="../../apps/ferdium-server/icon.svg" width="48" height="48" alt=""> | [Ferdium Server](../../apps/ferdium-server) | A sync server for the Ferdium app. |
| <img src="../../apps/filebrowser/icon.svg" width="48" height="48" alt=""> | [FileBrowser Quantum](../../apps/filebrowser) | A file manager in your browser. |
| <img src="../../apps/fmd-server/icon.svg" width="48" height="48" alt=""> | [FMD Server](../../apps/fmd-server) | Find your Android phone from the browser. |
| <img src="../../apps/freshrss/icon.svg" width="48" height="48" alt=""> | [FreshRSS](../../apps/freshrss) | Read all your news feeds in one place. |
| <img src="../../apps/frigate/icon.svg" width="48" height="48" alt=""> | [Frigate](../../apps/frigate) | A security camera recorder that spots people and objects. |
| <img src="../../apps/ghost/icon.webp" width="48" height="48" alt=""> | [Ghost](../../apps/ghost) | A blog and newsletter platform. |
| <img src="../../apps/gitea/icon.svg" width="48" height="48" alt=""> | [Gitea](../../apps/gitea) | A simple Git server for your code. |
| <img src="../../apps/gitea-runner/icon.svg" width="48" height="48" alt=""> | [Gitea Runner](../../apps/gitea-runner) | Runs the automated workflows of your Gitea. |
| <img src="../../apps/grafana/icon.svg" width="48" height="48" alt=""> | [Grafana](../../apps/grafana) | Charts and dashboards for your data. |
| <img src="../../apps/hermes-agent/icon.png" width="48" height="48" alt=""> | [Hermes Agent](../../apps/hermes-agent) | A personal AI assistant. |
| <img src="../../apps/home-assistant/icon.svg" width="48" height="48" alt=""> | [Home Assistant](../../apps/home-assistant) | Control all your smart home devices in one place. |
| <img src="../../apps/homebox/icon.svg" width="48" height="48" alt=""> | [HomeBox](../../apps/homebox) | Keep an inventory of everything you own. |
| <img src="../../apps/homepage/icon.png" width="48" height="48" alt=""> | [homepage](../../apps/homepage) | A start page for your home server. |
| <img src="../../apps/immich/icon.svg" width="48" height="48" alt=""> | [Immich](../../apps/immich) | Back up and browse your photos and videos. |
| <img src="../../apps/instagram-monitor/icon.svg" width="48" height="48" alt=""> | [Instagram Monitor](../../apps/instagram-monitor) | Watches Instagram profiles and shows their activity. |
| <img src="../../apps/invio/icon.svg" width="48" height="48" alt=""> | [Invio](../../apps/invio) | Create and track invoices. |
| <img src="../../apps/karakeep/icon.svg" width="48" height="48" alt=""> | [Karakeep](../../apps/karakeep) | Save and search your bookmarks. |
| <img src="../../apps/karaoke-eternal/icon.svg" width="48" height="48" alt=""> | [Karaoke Eternal](../../apps/karaoke-eternal) | Run karaoke parties from your own songs. |
| <img src="../../apps/kiwix/icon.svg" width="48" height="48" alt=""> | [Kiwix](../../apps/kiwix) | Read Wikipedia and other libraries offline. |
| <img src="../../apps/koffan/icon.png" width="48" height="48" alt=""> | [Koffan](../../apps/koffan) | A shared shopping list. |
| <img src="../../apps/komga/icon.svg" width="48" height="48" alt=""> | [Komga](../../apps/komga) | Read your comics and manga. |
| <img src="../../apps/lubelogger/icon.png" width="48" height="48" alt=""> | [LubeLogger](../../apps/lubelogger) | Track maintenance for your vehicles. |
| <img src="../../apps/mailpit/icon.svg" width="48" height="48" alt=""> | [Mailpit](../../apps/mailpit) | Catches the emails your apps send so you can read them. |
| <img src="../../apps/mdrop/icon.svg" width="48" height="48" alt=""> | [mdrop](../../apps/mdrop) | Turn documents into Markdown. |
| <img src="../../apps/media-stack/icon.svg" width="48" height="48" alt=""> | [Media Stack](../../apps/media-stack) | A media server and the tools that fill it. |
| <img src="../../apps/memos/icon.svg" width="48" height="48" alt=""> | [Memos](../../apps/memos) | A simple place for quick notes. |
| <img src="../../apps/metube/icon.svg" width="48" height="48" alt=""> | [MeTube](../../apps/metube) | Download videos from the web. |
| <img src="../../apps/monica/icon.svg" width="48" height="48" alt=""> | [Monica](../../apps/monica) | Remember the people in your life. |
| <img src="../../apps/n8n/icon.svg" width="48" height="48" alt=""> | [n8n](../../apps/n8n) | Automate tasks between your apps. |
| <img src="../../apps/neko/icon.svg" width="48" height="48" alt=""> | [neko](../../apps/neko) | A shared browser you can use together. |
| <img src="../../apps/netbootxyz/icon.svg" width="48" height="48" alt=""> | [netboot.xyz](../../apps/netbootxyz) | Install an operating system over the network. |
| <img src="../../apps/nginx/icon.svg" width="48" height="48" alt=""> | [nginx](../../apps/nginx) | A web server for static files. |
| <img src="../../apps/node-red/icon.svg" width="48" height="48" alt=""> | [Node-RED](../../apps/node-red) | Automate things by connecting blocks. |
| <img src="../../apps/ntfy/icon.svg" width="48" height="48" alt=""> | [ntfy](../../apps/ntfy) | Send notifications to your phone. |
| <img src="../../apps/omni-tools/icon.png" width="48" height="48" alt=""> | [Omni Tools](../../apps/omni-tools) | Handy tools that run in your browser. |
| <img src="../../apps/openwebui/icon.svg" width="48" height="48" alt=""> | [Open WebUI](../../apps/openwebui) | A chat interface for AI models. |
| <img src="../../apps/openwa/icon.svg" width="48" height="48" alt=""> | [OpenWA](../../apps/openwa) | Send WhatsApp messages from your other apps. |
| <img src="../../apps/owncloud/icon.svg" width="48" height="48" alt=""> | [ownCloud](../../apps/owncloud) | Your own cloud for files. |
| <img src="../../apps/owntracks/icon.svg" width="48" height="48" alt=""> | [OwnTracks](../../apps/owntracks) | Track your location from your phone. |
| <img src="../../apps/paperless-ngx/icon.svg" width="48" height="48" alt=""> | [Paperless-ngx](../../apps/paperless-ngx) | Scan and search your paper documents. |
| <img src="../../apps/pkvault/icon.svg" width="48" height="48" alt=""> | [PKVault](../../apps/pkvault) | Manage your Pokémon save files. |
| <img src="../../apps/postfix/icon.svg" width="48" height="48" alt=""> | [Postfix](../../apps/postfix) | Sends email on behalf of your other apps. |
| <img src="../../apps/postiz/icon.svg" width="48" height="48" alt=""> | [Postiz](../../apps/postiz) | Schedule your social media posts. |
| <img src="../../apps/prometheus/icon.svg" width="48" height="48" alt=""> | [Prometheus](../../apps/prometheus) | Collects numbers about how your services run. |
| <img src="../../apps/proxmox/icon.svg" width="48" height="48" alt=""> | [Proxmox VE](../../apps/proxmox) | Try the Proxmox virtualization system. |
| <img src="../../apps/radicale/icon.svg" width="48" height="48" alt=""> | [Radicale](../../apps/radicale) | A calendar and contacts server. |
| <img src="../../apps/rclone/icon.svg" width="48" height="48" alt=""> | [rclone](../../apps/rclone) | Move files between your cloud accounts. |
| <img src="../../apps/retrom/icon.webp" width="48" height="48" alt=""> | [Retrom](../../apps/retrom) | A library for your retro games. |
| <img src="../../apps/searxng/icon.png" width="48" height="48" alt=""> | [SearXNG](../../apps/searxng) | Search the web without being tracked. |
| <img src="../../apps/stirling-pdf/icon.svg" width="48" height="48" alt=""> | [Stirling-PDF](../../apps/stirling-pdf) | Edit and convert PDF files. |
| <img src="../../apps/syncthing/icon.svg" width="48" height="48" alt=""> | [Syncthing](../../apps/syncthing) | Sync files between your devices. |
| <img src="../../apps/toolbx/icon.png" width="48" height="48" alt=""> | [Toolbx](../../apps/toolbx) | Throwaway Linux shells for trying things. |
| <img src="../../apps/traccar/icon.svg" width="48" height="48" alt=""> | [Traccar](../../apps/traccar) | Track vehicles and devices by GPS. |
| <img src="../../apps/tsdproxy/icon.svg" width="48" height="48" alt=""> | [tsdproxy](../../apps/tsdproxy) | Puts your apps on your tailnet automatically. |
| <img src="../../apps/uptime-kuma/icon.svg" width="48" height="48" alt=""> | [Uptime Kuma](../../apps/uptime-kuma) | Tells you when a service goes down. |
| <img src="../../apps/vaultwarden/icon.png" width="48" height="48" alt=""> | [Vaultwarden](../../apps/vaultwarden) | A password manager you host yourself. |
| <img src="../../apps/vaultzap/icon.svg" width="48" height="48" alt=""> | [VaultZap](../../apps/vaultzap) | Browse your exported WhatsApp chats. |
| <img src="../../apps/vikunja/icon.svg" width="48" height="48" alt=""> | [Vikunja](../../apps/vikunja) | A to-do list for tasks and projects. |
| <img src="../../apps/vm/icon.svg" width="48" height="48" alt=""> | [VM](../../apps/vm) | Run Windows, macOS and Linux in a container. |
| <img src="../../apps/wger/icon.svg" width="48" height="48" alt=""> | [wger](../../apps/wger) | Plan and track your workouts. |
| <img src="../../apps/wud/icon.png" width="48" height="48" alt=""> | [WUD (What's Up Docker)](../../apps/wud) | Tells you when your containers have updates. |
| <img src="../../apps/zabbix/icon.svg" width="48" height="48" alt=""> | [Zabbix](../../apps/zabbix) | Monitors your servers and network. |
| <img src="../../apps/zerobyte/icon.png" width="48" height="48" alt=""> | [Zerobyte](../../apps/zerobyte) | Backs up your apps' data. |
| <img src="../../apps/zigbee2mqtt/icon.svg" width="48" height="48" alt=""> | [Zigbee2MQTT](../../apps/zigbee2mqtt) | Use Zigbee devices without the maker's hub. |

<!-- services:end -->

**Nada atualiza sozinho.** Toda imagem é fixada — numa versão, ou num digest
onde o projeto não publica versão — e atualizada na mão; ver
[auto-update](./auto-update.md).

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

Ele comenta as labels `tsdproxy.*` em vez de apagá-las. Ligar depois é uma atualização, que preserva
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
| [O manifesto do app](./manifesto.md) | `apps/<app>/app.json`: tudo o que um app diz de si mesmo |
| [Auto-update](./auto-update.md) | por que nada atualiza sozinho |
| [Endurecimento, o que foi medido](./endurecimento.md) | o que cada imagem aceitou, e os erros do que ela recusou |
| [Ferramentas](./ferramentas.md) | `qh-check` e `qh-updates` |

# Quadlet Homelab

**[🇺🇸 Read in English](../../README.md)**

84 serviços self-hosted como units do [Podman Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html),
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
  nessa versão, e 119 das 127 units usam. No 4.x o start volta antes de o app
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
| <img src="../../apps/actual-budget/icon.svg" width="48" height="48" alt=""> | [Actual Budget](../../apps/actual-budget) | Uma ferramenta simples para planejar e acompanhar seu dinheiro. |
| <img src="../../apps/adguardhome/icon.svg" width="48" height="48" alt=""> | [AdGuard Home](../../apps/adguardhome) | Bloqueia anúncios e rastreadores em toda a sua rede. |
| <img src="../../apps/anki/icon.svg" width="48" height="48" alt=""> | [Anki](../../apps/anki) | Um servidor de sincronização para os seus cartões do Anki. |
| <img src="../../apps/any-sync-bundle/icon.svg" width="48" height="48" alt=""> | [any-sync-bundle](../../apps/any-sync-bundle) | Um servidor de sincronização para o app Anytype. |
| <img src="../../apps/audiobookshelf/icon.svg" width="48" height="48" alt=""> | [Audiobookshelf](../../apps/audiobookshelf) | Um servidor para seus audiolivros e podcasts. |
| <img src="../../apps/authentik/icon.svg" width="48" height="48" alt=""> | [Authentik](../../apps/authentik) | Um servidor de login e de login único. |
| <img src="../../apps/beaverhabits/icon.png" width="48" height="48" alt=""> | [Beaver Habits](../../apps/beaverhabits) | Um acompanhador de hábitos simples. |
| <img src="../../apps/beszel/icon.svg" width="48" height="48" alt=""> | [Beszel](../../apps/beszel) | Mostra o quanto o seu servidor está ocupado. |
| <img src="../../apps/calibre-web-automated/icon.svg" width="48" height="48" alt=""> | [Calibre-Web-Automated](../../apps/calibre-web-automated) | Leia e gerencie sua biblioteca de ebooks no navegador. |
| <img src="../../apps/casa/icon.svg" width="48" height="48" alt=""> | [CasaOS](../../apps/casa) | Um painel para o servidor doméstico. |
| <img src="../../apps/changedetection/icon.svg" width="48" height="48" alt=""> | [changedetection.io](../../apps/changedetection) | Avisa quando uma página da web muda. |
| <img src="../../apps/collabora/icon.svg" width="48" height="48" alt=""> | [Collabora](../../apps/collabora) | Edite documentos no navegador. |
| <img src="../../apps/cookcli/icon.svg" width="48" height="48" alt=""> | [CookCLI](../../apps/cookcli) | Guarde suas receitas como arquivos de texto simples. |
| <img src="../../apps/copyparty/icon.svg" width="48" height="48" alt=""> | [Copyparty](../../apps/copyparty) | Um servidor de arquivos que aceita envios de qualquer aparelho. |
| <img src="../../apps/docuseal/icon.svg" width="48" height="48" alt=""> | [DocuSeal](../../apps/docuseal) | Assine documentos no seu próprio servidor. |
| <img src="../../apps/donetick/icon.svg" width="48" height="48" alt=""> | [Donetick](../../apps/donetick) | Acompanhe as tarefas de casa. |
| <img src="../../apps/dozzle/icon.svg" width="48" height="48" alt=""> | [Dozzle](../../apps/dozzle) | Leia os logs dos seus containers no navegador. |
| <img src="../../apps/excalidash/icon.svg" width="48" height="48" alt=""> | [ExcaliDash](../../apps/excalidash) | Um lugar para organizar e compartilhar desenhos do Excalidraw. |
| <img src="../../apps/faved/icon.svg" width="48" height="48" alt=""> | [Faved](../../apps/faved) | Um lugar simples para guardar favoritos. |
| <img src="../../apps/ferdium-server/icon.svg" width="48" height="48" alt=""> | [Ferdium Server](../../apps/ferdium-server) | Um servidor de sincronização para o app Ferdium. |
| <img src="../../apps/filebrowser/icon.svg" width="48" height="48" alt=""> | [FileBrowser Quantum](../../apps/filebrowser) | Um gerenciador de arquivos no navegador. |
| <img src="../../apps/fmd-server/icon.svg" width="48" height="48" alt=""> | [FMD Server](../../apps/fmd-server) | Encontre o seu celular Android pelo navegador. |
| <img src="../../apps/freshrss/icon.svg" width="48" height="48" alt=""> | [FreshRSS](../../apps/freshrss) | Leia todos os seus feeds de notícias num só lugar. |
| <img src="../../apps/frigate/icon.svg" width="48" height="48" alt=""> | [Frigate](../../apps/frigate) | Um gravador de câmeras de segurança que reconhece pessoas e objetos. |
| <img src="../../apps/ghost/icon.webp" width="48" height="48" alt=""> | [Ghost](../../apps/ghost) | Uma plataforma de blog e newsletter. |
| <img src="../../apps/gitea/icon.svg" width="48" height="48" alt=""> | [Gitea](../../apps/gitea) | Um servidor Git simples para o seu código. |
| <img src="../../apps/gitea-runner/icon.svg" width="48" height="48" alt=""> | [Gitea Runner](../../apps/gitea-runner) | Executa os fluxos automáticos do seu Gitea. |
| <img src="../../apps/grafana/icon.svg" width="48" height="48" alt=""> | [Grafana](../../apps/grafana) | Gráficos e painéis para os seus dados. |
| <img src="../../apps/headscale/icon.svg" width="48" height="48" alt=""> | [Headscale](../../apps/headscale) | O seu próprio servidor para uma rede privada. |
| <img src="../../apps/hermes-agent/icon.png" width="48" height="48" alt=""> | [Hermes Agent](../../apps/hermes-agent) | Um assistente de IA pessoal. |
| <img src="../../apps/home-assistant/icon.svg" width="48" height="48" alt=""> | [Home Assistant](../../apps/home-assistant) | Controle todos os seus dispositivos de casa inteligente num só lugar. |
| <img src="../../apps/homebox/icon.svg" width="48" height="48" alt=""> | [HomeBox](../../apps/homebox) | Mantenha um inventário de tudo o que você tem. |
| <img src="../../apps/homepage/icon.png" width="48" height="48" alt=""> | [homepage](../../apps/homepage) | Uma página inicial para o seu servidor doméstico. |
| <img src="../../apps/immich/icon.svg" width="48" height="48" alt=""> | [Immich](../../apps/immich) | Faça backup e navegue pelas suas fotos e vídeos. |
| <img src="../../apps/instagram-monitor/icon.svg" width="48" height="48" alt=""> | [Instagram Monitor](../../apps/instagram-monitor) | Acompanha perfis do Instagram e mostra a atividade deles. |
| <img src="../../apps/invio/icon.svg" width="48" height="48" alt=""> | [Invio](../../apps/invio) | Crie e acompanhe faturas. |
| <img src="../../apps/karakeep/icon.svg" width="48" height="48" alt=""> | [Karakeep](../../apps/karakeep) | Guarde e pesquise seus favoritos. |
| <img src="../../apps/karaoke-eternal/icon.svg" width="48" height="48" alt=""> | [Karaoke Eternal](../../apps/karaoke-eternal) | Faça festas de karaokê com as suas próprias músicas. |
| <img src="../../apps/kiwix/icon.svg" width="48" height="48" alt=""> | [Kiwix](../../apps/kiwix) | Leia a Wikipédia e outras bibliotecas sem internet. |
| <img src="../../apps/koffan/icon.png" width="48" height="48" alt=""> | [Koffan](../../apps/koffan) | Uma lista de compras compartilhada. |
| <img src="../../apps/komga/icon.svg" width="48" height="48" alt=""> | [Komga](../../apps/komga) | Leia seus quadrinhos e mangás. |
| <img src="../../apps/lubelogger/icon.png" width="48" height="48" alt=""> | [LubeLogger](../../apps/lubelogger) | Acompanhe a manutenção dos seus veículos. |
| <img src="../../apps/mailpit/icon.svg" width="48" height="48" alt=""> | [Mailpit](../../apps/mailpit) | Captura os e-mails que seus apps enviam para você lê-los. |
| <img src="../../apps/mdrop/icon.svg" width="48" height="48" alt=""> | [mdrop](../../apps/mdrop) | Transforme documentos em Markdown. |
| <img src="../../apps/media-stack/icon.svg" width="48" height="48" alt=""> | [Media Stack](../../apps/media-stack) | Um servidor de mídia e as ferramentas que o abastecem. |
| <img src="../../apps/memos/icon.svg" width="48" height="48" alt=""> | [Memos](../../apps/memos) | Um lugar simples para notas rápidas. |
| <img src="../../apps/metube/icon.svg" width="48" height="48" alt=""> | [MeTube](../../apps/metube) | Baixe vídeos da web. |
| <img src="../../apps/monica/icon.svg" width="48" height="48" alt=""> | [Monica](../../apps/monica) | Lembre das pessoas da sua vida. |
| <img src="../../apps/n8n/icon.svg" width="48" height="48" alt=""> | [n8n](../../apps/n8n) | Automatize tarefas entre os seus apps. |
| <img src="../../apps/neko/icon.svg" width="48" height="48" alt=""> | [neko](../../apps/neko) | Um navegador compartilhado para usar em conjunto. |
| <img src="../../apps/netbootxyz/icon.svg" width="48" height="48" alt=""> | [netboot.xyz](../../apps/netbootxyz) | Instale um sistema operacional pela rede. |
| <img src="../../apps/nginx/icon.svg" width="48" height="48" alt=""> | [nginx](../../apps/nginx) | Um servidor web para arquivos estáticos. |
| <img src="../../apps/node-red/icon.svg" width="48" height="48" alt=""> | [Node-RED](../../apps/node-red) | Automatize coisas ligando blocos. |
| <img src="../../apps/ntfy/icon.svg" width="48" height="48" alt=""> | [ntfy](../../apps/ntfy) | Envie notificações para o seu celular. |
| <img src="../../apps/omni-tools/icon.png" width="48" height="48" alt=""> | [Omni Tools](../../apps/omni-tools) | Ferramentas úteis que rodam no seu navegador. |
| <img src="../../apps/openwebui/icon.svg" width="48" height="48" alt=""> | [Open WebUI](../../apps/openwebui) | Uma interface de chat para modelos de IA. |
| <img src="../../apps/openwa/icon.svg" width="48" height="48" alt=""> | [OpenWA](../../apps/openwa) | Envie mensagens de WhatsApp a partir dos seus outros apps. |
| <img src="../../apps/owncloud/icon.svg" width="48" height="48" alt=""> | [ownCloud](../../apps/owncloud) | A sua própria nuvem de arquivos. |
| <img src="../../apps/owntracks/icon.svg" width="48" height="48" alt=""> | [OwnTracks](../../apps/owntracks) | Registre a sua localização pelo celular. |
| <img src="../../apps/paperless-ngx/icon.svg" width="48" height="48" alt=""> | [Paperless-ngx](../../apps/paperless-ngx) | Digitalize e pesquise os seus documentos de papel. |
| <img src="../../apps/pkvault/icon.svg" width="48" height="48" alt=""> | [PKVault](../../apps/pkvault) | Gerencie os seus arquivos de save de Pokémon. |
| <img src="../../apps/postfix/icon.svg" width="48" height="48" alt=""> | [Postfix](../../apps/postfix) | Envia e-mail em nome dos seus outros apps. |
| <img src="../../apps/postiz/icon.svg" width="48" height="48" alt=""> | [Postiz](../../apps/postiz) | Agende as suas publicações nas redes sociais. |
| <img src="../../apps/prometheus/icon.svg" width="48" height="48" alt=""> | [Prometheus](../../apps/prometheus) | Coleta números sobre como os seus serviços funcionam. |
| <img src="../../apps/proxmox/icon.svg" width="48" height="48" alt=""> | [Proxmox VE](../../apps/proxmox) | Experimente o sistema de virtualização Proxmox. |
| <img src="../../apps/radicale/icon.svg" width="48" height="48" alt=""> | [Radicale](../../apps/radicale) | Um servidor de calendários e contatos. |
| <img src="../../apps/rclone/icon.svg" width="48" height="48" alt=""> | [rclone](../../apps/rclone) | Mova arquivos entre as suas contas na nuvem. |
| <img src="../../apps/retrom/icon.webp" width="48" height="48" alt=""> | [Retrom](../../apps/retrom) | Uma biblioteca para os seus jogos retrô. |
| <img src="../../apps/searxng/icon.png" width="48" height="48" alt=""> | [SearXNG](../../apps/searxng) | Pesquise na web sem ser rastreado. |
| <img src="../../apps/stirling-pdf/icon.svg" width="48" height="48" alt=""> | [Stirling-PDF](../../apps/stirling-pdf) | Edite e converta arquivos PDF. |
| <img src="../../apps/syncthing/icon.svg" width="48" height="48" alt=""> | [Syncthing](../../apps/syncthing) | Sincronize arquivos entre os seus dispositivos. |
| <img src="../../apps/toolbx/icon.png" width="48" height="48" alt=""> | [Toolbx](../../apps/toolbx) | Shells Linux descartáveis para experimentar coisas. |
| <img src="../../apps/traccar/icon.svg" width="48" height="48" alt=""> | [Traccar](../../apps/traccar) | Rastreie veículos e dispositivos por GPS. |
| <img src="../../apps/tsdproxy/icon.svg" width="48" height="48" alt=""> | [tsdproxy](../../apps/tsdproxy) | Coloca os seus apps na sua tailnet automaticamente. |
| <img src="../../apps/uptime-kuma/icon.svg" width="48" height="48" alt=""> | [Uptime Kuma](../../apps/uptime-kuma) | Avisa quando um serviço cai. |
| <img src="../../apps/vaultwarden/icon.png" width="48" height="48" alt=""> | [Vaultwarden](../../apps/vaultwarden) | Um gerenciador de senhas que você hospeda. |
| <img src="../../apps/vaultzap/icon.svg" width="48" height="48" alt=""> | [VaultZap](../../apps/vaultzap) | Navegue pelas suas conversas exportadas do WhatsApp. |
| <img src="../../apps/vikunja/icon.svg" width="48" height="48" alt=""> | [Vikunja](../../apps/vikunja) | Uma lista de afazeres para tarefas e projetos. |
| <img src="../../apps/vm/icon.svg" width="48" height="48" alt=""> | [VM](../../apps/vm) | Rode Windows, macOS e Linux num container. |
| <img src="../../apps/wger/icon.svg" width="48" height="48" alt=""> | [wger](../../apps/wger) | Planeje e acompanhe os seus treinos. |
| <img src="../../apps/wud/icon.png" width="48" height="48" alt=""> | [WUD (What's Up Docker)](../../apps/wud) | Avisa quando os seus containers têm atualizações. |
| <img src="../../apps/zabbix/icon.svg" width="48" height="48" alt=""> | [Zabbix](../../apps/zabbix) | Monitora os seus servidores e a sua rede. |
| <img src="../../apps/zerobyte/icon.png" width="48" height="48" alt=""> | [Zerobyte](../../apps/zerobyte) | Faz backup dos dados dos seus apps. |
| <img src="../../apps/zigbee2mqtt/icon.svg" width="48" height="48" alt=""> | [Zigbee2MQTT](../../apps/zigbee2mqtt) | Use dispositivos Zigbee sem o hub do fabricante. |

<!-- services:end -->

**Nada atualiza sozinho.** Toda imagem é fixada — numa versão, ou num digest
onde o projeto não publica versão — e atualizada na mão; ver
[auto-update](./auto-update.md).

## A rede: Tailscale, Headscale ou só local

A tailnet faz parte do projeto, e uma escolha (perguntada pelo `bootstrap.sh`, trocada no painel em
**Configurações → Rede**, ou com `qh --network`) diz qual:

| Escolha | O que você tem |
| --- | --- |
| **Só local** | Sem tailnet. Os apps abrem na porta da LAN e o tsdproxy fica parado. O jeito mais simples. |
| **Tailscale** | O host entra numa tailnet do [Tailscale](https://tailscale.com) e o tsdproxy dá a cada serviço um nome HTTPS, acessível de qualquer lugar sem abrir porta. O Vaultwarden precisa dela: só decifra a sessão num contexto seguro. |
| **Headscale** | Uma rede sua, sem conta em terceiros: o projeto roda o [Headscale](https://headscale.net) (o app `headscale`), e o host e o tsdproxy entram nele. O Headscale não emite certificado HTTPS, então os apps ficam em HTTP na tailnet (o WireGuard ainda a cifra) e os que exigem HTTPS (Vaultwarden, Actual) precisam da escolha Tailscale. |

```bash
qh --network                                   # onde as coisas estão
qh --network local --apply
qh --network tailscale --apply
qh --network headscale --tailnet <your-tailnet> --apply     # --login-server URL se não for o endereço da LAN
```

O que pede root no host só é mostrado, nunca executado: o Tailscale é pacote do host (ele precisa *ser* o host na
rede), então o plano imprime o que falta, uma vez —

```bash
sudo transactional-update pkg install tailscale     # host imutável; depois reinicie
sudo systemctl enable --now tailscaled
sudo tailscale set --operator=$USER                  # deixa o painel fazer o login do host, sem root
```

— e todo o resto (o login, o servidor Headscale, o usuário e a chave dele, o secret e o `controlUrl` do tsdproxy, o
`TAILNET` das units, a atualização dos apps) são os passos do plano. Com o Tailscale, o tsdproxy pede uma chave
reutilizável do console de admin; com o Headscale, o projeto a cria. Trocar muda a label da porta proxiada dos apps
(uma atualização, que mantém os dados) e é reversível: `--network local` e depois `--network tailscale` é o caminho
de volta.

Sem tailnet, `qh --network local` grava a regra e para o tsdproxy; a regra de mais baixo nível sozinha continua
sendo `qh --set-access local`, que comenta as labels `tsdproxy.*` em vez de apagá-las.

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

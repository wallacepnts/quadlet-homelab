# Endurecimento, o que foi medido

**[🇬🇧 Read in English](../hardening.md)**

O que cada imagem de fato aceitou, container por container. A regra 20 das
[convenções](./convencoes.md) manda nunca copiar o bloco de hardening de outro
serviço às cegas — o que uma imagem tolera só se descobre testando. É aqui que
esses testes ficam guardados, para a próxima pessoa não pagar por eles de novo.

A primeira tabela é gerada a partir das units, e o [`check.py`](../../check.py)
a confere: linha que deixa de bater com seu `.container` reprova. O resto é
conhecimento que nenhum arquivo responde — uma mensagem de erro, um uid, um
motivo — e se mantém na mão.

## Estado medido

| Container | `ReadOnly` | Capabilities |
| --- | --- | --- |
| `actual` | yes | **none** + `User=1000` |
| `adguardhome` | yes | 1 (`net_bind_service`) |
| `anki` | yes | **none** + `User=65532` |
| `any-sync-bundle` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `audiobookshelf` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `authentik` | yes | **none** + `User=1000` |
| `authentik-postgres` | yes | **none** + `User=70` |
| `authentik-worker` | yes | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) + `User=0` |
| `beaverhabits` | yes | **none** + `User=1000` |
| `beszel` | yes | **none** |
| `beszel-agent` | no | podman default |
| `calibre-web-automated` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `changedetection` | yes | **none** + `User=1000` |
| `collabora` | no | 1 (`sys_chroot`) |
| `cookcli` | yes | **none** + `UserNS=keep-id` |
| `copyparty` | yes | **none** + `User=1000` |
| `docuseal` | yes | **none** + `User=1000` |
| `donetick` | yes | **none** + `User=1000` |
| `dozzle` | yes | **none** + `User=1000` |
| `excalidash` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `excalidash-backend` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `faved` | yes | 1 (`net_bind_service`) + `User=33` |
| `ferdium-server` | no | **none** |
| `filebrowser` | yes | **none** + `UserNS=keep-id` |
| `fmd-server` | yes | **none** + `User=1000` |
| `freshrss` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `frigate` | no | podman default |
| `ghost` | yes | **none** + `User=1000` |
| `gitea` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `gitea-runner` | yes | **none** |
| `grafana` | yes | **none** + `User=472` |
| `hermes-agent` | no | podman default |
| `home-assistant` | yes | **none** |
| `homebox` | yes | **none** + `User=1000` |
| `homepage` | yes | **none** |
| `immich` | yes | **none** + `UserNS=keep-id` |
| `immich-machine-learning` | yes | **none** + `UserNS=keep-id` |
| `immich-postgres` | no | **none** + `User=999` |
| `immich-redis` | yes | **none** + `UserNS=keep-id` |
| `invio` | no | **none** |
| `karakeep` | yes | **none** |
| `karakeep-chrome` | yes | **none** |
| `karakeep-meilisearch` | yes | **none** |
| `karaoke-eternal` | yes | **none** + `User=1000` |
| `kiwix` | yes | **none** + `User=1001` |
| `koffan` | yes | **none** + `User=1000` |
| `komga` | yes | **none** + `User=1000` |
| `lubelogger` | no | **none** |
| `mailpit` | yes | **none** + `User=1000` |
| `mdrop` | yes | **none** |
| `media-stack-bazarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-deluge` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-dispatcharr` | no | podman default |
| `media-stack-downtify` | no | podman default |
| `media-stack-gluetun` | no | podman default |
| `media-stack-jellyfin` | no | podman default + `UserNS=keep-id` |
| `media-stack-lidarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-navidrome` | yes | **none** + `User=1000` |
| `media-stack-prowlarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-radarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-sabnzbd` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-seerr` | yes | **none** + `UserNS=keep-id` |
| `media-stack-sonarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `memos` | yes | **none** + `User=1000` |
| `metube` | yes | **none** + `User=1000` |
| `monica` | no | podman default |
| `n8n` | no | **none** + `UserNS=keep-id` |
| `neko` | no | 3 (`chown`, `setgid`, `setuid`) |
| `netbootxyz` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `nginx` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `node-red` | no | **none** + `UserNS=keep-id` |
| `ntfy` | yes | **none** + `User=1000` |
| `omni-tools` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `openwa` | yes | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `openwebui` | no | **none** |
| `openwebui-ollama` | no | **none** |
| `owncloud` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `owntracks-frontend` | no | podman default |
| `owntracks-mosquitto` | yes | **none** + `User=1883` |
| `owntracks-recorder` | no | podman default |
| `paperless-ngx` | yes | **none** |
| `paperless-ngx-broker` | yes | **none** + `User=999` |
| `paperless-ngx-gotenberg` | yes | **none** |
| `paperless-ngx-tika` | yes | **none** |
| `pkvault` | yes | 4 (`chown`, `dac_override`, `setgid`, `setuid`) |
| `postfix` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `postiz` | yes | **none** + `User=33` |
| `postiz-postgres` | yes | **none** + `User=70` |
| `postiz-redis` | yes | **none** + `User=999` |
| `postiz-temporal` | no | **none** |
| `postiz-temporal-postgres` | yes | **none** + `User=999` |
| `prometheus` | yes | **none** + `User=65534` |
| `proxmox` | no | podman default |
| `radicale` | yes | 4 (`chown`, `kill`, `setgid`, `setuid`) |
| `retrom` | no | 3 (`chown`, `setgid`, `setuid`) |
| `searxng` | yes | **none** + `User=977` |
| `stirling-pdf` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `syncthing` | yes | **none** + `User=1000` |
| `toolbx-arch` | no | podman default + `UserNS=keep-id` |
| `toolbx-fedora` | no | podman default + `UserNS=keep-id` |
| `toolbx-rhel` | no | podman default + `UserNS=keep-id` |
| `toolbx-ubuntu` | no | podman default + `UserNS=keep-id` |
| `traccar` | yes | **none** + `User=1000` |
| `tsdproxy` | no | **none** |
| `uptime-kuma` | yes | **none** + `User=1000` |
| `vaultwarden` | yes | 1 (`net_bind_service`) |
| `vaultzap` | yes | **none** + `UserNS=keep-id:uid=65532,gid=65532` |
| `vikunja` | yes | **none** + `User=1000` |
| `vm-chromeos` | no | podman default + 1 add |
| `vm-macos` | no | podman default + 1 add |
| `vm-qemu` | no | podman default + 1 add |
| `vm-windows` | no | podman default + 1 add |
| `vm-windows-arm` | no | podman default + 1 add |
| `vm-zima` | no | podman default + 1 add |
| `wger` | yes | **none** |
| `wud` | yes | **none** |
| `zerobyte` | yes | 1 (`dac_read_search`) |
| `zigbee2mqtt` | yes | **none** |
| `zigbee2mqtt-mosquitto` | yes | **none** + `User=1883` |

## Zero capabilities: quem aceitou, quem recusou

O `DropCapability=ALL` é o passo mais barato e a maioria das imagens aceita.
Estas são as que não aceitaram, e onde o entrypoint insiste em escrever.

| Aceitou (foi a zero capabilities) | Recusou, e onde o entrypoint escreve |
| --- | --- |
| memos, syncthing | nginx, omni-tools → `/etc/nginx/conf.d/default.conf` |
| | netbootxyz → `/var/lib/nginx/logs` |
| | owncloud → `/var/www/owncloud/custom` |
| | stirling-pdf → `/tmp/stirling-pdf` |
| | freshrss → `/etc/localtime` |
| | gitea, calibre-web-automated → o lock do s6-overlay |
| | audiobookshelf, any-sync-bundle → uma exceção no start |

## De quem os arquivos ficam no host

`UserNS=keep-id` não é hardening — só decide quem é dono dos arquivos num bind
mount. `User=` é, e muda a resposta:

| config | uid no host |
| --- | --- |
| default | 1000 (você) |
| `UserNS=keep-id` | 1000 (você) |
| `User=1000` | **100999** |

## Recusas registradas

O erro que apareceu, para não se repetir a tentativa. Esta é a metade que não se
gera: container que sobe e responde prova que o hardening funciona, e só a
mensagem prova por que ele não vai além.

| Container | Ajuste | O que aconteceu |
| --- | --- | --- |
| `ferdium-server` | `ReadOnly=true` | o entrypoint faz `git clone` das receitas e escreve `/home/node/.gitconfig` |
| `ferdium-server` | `User=1000` | `EACCES: mkdir '/usr/local/lib/node_modules/pnpm'` — instala o pnpm global a cada start |
| `filebrowser` | sem `UserNS=keep-id` | `could not open database: open /home/filebrowser/data/database.db: permission denied` |
| `filebrowser` | porta interna 80 | `Server error: listen tcp 0.0.0.0:80: bind: permission denied` sob keep-id |
| `filebrowser` | `ReadOnly=true` com o `cacheDir` padrão | `cacheDir failed to create cache directory: mkdir tmp: read-only file system` — resolvido apontando o `cacheDir` pro volume |
| `authentik-worker` | `DropCapability=ALL` sem nada adicionado | `chown: /data`, depois `chmod: /data`, depois `setpriv: setresuid failed` — o entrypoint ajusta os volumes como root e desce para o usuário do authentik, então precisa de cinco. O papel de **servidor** da mesma imagem não precisa de nenhuma, porque o `User=1000` faz o entrypoint pular esse trecho; o worker é `User=0` porque o socket do podman que ele monta pertence ao usuário do host, que mapeia para 0 |
| `vaultzap` | `Secret=` com `type=mount` | `make mountpoint: read-only file system` — usar `type=env`. Não é regra geral: no mesmo Podman 6.0.2, o `owntracks-mosquitto` monta um secret `type=mount` sob `ReadOnly=true`, com e sem `UserNS=keep-id` |
| `proxmox` | sem `--privileged` | `ERROR: Please start the container with the --privileged flag!` |
| `toolbx` | instalar pacote com `UserNS=keep-id` | negado; usar `podman exec --user root` |
| `pkvault` | `DropCapability=ALL` sozinho | o container fica `Up` com o app morto: o supervisord segue rodando enquanto o nginx sai com `mkdir() "/var/lib/nginx/tmp/client_body" failed (13: Permission denied)` — o nginx roda como root sobre uma pasta do usuário `nginx`. Sem `CHOWN`: `chown("/var/lib/nginx/tmp/client_body", 100) failed`; sem `DAC_OVERRIDE`: o mesmo `mkdir` |
| `pkvault` | `Tmpfs=/var/lib/nginx/tmp` sem `mode=1777` | enviar um save responde 500: `open() "/var/lib/nginx/tmp/client_body/0000000001" failed (13: Permission denied)` — o nginx guarda ali todo corpo acima de 16 KB, e o tmpfs nasce com dono root. O `--tmpfs` do podman não tem `uid=`; as subpastas que o nginx cria dentro continuam `0700 nginx` |
| `pkvault` | `User=100` | `Error: Can't drop privilege as nonroot user` — o `supervisord.conf` da imagem declara `user=root` |
| `postiz-temporal` | `ReadOnly=true` | `unable to create open /etc/temporal/config/docker.yaml: read-only file system` — o entrypoint renderiza a configuração ali a cada start |
| `postiz` | `DropCapability=ALL` sendo root | o container fica `Up` com o app morto: o nginx sai com `mkdir() "/var/lib/nginx/body" failed (13: Permission denied)`. Como root precisa de quatro para rodar o nginx, e cada falta falha de um jeito: sem `CHOWN` → `chown("/var/lib/nginx/body", 100) failed (1)`; sem `DAC_OVERRIDE` → o mesmo `mkdir`; sem `SETGID` ou `SETUID` → `worker process exited with fatal code 2`. O `User=33` não precisa de nenhuma |
| `postiz` | `User=1000` | `open() "/var/log/nginx/access.log" failed (13: Permission denied)` — um tmpfs sobre `/var/log/nginx` recebe uma cópia do `access.log` da imagem, do `www-data` com modo 0640. Use `User=33` |
| `postiz` | `HOME=/root` sem ser root | `EACCES: permission denied, mkdir '/root/.pm2/logs'` — `/root` é 0700, então nenhum tmpfs dentro dele é alcançável. A unit aponta o `HOME` para um tmpfs próprio |
| `postiz` | `ReadOnly=true` com `/root/.cache` em volume | o backend às vezes nunca abre a porta 3000, sem erro em log nenhum: 2 de 9 partidas, contra 0 de 18 com o cache em tmpfs no laboratório — e 1 de 4 na unit instalada, que tem o tmpfs, então não é a causa inteira. `pm2 restart backend` o levanta. O cache tem 244 MB, que o `pnpm dlx prisma` baixa a cada start |
| `postiz` | `PidsLimit=256` | o padrão do repositório é apertado demais aqui: 197 em repouso, pico de 202. A unit usa 512 |
| `postfix` | `ReadOnly=true` | sai com 1 — o `run.sh` reescreve `/etc/postfix/main.cf` a cada start |
| `postfix` | `User=1000` | `chmod: changing permissions of '/scripts/common.sh': Operation not permitted` |
| `postfix` | `DropCapability=ALL` sozinho | container fica `Up` com o app morto: `chown: /var/spool/postfix/private: Operation not permitted` |
| `tsdproxy` | ícone com gradiente no `dash.icon` | o tsdproxy injeta `fill="currentColor"` na raiz do SVG; path sem `fill` próprio vira bloco sólido. Usar monocromático (`si/`, `mdi/`, ou a variante `-light`/`-dark` do selfh.st) |
| immich (os três) | `--cap-drop=NET_RAW` | não faz nada: rootless, o `podman info` declara 11 capabilities padrão e `NET_RAW` não é uma delas. Medido: o `CapEff` fica idêntico com e sem a flag. Só as três units do immich tentavam isso, em 110 |
| quem monta `podman.sock` | só `:z` | sob SELinux o processo fica `container_t` e a API recusa: `permission denied while trying to connect to the docker API`. O serviço sobe **healthy** e não enxerga container nenhum. Usar `SecurityLabelType=container_runtime_t`, não `SecurityLabelDisable` — são seis units: authentik-worker, beszel-agent, dozzle, homepage, tsdproxy, wud |
| `collabora` | `ReadOnly=true` | `Access to file denied: /opt/cool/child-roots/...` — o tmpfs nasce do root e o coolwsd roda como uid 1001 |
| `collabora` | `DropCapability=ALL` sozinho | `chroot(...) failed (EPERM)` — cada documento roda numa jaula própria |
| `retrom` | `ReadOnly=true` | panic em `packages/telemetry/src/lib.rs:48` — o entrypoint chowna os três volumes a cada start |
| `excalidash-backend` | `User=1000` | `Can't write to /app/node_modules/prisma` — o Prisma escreve dentro da imagem |
| `excalidash-backend` | `ReadOnly=true` | `EROFS: read-only file system, utime '/root/.cache/prisma/...'` |
| `excalidash` | `ReadOnly=true` | o entrypoint gera o `/etc/nginx/nginx.conf` a partir do template a cada start |
| `neko` | `ReadOnly=true` | sobe mas não serve: o supervisord escreve o socket em `/var/run` |
| media-stack | um job de backup por unit | o gancho para a stack pelo prefixo (`media-stack-*`), numa chamada só; parar doze leva mais que os 60s padrão, daí o `WEBHOOK_TIMEOUT=180` |
| `vm-windows` | `DISK_TYPE=sata` no Windows XP | ignorado — `writeState "type" "blk"` é fixo para `winxpx*`, e não existe driver virtio para XP |

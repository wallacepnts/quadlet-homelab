# Collabora Online

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/collabora-online.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

O LibreOffice desenhado no navegador, editando os arquivos que já estão no
[ownCloud](../owncloud/README.pt-BR.md). Documento, planilha e slides abrem no
lugar, e o arquivo não sai de casa.

Sozinho ele não serve para nada: todo documento que ele abre é o ownCloud que
entrega. Instale aquele primeiro.

## Instalação

```bash
qh collabora            # mostra o plano
qh collabora --apply
```

Depois, no `~/.config/containers/env/collabora.env`, ponha o endereço do seu
ownCloud no `aliasgroup1` e reinicie com `qh collabora --update --apply`. Do
lado do ownCloud, uma vez:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/collabora/collabora.container
wget -O ~/.config/containers/env/collabora.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/collabora/.env.example
# editar ~/.config/containers/env/collabora.env: aliasgroup1

systemctl --user daemon-reload
systemctl --user start collabora
```

</details>

## Arquivos

```
collabora.container   unit
.env.example          ambiente
install.ini
```

Sem volume: ele não guarda nada. Todo documento vive no ownCloud e é buscado a
cada edição, então não há o que copiar em backup nem o que perder num
`--purge`.

## As duas pontas da ligação

Elas precisam concordar, e cada uma falha de um jeito quando não concordam:

- **`aliasgroup1`**, aqui, é quem pode embutir o editor — é expressão regular,
  então os pontos vão escapados:
  `https://owncloud\.<your-tailnet>\.ts\.net:443`. Host fora da lista recebe
  `unauthorized WOPI host`, o que no ownCloud aparece como documento que roda
  para sempre sem abrir.
- **`wopi_url`**, no ownCloud, é de onde o navegador carrega o editor. Tem que
  ser o endereço que o **seu navegador** alcança, não um nome de container — a
  página é desenhada na sua máquina.

Servidor a servidor eles conversam pela `tsdproxy-net` pelo nome, que é como o
ownCloud lê `http://collabora:9980/hosting/discovery` sem porta publicada.

O `extra_params=--o:ssl.enable=false --o:ssl.termination=true` não é opcional
atrás do tsdproxy: sem a segunda flag o Collabora monta as URLs dele como
`http://` e o navegador bloqueia como conteúdo misto; sem a primeira ele serve
TLS por conta própria, com um certificado que ninguém confia.

## Endurecimento

Uma capacidade, a `SYS_CHROOT`. O Collabora roda cada documento numa jaula
chroot própria, e com tudo descartado o processo morre no start:

```
FTL  chroot("/opt/cool/child-roots/...") failed (EPERM: Operation not permitted)
```

O `ReadOnly=true` foi tentado e recusado — `Access to file denied:
/opt/cool/child-roots/...`, porque um tmpfs naquele caminho nasce do root
enquanto o coolwsd roda como uid 1001, que a própria imagem já define.

Não há `HealthCmd`, e por isso não há `Notify=healthy`: a imagem não tem shell
nem `curl` ou `wget` — `coolwsd`, `coolmount`, `coolforkit` e `openssl` são
todo o `/usr/bin`, então não há o que rodar dentro dela.

## Atualizar

```bash
qh collabora --update --apply
```

Fixado em `26.04.3.1.1`. O Collabora não publica release no GitHub, então o
`qh-updates` compara com a lista de tags do registry.

## Backup

Não há o que copiar — veja [Arquivos](#arquivos). Os documentos são do
ownCloud, e o `qh owncloud --backup` cobre eles.

## Remover

```bash
qh collabora --remove --apply           # para e tira a unit
qh collabora --remove --purge --apply   # e apaga o .env
```

Desligue também do lado do ownCloud, senão o menu de arquivo segue oferecendo
um editor que não existe mais:

```bash
podman exec owncloud occ app:disable richdocuments
```

## Comandos

```bash
systemctl --user status collabora
podman logs -f collabora

# o que o ownCloud pede
podman exec owncloud curl -s http://collabora:9980/hosting/discovery | head -20
```

## Créditos

[CollaboraOnline/online](https://github.com/CollaboraOnline/online) —
MPL-2.0. A imagem é a CODE, a Collabora Online Development Edition.

[Documentação oficial](https://sdk.collaboraonline.com/docs/installation/)

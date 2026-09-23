# FMD Server

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/fmd.svg" width="64" height="64" alt="">

**[🇬🇧 Read in English](./README.md)**

A metade servidor do [FMD](https://fmd-foss.org) — localizar, tocar, bloquear ou
apagar seu celular Android pelo navegador, sem o Encontre Meu Dispositivo do
Google. O celular roda o app FMD (no F-Droid); é aqui que ele reporta.

Localizações e fotos são **criptografadas no celular** antes de sair: o servidor
guarda texto cifrado e não consegue lê-lo. O outro lado disso é que esquecer a
senha da conta perde os dados — não há nada aqui com que recuperá-los.

## Instalação

```bash
qh fmd-server            # mostra o plano
qh fmd-server --apply
```

A instalação termina imprimindo o **token de registro**. Digite-o no app FMD
quando apontá-lo para `https://fmd.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
# 1. Baixe a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/fmd-server/fmd-server.container

# 2. A pasta do banco. A imagem roda como uid 1000, e o container não pode mais
#    fazer chown sozinho.
mkdir -p ~/.config/containers/volumes/fmd-server/db
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/fmd-server/db

# 3. O token de registro — sem ele, qualquer um que alcance o servidor abre
#    conta nele
mkdir -p ~/.config/containers/secrets/fmd-server
python3 -c 'import secrets; print(secrets.token_urlsafe(32), end="")' \
  > ~/.config/containers/secrets/fmd-server/registration-token.txt
chmod 600 ~/.config/containers/secrets/fmd-server/registration-token.txt
podman secret create fmd-server-registration-token \
  ~/.config/containers/secrets/fmd-server/registration-token.txt
cat ~/.config/containers/secrets/fmd-server/registration-token.txt; echo   # para o app

systemctl --user daemon-reload
systemctl --user start fmd-server
```

</details>

## Arquivos

```
fmd-server.container
install.ini
```

## Como se chega nele — e como o celular chega nele

**O FMD Server precisa ser servido por HTTPS**: a interface web não funciona em
HTTP puro. Na tailnet, o tsdproxy resolve isso. A porta `8124` na LAN é HTTP
puro, então escolher acesso só pela LAN na instalação deixa a interface web
inutilizável.

A parte fácil de esquecer: o **celular** reporta para
`fmd.<your-tailnet>.ts.net`, que só resolve com o app do Tailscale rodando no
celular. Deixe o Tailscale sempre ligado lá — um celular perdido com o Tailscale
desligado não reporta nada, por melhor que este lado esteja. O app FMD também
aceita comandos por SMS, que não dependem deste servidor.

## O token de registro

O FMD Server só confere o token quando há um definido, e esta unit sempre
define. Medido na 0.17.0: com `FMD_REGISTRATIONTOKEN` ausente, um registro com
token errado é aceito; com ele definido, o mesmo pedido responde
`401 Registration Token not valid`. O token só importa para **criar** contas —
uma conta existente entra com a própria senha.

## Atualizar

```bash
qh fmd-server --update --apply
```

Fixado em `0.17.0-alpine`. Nada atualiza sozinho.

O projeto é **pré-1.0, e avisa que versões minor podem quebrar** — leia as notas
da release antes de ir da 0.17 para a 0.18, e faça backup antes. Ele vive no
GitLab, então o `install.ini` compara com o registry de lá em vez de uma
página de releases do GitHub.

A variante `-alpine`, e não a Debian padrão nem a distroless menor, porque é a
que traz `wget` — de que o `HealthCmd` precisa, e o `Notify=healthy` precisa
do `HealthCmd` (regra 14 das convenções).

## Backup

```bash
qh fmd-server --backup --apply --out ~/backups
```

O volume guarda um banco SQLite. É texto cifrado, então o backup só serve junto
com as senhas das contas.

## Remover

```bash
qh fmd-server --remove --apply           # para, mantém os dados
qh fmd-server --remove --purge --apply   # e apaga o volume e o secret
```

O nó da tailnet não é desregistrado por isso — isso se faz no admin do Tailscale.

## Comandos

```bash
systemctl --user status fmd-server
podman logs -f fmd-server
podman exec fmd-server /opt/fmd-server-ctl listusers   # contas neste servidor
```

A CLI de administração acha o banco pelo `FMD_DATABASEDIR`, que a unit define. O
flag `--db-dir` dela aparece na ajuda geral mas não é aceito pelos
subcomandos, e sem a variável ela procura em `./db/` e tenta criar um banco
vazio ali — é a raiz somente-leitura que impede.

## Créditos

[fmd-foss/fmd-server](https://gitlab.com/fmd-foss/fmd-server) — GPL-3.0-or-later

[Documentação oficial](https://fmd-foss.org/docs/fmd-server/overview)

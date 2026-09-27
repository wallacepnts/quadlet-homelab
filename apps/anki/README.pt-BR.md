# Anki

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/anki.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

O servidor de sincronização que vem com o próprio [Anki](https://apps.ankiweb.net),
rodando aqui no lugar do AnkiWeb. Baralhos, histórico de revisão e mídia
sincronizam entre o Anki no computador, o AnkiDroid e o AnkiMobile pela sua
própria máquina.

## Instalação

```bash
qh anki            # mostra o plano
qh anki --apply
```

A instalação exibe o usuário e a senha no final. Depois, em cada cliente, aponte
a sincronização para `https://anki.<your-tailnet>.ts.net/` e entre com eles:

- **Anki (computador)**: Preferências → Sincronização → *Servidor de sincronização próprio*.
- **AnkiDroid**: Configurações → Sincronização → *Servidor de sincronização personalizado*.
- **AnkiMobile**: Settings → Syncing → *Custom server*.

A primeira sincronização depois de trocar de servidor é completa: envie a partir
do aparelho que tem a coleção que você quer manter e baixe nos outros.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
# 1. Baixar a unit (não precisa clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/anki/anki.container

# 2. A pasta de dados. A unit roda como uid 65532, o usuário nonroot do distroless.
mkdir -p ~/.config/containers/volumes/anki/data
podman unshare chown -R 65532:65532 ~/.config/containers/volumes/anki/data

# 3. A conta, como `usuário:senha`, o formato que o servidor lê
printf 'anki:%s' "$(openssl rand -hex 16)" | podman secret create anki-user -
podman secret inspect anki-user --showsecret --format '{{.SecretData}}'; echo

systemctl --user daemon-reload
systemctl --user start anki
```

</details>

## Arquivos

```
anki.container   unit
install.ini      a receita do segredo e de onde vêm as atualizações
```

Dados em `~/.config/containers/volumes/anki/data`, uma pasta por usuário. Porta
**8125** na LAN.

## Acesso

**Não há página web.** Aberto no navegador, o endereço mostra um `404 Not Found`
vazio — é o servidor funcionando; ele só responde aos apps do Anki, em `/sync/`.
Para ver que funciona, sincronize a partir de um cliente.

O servidor fala só **HTTP puro**. Na tailnet, o tsdproxy põe HTTPS na frente, e
é esse o endereço para dar aos clientes: **o AnkiMobile recusa servidor sem
TLS**, e uma senha enviada por HTTP puro atravessa a rede legível. A porta
`8125` na LAN serve para um cliente de computador na mesma rede, se você quiser.

O celular só alcança `anki.<your-tailnet>.ts.net` enquanto o Tailscale estiver
rodando nele. No iOS, o AnkiMobile também precisa da permissão de *Rede Local*
para chegar a um servidor da sua própria rede.

O `SYNC_HOST=0.0.0.0` está na unit porque o servidor escuta em `localhost` por
padrão, o que dentro de um container fica inalcançável de fora dele.

## Mais de um usuário

Cada conta é uma variável `SYNC_USERn` (`SYNC_USER1`, `SYNC_USER2`, …), cada uma
com a sua coleção. A instalação cria uma. Para uma segunda pessoa:

```bash
printf 'maria:%s' "$(openssl rand -hex 16)" | podman secret create anki-user2 -
```

e acrescente `Secret=anki-user2,type=env,target=SYNC_USER2` à unit. O `qh anki
--update` mostra edições locais na unit antes de sobrescrevê-las.

## Atualizar

```bash
qh anki --update --apply
```

Fixado em `26.08-distroless`. Nada atualiza sozinho.

**Não existe imagem oficial.** O repositório do Anki traz o Dockerfile, mas não
publica imagem; esta é construída a partir desse Dockerfile pelo autor dele, no
ritmo dele — da 25.07 para a 26.05 foram dez meses, e a imagem fica atrás das
versões do Anki. Isso não atrapalha: o protocolo de sincronização é estável
entre versões, e um cliente 26.09 foi medido sincronizando contra este servidor
26.08. O `install.ini` compara com o registry, não com a página de releases do Anki.

A variante distroless, não a Alpine, porque o entrypoint da Alpine faz `chown`
dos dados e troca de usuário com `su-exec` — o que exige root e capabilities. A
distroless não tem entrypoint, então roda sem privilégio desde o início.

## Endurecimento

Tudo, medido na `26.08-distroless`: raiz somente leitura sem `/tmp` (um arquivo
de mídia de 3 MB sincronizou sem ele), nenhuma capability, `User=65532`. Testado
com um cliente de verdade — login, senha errada recusada, uma nota e um arquivo
de mídia enviados de uma coleção e baixados em outra.

`StopSignal=SIGINT` porque o servidor não trata SIGTERM, o sinal padrão do
podman: todo stop e restart esperava os 10 segundos até o SIGKILL. Com SIGINT ele
sai limpo, com código 0.

## Backup

```bash
qh anki --backup --apply --out ~/backups
```

O volume guarda a coleção e a mídia de cada usuário, em arquivos SQLite e uma
pasta. Os clientes também têm a própria cópia, então um servidor perdido se
recupera com um envio completo a partir de qualquer um deles.

## Remover

```bash
qh anki --remove --apply           # para, mantém os dados
qh anki --remove --purge --apply   # e apaga o volume e o segredo
```

O nó da tailnet não é removido por aqui — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status anki
podman logs -f anki
podman exec anki anki-sync-server --healthcheck; echo $?
```

## Créditos

[ankitects/anki](https://github.com/ankitects/anki) — AGPL-3.0-or-later.
A imagem, [jeankhawand/anki-sync-server](https://hub.docker.com/r/jeankhawand/anki-sync-server),
é construída a partir do Dockerfile em `docs/syncserver` do Anki, mantido por Jean Khawand.

[Documentação oficial](https://docs.ankiweb.net/sync-server.html)

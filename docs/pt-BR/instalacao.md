# Instalando e operando

Tudo pelo `qh`. Todo modo é **dry-run por padrão**; `--apply` executa.

```bash
qh                                    # os serviços
qh traccar                            # mostra o que faria
qh traccar --apply
qh traccar --update --apply           # recopia as units, reinicia, mantém dados
qh traccar --reinstall --apply        # sobrescreve env, config e secrets
qh traccar --remove --apply           # para e tira, mantendo os dados
qh traccar --remove --purge --apply   # + apaga volumes, secrets e env
qh traccar --backup --apply --out ~/backups
qh traccar --restore ~/backups/traccar-....tar.gz --apply
```

Vários de uma vez, ou `--all` pra todos:

```bash
qh memos ntfy homebox --apply
qh --all --update --apply
```

Uma unit só de uma stack — nomear a unit em vez da pasta:

```bash
qh media-stack-jellyfin --apply
qh immich-postgres --update --apply
```

Vale pra instalação, `--reinstall` e `--update`. O `--backup`, o `--restore` e
o `--remove` agem sobre os dados da pasta inteira, então pedem o nome da pasta.

## O que cada modo faz

**`--update`** é o de toda semana: bump de versão no repositório não muda o
arquivo já instalado no host, e é isso que ele resolve. Não toca em volume,
`.env` nem secret. Tag móvel (`latest`) é sempre puxada; tag fixa só quando o
host não a tem.

**Instalação simples sobre serviço instalado recusa** e mostra os dois
caminhos:

```
filebrowser: já instalado — 1/1 unit(s) em ~/.config/containers/systemd
  --update     recopia as units e reinicia, mantendo dados, env e secrets
  --reinstall  instala de novo, SOBRESCREVENDO env, config e secrets
```

**Depois de um `--remove`**, instalar de novo encontra o `.env`, a config e os
secrets no lugar e mantém, com aviso. O `--reinstall` sobrescreve.

**O `--backup` para o serviço** antes de empacotar e sobe de novo. O `.tar.gz`
leva os volumes, os secrets e o `.env` — os dois últimos são minúsculos e são o
que torna o backup restaurável.

**O `--restore` é troca, não mistura.** Ele apaga a raiz do volume antes de
extrair, confere se o arquivo é daquele serviço, e pede o nome digitado pra
confirmar.

## O que foi feito

Com `--apply`, a execução termina com o que de fato rodou:

```
feito: 3 instalações
  7 diretórios, 6 units e arquivos copiados, 3 volumes com dono ajustado,
  3 imagens baixadas, 3 serviços reiniciados, 1 secret criado
```

Com um serviço, a lista de passos acima já é o resumo; com `--all` ela tem
trezentas linhas e a pergunta que sobra é o que mudou.

## Estado

```bash
qh --status
```

```
service                    unit       container  repo
adguardhome                failed     —          changed
filebrowser                active     healthy    changed
memos                      active     healthy    —
```

O `unit` é o que o systemd diz, o `container` é o que o podman diz — uma unit
pode estar `active` com o app morto lá dentro, então não são a mesma pergunta.
O `repo` avisa que o arquivo aqui difere do instalado, que é o que o `--update`
resolve. Versão não está aqui: isso exige rede, e é o que o `qh-updates` faz.
Sai com código diferente de zero quando há algo precisando de atenção.

## A regra de acesso

Escolhida uma vez, seguida por toda instalação e atualização:

```bash
qh --set-access tailnet     # local | tailnet | both
qh                          # mostra a regra em vigor
```

| regra | tsdproxy | porta na LAN |
| --- | --- | --- |
| `local` | labels comentados | aberta |
| `tailnet` | ligado | **fechada** |
| `both` | ligado | aberta |


O `qh` informa quantos serviços instalados não a seguem, e o comando que os
alinha — regra que só valesse pra próxima instalação seria meia regra.

O bootstrap pergunta no primeiro uso. Enquanto não houver regra, o padrão é
`tailnet`. Nomear o `--access` num comando vence a regra só naquele comando, e
não muda nada do que está salvo.

## Acesso

```bash
qh traccar --apply --access local     # sem tsdproxy, link do dashboard pra LAN
qh traccar --apply --access tailnet   # padrão
qh traccar --apply --access both
qh traccar --apply --href-local       # na tailnet, link do dashboard pra LAN
```

O `--local` é atalho pra `--access local`. As labels `tsdproxy.*` são
comentadas em vez de apagadas, então mudar de ideia depois é um `--update` com
outro modo — não um `--reinstall`, que sobrescreveria env, config e secrets pra
trocar uma label.

O `--access tailnet` também **fecha a porta na LAN**. O serviço entra na rede
`tsdproxy-net` e o tsdproxy o alcança no endereço do próprio container, então
nada dele fica aberto no host. Só a porta que o tsdproxy faz proxy é fechada:
unit que também publica DNS, MQTT ou porta de torrent mantém essas em todo
modo, porque dispositivos falam com elas direto.

Uma atualização mantém o modo que o host já tem, então serviço instalado com
`--local` não volta calado pra tailnet no próximo bump. Nomear o `--access`
numa atualização muda isso:

```bash
qh memos --update --apply --access tailnet    # e fecha a porta dele na LAN
```

## Credenciais

Quando o serviço tem login, a instalação termina com ele:

```
  usuário:  admin
  senha:    7x63tlKq...
```

No `--update` não: ele não muda credencial nenhuma, e um `qh --all --update`
despejaria todas as senhas no terminal de uma vez. A instalação e o
`--reinstall` imprimem, e o `qh <app>` simples num serviço já instalado também
— que é a forma deliberada de consultar. Isso fica no seu scrollback.

Qual secret é esse vem do `install.ini`. Só o que é senha digitada é impresso —
chave de JWT e token de API ao lado também são secrets:

```ini
[login]
user = admin
password = filebrowser-admin-password
```

Stack cujas units têm logins diferentes nomeia um por unit:

```ini
[login.vm-windows]
user = Docker
password = vm-windows-password

[login.vm-chromeos]
user = admin
password = vm-chromeos-password
```

Quando um secret guarda os dois lados, na forma `usuario:senha` que o app lê,
basta nomear uma vez e a instalação divide no primeiro `:`:

```ini
[login]
credentials = vaultzap-basic-auth
```

O `check.py` reprova o build se algum desses nomes não for um `Secret=`
declarado por alguma unit.

Pra digitar os secrets em vez de gerá-los:

```bash
qh filebrowser --reinstall --ask-secrets --apply
```

Enter aceita o valor gerado, então dá pra digitar a única senha que você usa
pra entrar e deixar o resto aleatório. Exige terminal e `--apply`.

## Perguntas durante a instalação

Alguns valores de `.env` são escolha de uma lista conhecida e só valem no
primeiro start — a edição do Windows é baixada uma vez e nunca mais revista.
Essas são perguntadas, com o padrão primeiro:

```
VERSION — qual Windows instalar
  1) 11   Windows 11 Pro — 7.9 GB   [padrão]
  2) 10   Windows 10 Pro — 5.8 GB
```

Enter aceita o padrão. Sem terminal, os padrões ficam e a instalação avisa.

## Sandbox

```bash
qh traccar --apply --prefix /tmp/teste
```

Redireciona todos os caminhos, e não toca em systemd nem podman — os passos que
tocariam são impressos em vez de executados.

## Ciclo de vida

```bash
qh <app> --apply                      # instalar
qh <app> --update --apply             # depois de um bump no repositório
qh <app> --backup --apply --out ~/backups
qh <app> --remove --apply             # para e tira, mantendo os dados
qh <app> --remove --purge --apply     # apaga tudo
```

Conferindo depois:

```bash
systemctl --user is-active <app>
podman ps --filter "name=<app>"       # confirma healthy, não só iniciado
journalctl --user -u <app> -f
```

Serviço com dependências (immich, owntracks, paperless-ngx) sobe pelo principal
sozinho — o `Requires=` puxa a cadeia. Pra derrubar antes de um backup, parar
todos juntos, senão as dependências seguem gravando.

Remover a unit não desregistra o nó da tailnet; isso é no admin do Tailscale.

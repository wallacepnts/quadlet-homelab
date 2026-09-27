# Mailpit

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/mailpit.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor SMTP que aceita toda mensagem e não entrega nenhuma. Aponte a
configuração de e-mail de um app para ele e leia no navegador o que foi
enviado, em vez de num endereço de verdade.

## Instalação

```bash
qh mailpit            # mostra o plano
qh mailpit --apply
```

A instalação exibe o usuário e a senha no final. Abra
`http://<ip-do-host>:8025` ou `https://mailpit.<your-tailnet>.ts.net`.

Depois aponte seu app para a porta SMTP — host `<ip-do-host>`, porta **1025**,
sem autenticação e sem TLS:

```
SMTP_HOST=<ip-do-host>
SMTP_PORT=1025
```

<details>
<summary><b>Instalação manual</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/mailpit/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/mailpit

printf 'admin:%s' "$(openssl rand -hex 12)" \
  | podman secret create mailpit-ui-auth -

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/mailpit/mailpit.container
wget -O ~/.config/containers/env/mailpit.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/mailpit/.env.example

systemctl --user daemon-reload
systemctl --user start mailpit
```

Para ler a senha depois: `podman secret inspect mailpit-ui-auth --showsecret
--format '{{.SecretData}}'`.

</details>

## Arquivos

```
mailpit.container   unit
.env.example        ambiente
install.ini         a receita do segredo
```

Dados em `~/.config/containers/volumes/mailpit/data`. Web na **8025**, SMTP na
**1025**.

## Autenticação

A interface web pede senha; a porta SMTP não. É de propósito: os apps que
enviam estão na sua própria rede e cada um precisaria de credencial, enquanto
a interface guarda tudo que eles mandaram — redefinição de senha, link de
confirmação, fatura.

As duas vêm de um segredo só, `mailpit-ui-auth`, no formato `usuário:senha`
que o Mailpit lê.

## Senha sua

A instalação gera uma. Para escolher a sua, na instalação ou depois dela:

```bash
qh mailpit --reinstall --ask-secrets --apply
```

e digite **usuário e senha juntos**, como o Mailpit os lê:

```
admin:sua-senha
```

Medido na v1.31.2, dois jeitos de errar sem erro nenhum:

- **Nada de espaço na senha.** O Mailpit separa o valor em espaços para aceitar
  vários usuários, então `admin:minha senha` deixa a senha só como `minha` — e
  `senha` vira uma segunda entrada. O serviço sobe e a senha que você digitou é
  recusada.
- **Só a senha**, sem o `admin:` na frente, e o serviço sobe mesmo assim, com
  autenticação ligada e ninguém conseguindo entrar.

`:` na senha pode — ele separa no primeiro. Enter sem nada digitado gera outra
aleatória. O `--reinstall` recria o segredo e reinicia o serviço, sem tocar nas
mensagens guardadas — mas também põe o `.env.example` de volta por cima de
`~/.config/containers/env/mailpit.env`, então guarde antes o que você mudou ali. O `qh mailpit` mostra o usuário e a senha em uso.

## Atualizar

```bash
qh mailpit --update --apply
```

Fixado em `v1.31.2`. Nada atualiza sozinho — a versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh mailpit --backup --apply --out ~/backups
```

Para o serviço, empacota os dados, o `.env` e os segredos, e religa. A frio de
propósito: copiar banco em uso gera um arquivo que só falha na hora de
restaurar.

Para restaurar, por cima dos dados atuais:

```bash
qh mailpit --restore ~/backups/mailpit-20260809-1200.tar.gz --apply
```

Ele pede que você digite `mailpit` para confirmar, porque os dados atuais são
apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh mailpit --remove --apply           # para, mantém os dados
qh mailpit --remove --purge --apply   # e apaga volumes, segredos e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é removido por
aqui — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status mailpit
podman logs -f mailpit
podman exec mailpit /mailpit readyz
```

Enviar uma mensagem de teste a partir do host:

```bash
python3 -c "import smtplib; smtplib.SMTP('127.0.0.1', 1025).sendmail(
  'a@test', ['b@test'], 'Subject: hello\n\nfuncionou')"
```

## Créditos

[Mailpit](https://github.com/axllent/mailpit) — MIT

[Documentação oficial](https://mailpit.axllent.org/docs/)

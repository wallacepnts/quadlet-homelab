# Radicale

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radicale.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor CalDAV/CardDAV leve e minimalista.

## Instalar

```bash
qh radicale            # mostra o plano
qh radicale --apply
```

Abrir `http://<ip-do-host>:5232` ou `https://radicale.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/radicale.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/radicale/{data,config}
wget -O ~/.config/containers/volumes/radicale/config/config \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/config/config

# 3. Usuário/senha — hash bcrypt gerado localmente, formato htpasswd
#    (usuario:hash, um por linha). O arquivo /config/users precisa ser
#    legível por qualquer uid (mundo-legível) porque o container roda
#    com um uid interno fixo (2999) que não é o seu — sem UserNS=keep-id
#    nesta imagem (ver Arquitetura), é a única forma dele enxergar o
#    arquivo.
read -p "Usuário do Radicale: " RADICALE_USER
read -s -p "Senha do Radicale: " RADICALE_PW; echo
RADICALE_USER="$RADICALE_USER" RADICALE_PW="$RADICALE_PW" python3 -c "
import bcrypt, os
user = os.environ['RADICALE_USER']
pw = os.environ['RADICALE_PW'].encode()
h = bcrypt.hashpw(pw, bcrypt.gensalt()).decode()
print(f'{user}:{h}')
" > ~/.config/containers/volumes/radicale/config/users
unset RADICALE_PW
chmod 644 ~/.config/containers/volumes/radicale/config/users

# 4. Env não-secreto — baixar o exemplo
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/radicale.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/.env.example

# 5. Subir
systemctl --user daemon-reload
systemctl --user start radicale
```

</details>

## Arquivos

```
radicale.container
.env.example
```

## Atualizar

```bash
qh radicale --update --apply
```

Fixado em `3.7.6.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh radicale --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh radicale --restore ~/backups/radicale-20260809-1200.tar.gz --apply
```

Ele pede que você digite `radicale` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh radicale --remove --apply           # para e tira, mantendo os dados
qh radicale --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status radicale
podman logs -f radicale
```

## Créditos

[tomsquest/docker-radicale](https://github.com/tomsquest/docker-radicale) — MIT

[Documentação oficial](https://radicale.org/v3.html)

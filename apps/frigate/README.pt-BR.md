# Frigate

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/frigate.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

NVR com detecção de objetos por IA — CPU-only por padrão, sem câmera configurada ainda.

## Instalar

```bash
qh frigate            # mostra o plano
qh frigate --apply
```

Abrir `http://<ip-do-host>:8971` ou `https://frigate.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/frigate/frigate.container

# 2. Diretório de config — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/frigate/config

# 3. Caminho de gravação — decidir onde as gravações vão morar (disco
#    com espaço de sobra; pode ser fora de ~/.config/containers/volumes)
mkdir -p ~/.config/environment.d
cat > ~/.config/environment.d/frigate.conf <<EOF
FRIGATE_MEDIA_DIR=$HOME/frigate-media
EOF
mkdir -p "$HOME/frigate-media"
# Se preferir outro disco/mount, usar o path real ali em cima.

# 4. Aplicar a env.d nova (precisa de daemon-reload, não só reiniciar
#    o serviço — é o systemd --user que precisa reler o ambiente)
systemctl --user daemon-reload

# 5. Subir
systemctl --user start frigate

# 6. Capturar a senha do admin ANTES do restart do próximo passo —
#    testado na prática: essa mensagem só aparece no log UMA VEZ, no
#    primeiro start com o banco de usuários vazio; reiniciar depois
#    (passo 7) não recria o usuário (ele já existe, persistido no
#    volume) então a mensagem não volta a aparecer, mesmo a conta
#    continuando válida. Esperar ficar healthy antes de checar.
until podman inspect frigate --format '{{.State.Health.Status}}' 2>/dev/null | grep -qE 'healthy|unhealthy'; do sleep 3; done
podman logs frigate 2>&1 | grep -A3 "Created a default user"
# Anotar usuário/senha mostrados acima — não vão aparecer de novo depois do restart abaixo.

# 7. Limpar a câmera de exemplo que a imagem gera sozinha no primeiro
#    start (ver aviso acima) — sem isso, fica tentando conectar num IP
#    fake e poluindo os logs até você configurar uma câmera de verdade
cat > ~/.config/containers/volumes/frigate/config/config.yaml <<EOF
mqtt:
  enabled: False

cameras: {}
EOF
systemctl --user restart frigate
```

</details>

## Arquivos

```
frigate.container
```

## Atualizar

```bash
qh frigate --update --apply
```

Fixado em `0.17.2`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh frigate --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh frigate --restore ~/backups/frigate-20260809-1200.tar.gz --apply
```

Ele pede que você digite `frigate` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh frigate --remove --apply           # para e tira, mantendo os dados
qh frigate --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status frigate
podman logs -f frigate
```

## Créditos

[blakeblackshear/frigate](https://github.com/blakeblackshear/frigate) — MIT

[Documentação oficial](https://frigate.video)

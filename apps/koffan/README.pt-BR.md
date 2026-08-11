# Koffan

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/koffan.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

A lista de compras da casa. Todo mundo abre a mesma lista no celular, vai
marcando no corredor do mercado, e os outros veem mudar.

Não há contas: uma senha dá entrada, e quem tem edita. É esse o modelo inteiro,
e é por isso que ele serve pra uma família e não pra uma empresa.

## Instalação

```bash
qh koffan            # mostra o plano
qh koffan --apply
```

O `qh` gera a senha e mostra uma vez, no fim da instalação. Abrir
`https://koffan.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/koffan/data

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/koffan/koffan.container
wget -O ~/.config/containers/env/koffan.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/koffan/.env.example

openssl rand -base64 18 | tr -d '\n' | podman secret create koffan-password -

# O container roda como uid 1000, que não é o seu depois do mapeamento
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/koffan

systemctl --user daemon-reload
systemctl --user start koffan
```

</details>

## Arquivos

```
koffan.container   unit
.env.example       ambiente
install.ini
```

A lista é o `shopping.db` em `~/.config/containers/volumes/koffan/data`.
SQLite com WAL ligado, então a pasta guarda três arquivos que só fazem sentido
juntos — que é justamente o que o modo `sqlite` do gancho do zerobyte copia de
forma consistente.

## A senha

É a única credencial, então é um secret do Podman e não uma linha no `.env`
como o compose oficial sugere — lá o padrão que vem é `shopping123`. O `qh`
gera com `rand-base64 18` e mostra uma vez.

Pra trocar depois:

```bash
podman secret rm koffan-password
openssl rand -base64 18 | tr -d '\n' | podman secret create koffan-password -
qh koffan --update --apply
```

## Notificações

O `WEBHOOK_URL` do `.env` é chamado a cada mudança. Apontado pro
[ntfy](../ntfy/README.pt-BR.md) daqui, o celular apita quando alguém acrescenta
pão no caminho de casa:

```ini
WEBHOOK_URL=http://ntfy:2586/compras
```

Os dois containers estão na `tsdproxy-net`, então `ntfy` resolve pelo nome.

## Atualizar

```bash
qh koffan --update --apply
```

Fixado em `v2.13.0`.

## Backup

```bash
qh koffan --backup --apply --out ~/backups
```

Para o serviço, empacota a pasta de dados e o `.env`, e sobe de novo.

Pra restaurar, por cima dos dados atuais:

```bash
qh koffan --restore ~/backups/koffan-20260811-1200.tar.gz --apply
```

## Remover

```bash
qh koffan --remove --apply           # para e mantém a lista
qh koffan --remove --purge --apply   # e apaga o volume e o secret
```

## Comandos

```bash
systemctl --user status koffan
podman logs -f koffan
```

## Créditos

[PanSalut/Koffan](https://github.com/PanSalut/Koffan), de Artur Witoś.

A licença é **MIT com a Commons Clause**: livre pra rodar e modificar, mas
proíbe vender o software ou um serviço cujo valor seja substancialmente o
próprio software. Rodar em casa é exatamente o que ela permite — a cláusula
importa antes de construir algo comercial em cima.

[Documentação oficial](https://github.com/PanSalut/Koffan#readme)

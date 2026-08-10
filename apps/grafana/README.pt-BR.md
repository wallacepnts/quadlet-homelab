# Grafana

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/grafana.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Painéis sobre dados que moram em outro lugar. O Grafana não guarda métrica
nenhuma — ele consulta uma fonte e desenha o resultado, então serve na medida
do que você apontar para ele.

## Instalação

```bash
qh grafana            # mostra o plano
qh grafana --apply
```

A instalação exibe o usuário e a senha no final. Abra
`http://<ip-do-host>:3004` ou `https://grafana.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/grafana/data
podman unshare chown -R 472:472 ~/.config/containers/volumes/grafana

openssl rand -hex 10 | podman secret create grafana-admin-password -

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/grafana/grafana.container
wget -O ~/.config/containers/env/grafana.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/grafana/.env.example

systemctl --user daemon-reload
systemctl --user start grafana
```

</details>

## Arquivos

```
grafana.container   unit
.env.example        ambiente
install.ini         a receita da senha
```

Dados em `~/.config/containers/volumes/grafana/data`, na porta **3004**. A
configuração dele — usuários, painéis, fontes de dados — é SQLite nesse
diretório.

O `User=472` é o uid com que a imagem roda, e declarar isso é o que faz a
instalação ajustar o dono do volume. Sem ele, o Grafana sobe e não consegue
escrever o banco.

## Para onde apontar

Sozinho, o Grafana não mostra nada. Este repositório não traz banco de série
temporal, então a fonte é você que fornece:

- O **[Beszel](../beszel/README.pt-BR.md)** já coleta CPU, RAM, disco e
  containers deste host e desenha sozinho. Se for só isso que você quer, o
  Grafana acrescenta um passo em vez de tirar.
- Um **Prometheus** ou **InfluxDB** em outro ponto da rede, adicionado em
  Connections → Data sources.
- **SQLite ou Postgres** de outro serviço, pelo plugin correspondente, quando a
  pergunta é sobre o dado do app e não sobre a máquina.

## Atualizar

```bash
qh grafana --update --apply
```

Pinado em `13.1.3`. Nada atualiza sozinho — a versão nova entra quando você
roda o comando acima.

Repare na imagem: a `grafana/grafana` é a compilação OSS e é a que acompanha as
releases. A `grafana/grafana-oss` é um espelho atrasado, e a
`grafana-enterprise` é outro produto.

## Backup

```bash
qh grafana --backup --apply --out ~/backups
```

Para o serviço, empacota os dados, o `.env` e o segredo, e religa. O banco
guarda os painéis que você montou, que é a parte que daria trabalho refazer.

Para restaurar, por cima dos dados atuais:

```bash
qh grafana --restore ~/backups/grafana-20260810-1200.tar.gz --apply
```

## Remover

```bash
qh grafana --remove --apply           # para, mantém os dados
qh grafana --remove --purge --apply   # e apaga o volume, o segredo e o .env
```

## Comandos

```bash
systemctl --user status grafana
podman logs -f grafana
podman exec grafana wget -qO- http://127.0.0.1:3000/api/health
```

## Créditos

[Grafana](https://github.com/grafana/grafana) — AGPL-3.0

[Documentação oficial](https://grafana.com/docs/grafana/latest/)

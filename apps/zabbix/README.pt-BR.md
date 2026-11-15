# Zabbix

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zabbix.svg" width="64" height="64" alt="">

O [Zabbix](https://www.zabbix.com) monitora servidores, redes e serviços:
agentes nas máquinas, SNMP, checagens HTTP, triggers que transformam números em
problemas, e alertas. São três containers: o **server**, que coleta e avalia, a
**interface web** e o **PostgreSQL**.

## Instalação

```bash
qh zabbix            # mostra o plano
qh zabbix --apply
```

O primeiro start leva um ou dois minutos: o server cria o schema do banco (uns
30 s medidos) e só então a interface web sobe. Depois abra
`https://zabbix.<your-tailnet>.ts.net`.

**O primeiro login é o padrão do próprio Zabbix, `Admin` / `zabbix`.** A imagem
não tem configuração para isso, então a instalação não consegue gerar uma senha.
Troque na hora: *Users → Users → Admin → Change password*.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
# 1. Baixar as units (sem clonar o repositório)
mkdir -p ~/.config/containers/systemd/zabbix
wget -P ~/.config/containers/systemd/zabbix/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zabbix/zabbix-net.network \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zabbix/zabbix-postgres.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zabbix/zabbix-server.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zabbix/zabbix.container

# 2. A pasta do banco (a unit roda como uid 70, o do próprio postgres)
mkdir -p ~/.config/containers/volumes/zabbix/postgres
podman unshare chown -R 70:70 ~/.config/containers/volumes/zabbix/postgres

# 3. A senha do banco, compartilhada pelas três units
openssl rand -hex 24 | podman secret create zabbix-postgres-password -

systemctl --user daemon-reload
systemctl --user start zabbix
```

`start zabbix` sobe o server e o Postgres pelo `Requires=`.

</details>

## Arquivos

```
zabbix.container            interface web (nginx + PHP)
zabbix-server.container     o server
zabbix-postgres.container   banco de dados
zabbix-net.network          rede que os três compartilham
install.ini                 a receita do segredo e de onde vêm as atualizações
```

Interface web na **8098**, porta trapper do server na **10051**, as duas na LAN.
Dados em `~/.config/containers/volumes/zabbix/postgres`; o server e a interface
web não guardam nada em disco.

## PostgreSQL, não SQLite

O repositório prefere SQLite, mas o server do Zabbix não tem modo SQLite: roda em
PostgreSQL ou MySQL, e SQLite existe só para o *proxy*. O PostgreSQL é o que o
compose do próprio projeto usa, e a major (17) é a que ele valida.

## O host "Zabbix server" nasce com o agente quebrado

Uma instalação nova traz um host chamado *Zabbix server* cujo agente é esperado
em `127.0.0.1:10050`. Não há agente nesta stack, então os itens falham com
"network error" e o host fica vermelho. Desative esse host, ou instale um agente
em algum lugar e aponte o host para ele.

Para monitorar uma máquina, instale o agente do Zabbix nela e faça-o alcançar
este host na porta **10051** (checagens ativas), ou deixe o server alcançar o
agente na **10050** (passivas). As duas são TCP simples, na tailnet ou na LAN.

## Atualização

```bash
qh zabbix --update --apply
```

Fixado em `17.11-alpine`. A imagem do próprio app não tem versão aqui: o `qh` fixa a última release neste host, e `qh zabbix --update --latest --apply` a muda. O server e a interface web
compartilham uma tag e têm de andar juntos. O server atualiza o próprio schema ao subir, então
faça um backup antes de um salto de minor. O Postgres fica na 17.

## Hardening

Medido em `alpine-7.4.16` com as mesmas flags das units: zero capabilities em
todos, `NoNewPrivileges`, e o server e o Postgres somente leitura (o server
precisa só de um `/tmp` de 64 MB). A interface web **não** é somente leitura: o
entrypoint grava a configuração do nginx em `/etc/nginx` a cada start. As duas
imagens do Zabbix já rodam como uid 1997.

O `RunInit=true` no server é obrigatório, não estético: sem ele o stop espera os
10 s e termina em SIGKILL. Com ele, 1–2 s.

Testado em laboratório: schema criado pelo server, Postgres alcançável dos dois,
login web (a conta padrão redireciona), dashboard servido e a porta 10051 aberta.
Não testado: um agente de verdade, nem o navegador pelo tsdproxy.

## Backup

```bash
qh zabbix --backup --apply --out ~/backups
```

A frio, como as outras stacks com banco: para as três units, empacota o volume e
o segredo, e sobe de novo.

## Remover

```bash
qh zabbix --remove --apply           # para, mantém os dados
qh zabbix --remove --purge --apply   # e apaga o volume e o segredo
```

O nó da tailnet não é desregistrado por isso — é feito no admin do Tailscale.

## Comandos

```bash
systemctl --user status zabbix zabbix-server zabbix-postgres
podman logs -f zabbix-server
```

## Créditos

[zabbix/zabbix](https://github.com/zabbix/zabbix) — AGPL-3.0; as imagens vêm de
[zabbix/zabbix-docker](https://github.com/zabbix/zabbix-docker).

[Documentação oficial](https://www.zabbix.com/documentation/current/en/manual/installation/containers)

# Zabbix

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zabbix.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

[Zabbix](https://www.zabbix.com) monitors servers, networks and services:
agents on the machines, SNMP, HTTP checks, triggers that turn numbers into
problems, and alerts. Three containers: the **server** that collects and
evaluates, the **web interface**, and **PostgreSQL**.

## First run

The first start takes a minute or two: the server creates the database schema
(about 30 s measured), and only then does the web interface come up. Then open
`https://zabbix.<your-tailnet>.ts.net`.

**The first login is Zabbix's own default, `Admin` / `zabbix`.** The image has
no setting for it, so the install cannot generate one. Change it at once:
*Users → Users → Admin → Change password*.

## Files

```
zabbix.container            web interface (nginx + PHP)
zabbix-server.container     the server
zabbix-postgres.container   database
zabbix-net.network          network the three share
install.ini                 the secret's recipe and where updates come from
```

Web interface on **8098**, the server's trapper port on **10051**, both on the
LAN. Data in `~/.config/containers/volumes/zabbix/postgres`; the server and the
web interface keep nothing on disk.

## PostgreSQL, not SQLite

The repository prefers SQLite, but Zabbix's server has no SQLite mode: it runs
on PostgreSQL or MySQL, and SQLite exists only for the *proxy*. PostgreSQL is the
one the project's own compose uses, and the major (17) is the one it validates.

## The "Zabbix server" host starts with a broken agent

A fresh install ships a host called *Zabbix server* whose agent is expected at
`127.0.0.1:10050`. There is no agent in this stack, so its items fail with
"network error" and the host turns red. Disable that host, or install an agent
somewhere and point the host at it.

To monitor a machine, install the Zabbix agent there and have it reach this
host on port **10051** (active checks) or let the server reach the agent on
**10050** (passive). Both are plain TCP on the tailnet or LAN.

## Update

The server and the web interface share one tag and must move together. The server upgrades its own schema on start, so take a backup before a minor jump. Postgres stays on 17.

## Hardening

Measured on `alpine-7.4.16` with the same flags as the units: no capabilities
anywhere, `NoNewPrivileges`, and the server and Postgres read-only (the server
needs only a 64 MB `/tmp`). The web interface is **not** read-only: its
entrypoint writes the nginx configuration into `/etc/nginx` on every start.
Both Zabbix images already run as uid 1997.

`RunInit=true` on the server is required, not cosmetic: without it a stop waits
the 10 s and ends in SIGKILL. With it, 1–2 s.

Tested in a lab: schema created by the server, Postgres reachable from both, web
login (the default account redirects), dashboard served, and the port 10051
open. Not tested: a real agent, or the browser through tsdproxy.

## Backup

Cold, like the other stacks with a database: it stops the three units, packs the
volume and the secret, and starts them again.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[zabbix/zabbix](https://github.com/zabbix/zabbix) — AGPL-3.0; the images come from
[zabbix/zabbix-docker](https://github.com/zabbix/zabbix-docker).

[Official documentation](https://www.zabbix.com/documentation/current/en/manual/installation/containers)

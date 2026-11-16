The first start takes a minute or two: the server creates the database schema
(about 30 s measured), and only then does the web interface come up. Then open
`https://zabbix.<your-tailnet>.ts.net`.

**The first login is Zabbix's own default, `Admin` / `zabbix`.** The image has
no setting for it, so the install cannot generate one. Change it at once:
*Users → Users → Admin → Change password*.

### PostgreSQL, not SQLite

The repository prefers SQLite, but Zabbix's server has no SQLite mode: it runs
on PostgreSQL or MySQL, and SQLite exists only for the *proxy*. PostgreSQL is the
one the project's own compose uses, and the major (17) is the one it validates.

### The "Zabbix server" host starts with a broken agent

A fresh install ships a host called *Zabbix server* whose agent is expected at
`127.0.0.1:10050`. There is no agent in this stack, so its items fail with
"network error" and the host turns red. Disable that host, or install an agent
somewhere and point the host at it.

To monitor a machine, install the Zabbix agent there and have it reach this
host on port **10051** (active checks) or let the server reach the agent on
**10050** (passive). Both are plain TCP on the tailnet or LAN.

### Update

The server and the web interface share one tag and must move together. The server upgrades its own schema on start, so take a backup before a minor jump. Postgres stays on 17.

### Backup

Cold, like the other stacks with a database: it stops the three units, packs the
volume and the secret, and starts them again.

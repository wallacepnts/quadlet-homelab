The first start takes a minute or two (it creates the database schema). Then open `https://zabbix.<your-tailnet>.ts.net`.

**The first login is Zabbix's own default, `Admin` / `zabbix`.** The image has no setting for it, so change it at once: *Users → Users → Admin → Change password*.

The "Zabbix server" host starts red: its agent is expected at `127.0.0.1:10050` and this stack has none. Disable that host. To monitor a machine, install the Zabbix agent there and have it reach this host on port **10051** (active) or let the server reach it on **10050** (passive).

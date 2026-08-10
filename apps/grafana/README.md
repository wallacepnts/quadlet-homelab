# Grafana

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/grafana.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Dashboards over data that lives somewhere else. Grafana stores no metrics of
its own — it queries a data source and draws the result, so it is only as
useful as what you point it at.

## Install

```bash
qh grafana            # shows the plan
qh grafana --apply
```

The install prints the user and password at the end. Open
`http://<host-ip>:3004` or `https://grafana.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

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

## Files

```
grafana.container   unit
.env.example        environment
install.ini         the password's recipe
```

Data in `~/.config/containers/volumes/grafana/data`, on port **3004**. Its own
configuration — users, dashboards, data sources — is SQLite in that directory.

`User=472` is the uid the image runs as, and declaring it is what makes the
install chown the volume. Without that, Grafana starts and cannot write its
database.

## What to point it at

Grafana on its own shows nothing. This repository ships no time-series
database, so you supply the source:

- **[Beszel](../beszel)** already collects CPU, RAM, disk and container
  metrics for this host and draws them itself. If that is all you want,
  Grafana adds a step rather than removing one.
- A **Prometheus** or **InfluxDB** elsewhere on the network, added under
  Connections → Data sources.
- **SQLite or Postgres** from another service, through the respective plugin,
  when the question is about the app's own data rather than the machine's.

## Update

```bash
qh grafana --update --apply
```

Pinned to `13.1.3`. Nothing updates on its own — a new version is applied when
you run the command above.

Note the image: `grafana/grafana` is the OSS build and the one that tracks the
releases. `grafana/grafana-oss` is a mirror that lags behind it, and
`grafana-enterprise` is a different product.

## Backup

```bash
qh grafana --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secret, and starts it
again. The database holds the dashboards you built, which is the part that
would take real time to recreate.

To restore, over the current data:

```bash
qh grafana --restore ~/backups/grafana-20260810-1200.tar.gz --apply
```

## Remove

```bash
qh grafana --remove --apply           # stops it, keeps the data
qh grafana --remove --purge --apply   # and deletes the volume, secret and .env
```

## Commands

```bash
systemctl --user status grafana
podman logs -f grafana
podman exec grafana wget -qO- http://127.0.0.1:3000/api/health
```

## Credits

[Grafana](https://github.com/grafana/grafana) — AGPL-3.0

[Official documentation](https://grafana.com/docs/grafana/latest/)

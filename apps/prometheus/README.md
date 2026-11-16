# Prometheus

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prometheus.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Asks each target for its metrics on a schedule and keeps the history. It is
the data source [Grafana](../grafana) draws from — Grafana stores nothing, this
one stores everything.

## First run

Open `http://<host-ip>:9090` or `https://prometheus.<your-tailnet>.ts.net`.
Status → Targets shows what it is scraping and whether each one answered.

## Files

```
prometheus.container   unit
config/prometheus.yml  the scrape list, into the volume
install.ini            where that file goes, and where updates.py looks
```

Config and history in `~/.config/containers/volumes/prometheus/`, on port
**9090**. There is no `.env`: everything is in the YAML.

`User=65534` is `nobody`, the uid the image runs as. Declaring it is what makes
the install chown the volume — without that, Prometheus starts and cannot write
its database.

## Adding targets

The shipped config scrapes one thing: Prometheus itself. That proves the file
is being read and gives you a working query on day one. Anything else you add
by hand:

```yaml
  - job_name: node
    static_configs:
      - targets: ["node-exporter:9100"]
```

Targets are reachable by **container name**, because every service here joins
`tsdproxy-net`. No IP, no host port.

A service only appears here if it already speaks the exposition format — most
in this repository do not. What you usually want first is a `node-exporter`
for the machine itself, and it is not shipped here.

After editing:

```bash
qh prometheus --update --apply
```

## Backup

It stops the service, packs the config and the history, and starts it again.
Cold on purpose: the TSDB is a database like any other, and copying it live
gives an archive that only fails when you restore it.

## Credits

[Prometheus](https://github.com/prometheus/prometheus) — Apache-2.0

[Official documentation](https://prometheus.io/docs/introduction/overview/)

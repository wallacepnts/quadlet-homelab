# Prometheus

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prometheus.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Asks each target for its metrics on a schedule and keeps the history. It is
the data source [Grafana](../grafana) draws from — Grafana stores nothing, this
one stores everything.

## Install

```bash
qh prometheus            # shows the plan
qh prometheus --apply
```

Open `http://<host-ip>:9090` or `https://prometheus.<your-tailnet>.ts.net`.
Status → Targets shows what it is scraping and whether each one answered.

<details>
<summary><b>Manual install</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/prometheus/{config,data}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/prometheus/prometheus.container
wget -O ~/.config/containers/volumes/prometheus/config/prometheus.yml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/prometheus/config/prometheus.yml
podman unshare chown -R 65534:65534 ~/.config/containers/volumes/prometheus

systemctl --user daemon-reload
systemctl --user start prometheus
```

</details>

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

## Update

```bash
qh prometheus --update --apply
```

Pinned to `v3.13.2`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh prometheus --backup --apply --out ~/backups
```

It stops the service, packs the config and the history, and starts it again.
Cold on purpose: the TSDB is a database like any other, and copying it live
gives an archive that only fails when you restore it.

To restore, over the current data:

```bash
qh prometheus --restore ~/backups/prometheus-20260810-1200.tar.gz --apply
```

## Remove

```bash
qh prometheus --remove --apply           # stops it, keeps the history
qh prometheus --remove --purge --apply   # and deletes the volume
```

## Commands

```bash
systemctl --user status prometheus
podman logs -f prometheus
podman exec prometheus wget -qO- http://127.0.0.1:9090/-/healthy
podman exec prometheus wget -qO- 'http://127.0.0.1:9090/api/v1/query?query=up'
```

## Credits

[Prometheus](https://github.com/prometheus/prometheus) — Apache-2.0

[Official documentation](https://prometheus.io/docs/prometheus/latest/)

Open `http://<host-ip>:9090` or `https://prometheus.<your-tailnet>.ts.net`.
Status → Targets shows what it is scraping and whether each one answered.

### Adding targets

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

### Backup

It stops the service, packs the config and the history, and starts it again.
Cold on purpose: the TSDB is a database like any other, and copying it live
gives an archive that only fails when you restore it.

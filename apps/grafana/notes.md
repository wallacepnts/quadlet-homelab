The install prints the user and password at the end. Open
`http://<host-ip>:3004` or `https://grafana.<your-tailnet>.ts.net`.

### What to point it at

Grafana on its own shows nothing — it stores no metrics, so the first thing to
do after signing in is add a source under Connections → Data sources.

**[Prometheus](../prometheus)** is in this repository and is the one to reach
for. Its URL is the container name, because both join `tsdproxy-net`:

```
http://prometheus:9090
```

Note that it scrapes only itself out of the box, so a fresh Grafana on a fresh
Prometheus draws one line about Prometheus. Adding targets is a Prometheus
job, not a Grafana one.

Other sources that make sense here:

- **[Beszel](../beszel)** already collects CPU, RAM, disk and container metrics
  for this host and draws them itself. If that is all you want, Grafana and
  Prometheus add two services rather than removing one.
- An **InfluxDB** elsewhere on the network.
- **SQLite or Postgres** from another service, through the respective plugin,
  when the question is about the app's own data rather than the machine's.

### Update

Note the image: `grafana/grafana` is the OSS build and the one that tracks the
releases. `grafana/grafana-oss` is a mirror that lags behind it, and
`grafana-enterprise` is a different product.

### Backup

It stops the service, packs the data, the `.env` and the secret, and starts it
again. The database holds the dashboards you built, which is the part that
would take real time to recreate.

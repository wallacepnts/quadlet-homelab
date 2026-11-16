Open `https://vaultwarden.<your-tailnet>.ts.net`.

The vault is reachable over the tailnet only. `PublishPort=8082:80` ships
commented out in the unit: publishing it would also answer to anyone on the
LAN, which is a wider door than a password vault needs. Uncomment it if you
want `http://<host-ip>:8082` too.

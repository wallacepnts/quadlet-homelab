`qh` generates the password and prints it once, at the end of the install.
Open `https://koffan.<your-tailnet>.ts.net`.

### The password

It is the only credential, so it is a Podman secret and not a line in the
`.env` the upstream compose suggests — the shipped default there is
`shopping123`. `qh` generates it with `rand-base64 18` and shows it once.

To change it later:

```bash
podman secret rm koffan-password
openssl rand -base64 18 | tr -d '\n' | podman secret create koffan-password -
qh koffan --update --apply
```

### Notifications

`WEBHOOK_URL` in the `.env` is called on every change. Pointed at the
[ntfy](../ntfy) here, the phone buzzes when someone adds bread on the way home:

```ini
WEBHOOK_URL=http://ntfy:2586/groceries
```

Both containers are on `tsdproxy-net`, so `ntfy` resolves by name.

### Backup

Stops it, packs the data folder and the `.env`, starts it again.

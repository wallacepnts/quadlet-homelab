**Read this first.** It works as a dashboard, but:

- **It holds your Podman socket.** It lists, starts, stops and creates *any* container of your user: whoever is logged in to it is, in practice, you on this host. That is why the LAN port stays closed under the default `tailnet` rule.
- **Installing apps from its store failed in testing** (`mkdir /DATA: permission denied`). What it creates is not this repository's: no Quadlet, no pinned tag, no hardening. To install apps, use the store (`qh-store`) or `qh`.
- **It changes your Podman at the first start**: it creates the `casa-net` network (`10.22.0.0/16`, `SUBNET` in the `.env`).

Open `https://casa.<your-tailnet>.ts.net`; `qh` prints the login (`admin` and the generated password). On removal, `podman network rm casa-net` and remove what it installed.

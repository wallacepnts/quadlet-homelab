# netboot.xyz

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/netbootxyz.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A network boot (PXE) menu for installing or trying distros and tools without writing a USB stick.

## First run

Open `http://<host-ip>:8088` or `https://netbootxyz.<your-tailnet>.ts.net`. Port
69 is published too, but it is TFTP over UDP — what the machines booting from it
speak, not a page a browser can open.

## Files

```
netbootxyz.container
.env.example
install.ini
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[netbootxyz/docker-netbootxyz](https://github.com/netbootxyz/docker-netbootxyz) — MIT

[Official documentation](https://netboot.xyz/docs/docker)

# Proxmox VE

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/proxmox.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The Proxmox hypervisor in a container, for trying it without dedicating a machine — runs privileged.

It is the interface, not a hypervisor with KVM behind it: to actually run a guest here, see [vm](../vm).

## First run

Open `http://<host-ip>:8010` or `https://proxmox.<your-tailnet>.ts.net`.

## Files

```
proxmox.container
install.ini
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[dockur/proxmox](https://github.com/dockur/proxmox) — MIT

[Official documentation](https://pve.proxmox.com/pve-docs/)

# Hermes Agent

<img src="https://cdn.jsdelivr.net/gh/NousResearch/hermes-agent@main/website/static/img/logo.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A personal AI agent with skills and memory, exposing an OpenAI-compatible API for the other services to call.

## First run

Open `http://<host-ip>:8642` or `https://hermes.<your-tailnet>.ts.net`.

## Files

```
hermes-agent.container
.env.example
install.ini
```

## No memory limit

The unit sets `PidsLimit=`, not `Memory=`. A memory cap in a rootless unit
needs the memory controller delegated to the user manager, and on a host where
it is not, the container cannot be created at all:

```
memory.swap.max: no such file or directory
```

To check whether your host delegates it:

```bash
ls /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/ | grep memory.max
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — MIT

[Official documentation](https://hermes-agent.nousresearch.com)

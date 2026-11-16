# Gitea Runner

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gitea.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Runs the Actions workflows of the [Gitea](../gitea) next door — the same CI this
repository gets from GitHub, on a machine you own.

> **It creates containers through the Podman socket.** That is how it runs a
> job, and it is also the whole of its blast radius: a workflow in any
> repository this runner serves can do whatever `podman` can do as your user.
> Point it at repositories you trust, the way you would with a shell.

Actions is on by default in Gitea since 1.21, so nothing has to be turned on
first — this repository pins 1.27.3.

## First run

It asks for the registration token. Get it from Gitea, either in
**Site Administration → Actions → Runners → Create new Runner**, or from the
command line:

```bash
podman exec -u git gitea gitea actions generate-runner-token
```

The token is spent on the first registration. After that the runner uses the
`.runner` file in its volume and never reads the token again.

## Files

```
gitea-runner.container
gitea-runner.env.example
config.yaml                 installed into the volume, not next to the unit
install.ini
```

## The labels decide what a job costs

`runs-on:` in a workflow matches a label, and a label names an image. Register
without choosing and the runner asks for `ubuntu-latest` and its siblings —
images built to look like a GitHub worker, measured in gigabytes, pulled on the
first job. The `.env` names small ones instead:

```ini
GITEA_RUNNER_LABELS=alpine:docker://docker.io/library/alpine:3
```

A workflow then says `runs-on: alpine`. Labels are read **once**, at
registration: changing them later means deleting `.runner` from the volume and
letting it register again with a fresh token.

## Two settings that are not upstream defaults

`config.yaml` here differs from the shipped example in two places, both
measured rather than guessed:

- **`cache.dir: /data/cache`.** The default is `$HOME/.cache/actcache`, which
  lives inside the image — and the unit mounts that read-only. The runner then
  starts, answers its health check, and logs `cannot init cache server, it will
  be disabled`. Healthy and half working, which is the failure this repository
  keeps running into. Pointing it at the volume fixes it and keeps the cache
  across restarts.
- **`metrics.enabled: true`.** Off upstream. `Notify=healthy` needs a
  `HealthCmd` (rule 14 of the conventions), and `/healthz` on `127.0.0.1:9101`
  is the only thing the runner serves. It stays on loopback: the port is not
  published and there is no authentication in front of it.

## Update

The project moved: it used to be published as `gitea/act_runner`, which stopped
at `0.6.1`, and is now `gitea/runner` on its own versioning. It also lives on
`gitea.com` and not on GitHub, so `install.ini` compares against the registry
instead of a release page that does not exist.

## Backup

Worth little: the volume holds a registration you can recreate in a minute and
a cache that exists to be thrown away. Restoring the `.runner` file onto a
different machine gives two runners claiming one registration.

## Remove

Gitea keeps the runner in its list either way — delete it there too, under
Site Administration → Actions → Runners.

## Credits

[gitea/runner](https://gitea.com/gitea/runner) — MIT

[Official documentation](https://docs.gitea.com/usage/actions/overview)

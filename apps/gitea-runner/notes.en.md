It asks for the registration token. Get it from Gitea, in **Site Administration → Actions → Runners → Create new Runner**, or:

```bash
podman exec -u git gitea gitea actions generate-runner-token
```

The token is spent on the first registration; after that the runner uses the `.runner` file in its volume.

Labels are read **once**, at registration: the `.env` names a small image (`GITEA_RUNNER_LABELS=alpine:docker://docker.io/library/alpine:3`, so a workflow says `runs-on: alpine`). To change them, delete `.runner` from the volume and register again with a fresh token. On removal, delete the runner in Gitea too.

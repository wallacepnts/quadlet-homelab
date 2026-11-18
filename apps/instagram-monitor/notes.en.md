After the install, run the setup wizard once; it creates the config and `.env` inside the data volume:

```bash
podman run -it --rm \
  -v ~/.config/containers/volumes/instagram-monitor/data:/data:Z \
  -v ~/.config/containers/volumes/instagram-monitor/session:/home/instagram/.config/instaloader:Z \
  --user 10001:10001 \
  docker.io/misiektoja/instagram-monitor:v4.0.2 --setup
```

It asks for the usernames to watch, the notifications and, optionally, an Instagram session (stories, private accounts). Then `systemctl --user restart instagram-monitor`. To run it again, stop the service first. No Podman secrets are used: the tool reads its own `/data/.env`.

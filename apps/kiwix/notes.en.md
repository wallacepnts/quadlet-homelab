**It does not start empty.** With no `.zim` in the volume it exits, so the install leaves it stopped. Put a library in `~/.config/containers/volumes/kiwix/data` and start it:

```bash
cd ~/.config/containers/volumes/kiwix/data
wget https://download.kiwix.org/zim/wikipedia/wikipedia_pt_all_nopic_2026-07.zim
podman unshare chown 1001:1001 *.zim
systemctl --user start kiwix
```

Catalogue: [library.kiwix.org](https://library.kiwix.org). Every `.zim` in the folder is served; a new one only needs a restart. The libraries are not in the backup (they can be downloaded again).

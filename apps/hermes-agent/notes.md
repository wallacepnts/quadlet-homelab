Open `http://<host-ip>:8642` or `https://hermes.<your-tailnet>.ts.net`.

### No memory limit

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

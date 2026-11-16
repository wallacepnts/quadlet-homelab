Abrir `http://<ip-do-host>:8642` ou `https://hermes.<your-tailnet>.ts.net`.

### Sem limite de memória

A unit define `PidsLimit=`, não `Memory=`. Limite de memória em unit rootless
exige o controlador de memória delegado ao gerenciador de usuário, e num host
onde ele não é, o container nem chega a ser criado:

```
memory.swap.max: no such file or directory
```

Pra saber se o seu host delega:

```bash
ls /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/ | grep memory.max
```

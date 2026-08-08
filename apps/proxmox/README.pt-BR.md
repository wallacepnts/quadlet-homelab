# Proxmox VE — Podman Quadlet (rootless)

**[🇺🇸 Read in English](./README.md)**

Deploy do [dockur/proxmox](https://github.com/dockur/proxmox) via Podman
Quadlet, usando a imagem oficial `docker.io/dockurr/proxmox`.

O Proxmox VE — a plataforma de gerenciamento de hypervisor — rodando como
container em vez de bare metal. Um lugar pra aprender a interface, ensaiar uma
mudança de cluster, ou conferir se um fluxo serve antes de dedicar uma máquina.

**Não** substitui uma instalação real de Proxmox. Tudo que ele gerencia vive
dentro de um container, num host que tem as próprias opiniões sobre
armazenamento e rede; tratar como laboratório, não como infraestrutura.

## Por que este não está em [`apps/vm`](../vm/)

Parece que pertence lá — mesmo autor, mesma família, interface web na 8006 —
mas três coisas o separam:

- **Ele roda privileged.** Os outros quatro recebem `/dev/kvm`, `/dev/net/tun`
  e `NET_ADMIN`; este recebe tudo. É exigência do upstream, não escolha (ver
  abaixo).
- **Ele roda systemd como PID 1** (`/sbin/init`), onde os outros rodam QEMU sob
  `tini`. Um sistema de init inteiro, com os serviços que o Proxmox espera em
  volta.
- **Ele é plataforma, não convidado.** No `apps/vm` você escolhe qual SO
  instalar; aqui não há o que escolher — você roda o Proxmox e cria VMs dentro.

As portas fecham o argumento: o `apps/vm` publica a 8006 duas vezes de
propósito, porque `vm-windows` e `vm-windows-arm` nunca rodam juntos. Proxmox e
Windows rodam, então este leva uma porta própria.

## Privileged é obrigatório, e foi medido

A unit traz `PodmanArgs=--privileged`. Isso não foi copiado do compose do
upstream — foi testado, porque a [regra 20](../../docs/pt-BR/convencoes.md) diz
pra nunca decidir hardening na fé. Sem a flag o entrypoint para antes de
começar:

```
❯ ERROR: Please start the container with the --privileged flag!
```

Com ela, a interface responde `200` na 8006. Não existe meio-termo a procurar:
a checagem é do próprio upstream, no topo do entrypoint.

**O que isso significa.** Container privileged abre mão do isolamento de sempre:
todas as capabilities, sem filtro seccomp, acesso a dispositivos. O Podman
rootless ainda embrulha tudo no seu user namespace, então não é root no host —
mas é o mais perto disso que qualquer coisa neste repositório chega. Nada mais
aqui roda assim, tirando o Gluetun do [media-stack](../media-stack/), e aquele
pelo menos tem uma função estreita.

Subir quando quiser o Proxmox; não deixar rodando quando não quiser.

## Requisitos

- **KVM no host**, se a intenção for subir VMs dentro do Proxmox:

  ```bash
  ls -l /dev/kvm                          # precisa existir
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo ok
  ```

  A interface sobe sem KVM; as VMs que ela gerencia, não.

- **Pelo menos 2 GB de RAM** pro Proxmox em si, mais o que os convidados
  levarem.
- **32 GB de disco livre**, segundo o upstream. O pool de armazenamento é um
  volume aqui, então cresce dentro da sua home.

## Arquitetura

Um container só. Dois volumes, que é o que torna um restart sobrevivível:

| Volume | Guarda |
| --- | --- |
| `/var/lib/vz` | o pool de armazenamento — discos de VM, ISOs, backups |
| `/var/lib/pve-cluster` | o banco de configuração |

O hostname é fixo em `pve` (`HostName=pve`), porque o Proxmox grava o próprio
hostname na config de cluster e um que muda confunde ele.

A interface web é **HTTPS com certificado autoassinado**, na porta **8010** do
host mapeada pra 8006 lá dentro. HTTP puro naquela porta responde `301`, e é
por isso que o healthcheck usa `curl -k https://` — uma checagem em `http`
passaria no redirect sem nunca provar que a interface está de pé.

## Arquivos

```
proxmox.container   # unit principal
install.ini         # a receita da senha de root + o override de upstream
```

## Instalação

```bash
python3 install.py proxmox            # dry-run: mostra o que vai fazer
python3 install.py proxmox --apply
```

Depois abrir `https://<ip-do-host>:8010` — aceitar o certificado autoassinado, e
entrar como `root` com:

```bash
podman secret inspect --showsecret proxmox-root-password
```

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/proxmox/proxmox.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/proxmox/{data,config}

# 3. Secret — a senha de root da interface web
podman secret create proxmox-root-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 4. Subir
systemctl --user daemon-reload
systemctl --user start proxmox
```

</details>

## Segurança

Duas coisas se somam aqui, e vale ler juntas.

**O container é privileged**, como acima — a postura mais larga do repositório.

**A interface está na tailnet por padrão**, seguindo a convenção daqui. Ela até
tem login de verdade, diferente dos viewers do [`apps/vm`](../vm/), e o
`install.ini` troca a senha padrão `root` do upstream por uma gerada. Mas
tailnet não é autenticação: ela estreita quem pode bater na porta, não quem
entra.

Se essa troca não for o que você quer, instalar com `--access local` — as
labels do tsdproxy são comentadas em vez de apagadas, então mudar de ideia
depois é um `--update` com outro modo
([Instalando e operando](../../docs/pt-BR/instalacao.md)).

## Hardening — o que não foi tentado

O `--privileged` torna quase toda a escada da
[regra 20](../../docs/pt-BR/convencoes.md) sem sentido: não adianta tirar
capability de um container que acabou de receber todas.

| Ajuste | Situação |
| --- | --- |
| `PodmanArgs=--privileged` | **obrigatório** — o entrypoint sai sem ele, medido |
| `PidsLimit=` | **não definido** — systemd mais os serviços do Proxmox, e sem medição pra basear um número |
| `ReadOnly=true` | **não tentado** — systemd como PID 1 precisa de `/run` gravável e mais |
| `User=` | **não tentado** — o PID 1 aqui é o `/sbin/init` |
| `DropCapability=ALL` | **inútil** — o `--privileged` devolve todas |

Se você medir um `PidsLimit` que funcione, registrar aqui com o número e como
chegou nele.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`9.2.9`), bump na mão
([regra 9](../../docs/pt-BR/convencoes.md)). Ler as notas de release do Proxmox
antes de subir uma minor: o banco de configuração em `/var/lib/pve-cluster` é
migrado no start, e esse não é um passo pra dar às cegas.

O `install.ini` carrega um override de `[upstream]` porque a imagem é
`dockurr/proxmox` (com dois erres) e o repositório é `dockur/proxmox` — sem
essa linha o `updates.py` deriva o nome errado e reporta que não há releases.

## Backup & recuperação

```bash
systemctl --user stop proxmox
tar -czf proxmox-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes proxmox
systemctl --user start proxmox
```

A frio de propósito: o `/var/lib/pve-cluster` é um banco SQLite vivo, e copiar
com o Proxmox escrevendo dá um arquivo que só se revela corrompido na hora de
restaurar. O pool de armazenamento vai no mesmo tarball, então o tamanho segue
as VMs que você criou lá dentro.

## Comandos úteis

```bash
systemctl --user status proxmox
podman logs -f proxmox
podman exec proxmox pvecm status          # estado do cluster, por dentro
podman exec proxmox df -h /var/lib/vz     # quanto o pool cresceu
```

## Créditos

Deploy Quadlet baseado no [dockur/proxmox](https://github.com/dockur/proxmox)
(MIT). O Proxmox VE é produto da Proxmox Server Solutions GmbH; este
repositório não tem afiliação nem endosso deles.

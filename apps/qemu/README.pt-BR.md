# QEMU — Podman Quadlet (rootless)

**[🇺🇸 Read in English](./README.md)**

Deploy do [qemus/qemu](https://github.com/qemus/qemu) via Podman Quadlet,
usando a imagem oficial `docker.io/qemux/qemu`.

Uma VM sob QEMU/KVM embrulhada num container, com a tela servida no navegador.
Escolhe um SO de uma lista de 23, ou aponta pra qualquer ISO, e ele se instala
no primeiro boot. Um lugar pra experimentar distro, reproduzir bug em outro
kernel, ou manter uma máquina descartável.

É o mesmo motor sobre o qual o [Windows](../windows/) roda — aquela imagem é
esta aqui com um instalador de Windows por cima. Este serve pra quando o
convidado não é Windows.

## Requisitos

Além do Podman rootless de sempre:

- **KVM no host.** O `/dev/kvm` precisa existir e ser legível e gravável pelo
  usuário que roda o Podman. Sem ele a VM ou recusa subir, ou cai em emulação
  por software, que é inutilizável de tão lenta.

  ```bash
  ls -l /dev/kvm                          # precisa existir
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo ok
  grep -oE 'vmx|svm' /proc/cpuinfo | head -1   # VT-x ou AMD-V, ligado na firmware
  ```

  O `/dev/kvm` existir é o teste melhor: quem cria esse device é o módulo do
  kernel, então a presença dele prova que a virtualização está de fato ligada,
  não só presente na CPU. Se estiver `crw-rw----` e for de `root:kvm`, entrar
  no grupo `kvm` e relogar.

- **`/dev/net/tun`**, que o container usa pra rede da VM.
- **Disco.** O `DISK_SIZE` padrão aqui é 32 GB (o upstream usa 64). A imagem
  cresce sob demanda, mas mora no volume, dentro da sua home.
- **RAM.** O `RAM_SIZE` fica reservado pela vida inteira da VM, não é
  emprestado sob demanda. Os 2 GB do padrão são 2 GB que o host não tem mais.

## Arquitetura

Um container só rodando QEMU. Um volume, `/storage`, com o disco virtual e a
mídia baixada. A tela fica na **8007** do host, mapeada pra 8006 lá dentro — a
8006 já é do [Windows](../windows/), que é a mesma imagem por baixo.

O primeiro start baixa o SO escolhido e sobe o instalador dele, e é por isso
que estão aqui o `TimeoutStartSec=600` e os três minutos de
`HealthStartPeriod`.

## Arquivos

```
qemu.container      # unit principal
.env.example        # SO, RAM, núcleos, tamanho do disco
install.ini         # a pergunta do BOOT + o override de upstream
```

## Instalação

```bash
python3 install.py qemu            # dry-run: mostra o que vai fazer
python3 install.py qemu --apply
```

Ele pergunta qual SO instalar e depois baixa a imagem com o progresso do podman
na tela — ver [Instalando e operando](../../docs/pt-BR/instalacao.md).

Depois abrir `http://<ip-do-host>:8007` e tocar o instalador.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/qemu/qemu.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/qemu/storage
mkdir -p ~/.config/containers/env

# 3. Ambiente — editar BOOT pro SO que você quer
wget -O ~/.config/containers/env/qemu.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/qemu/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start qemu
```

</details>

## Escolhendo o SO

O `install.py` pergunta na primeira instalação. Responder com o número, com o
próprio valor, ou Enter pro padrão. Só vale no **primeiro** start — depois o SO
está instalado e o valor nunca mais é lido; mudar de ideia significa apagar o
volume.

| Valor | SO | Download |
| --- | --- | --- |
| `alpine` | Alpine Linux | 60 MB |
| `suse` | openSUSE | 1.0 GB |
| `arch` | Arch Linux | 1.2 GB |
| `zima` | ZimaOS | 1.4 GB |
| `tails` | Tails | 1.5 GB |
| `rocky` | Rocky Linux | 2.1 GB |
| `alma` | Alma Linux | 2.2 GB |
| `mx` | MX Linux | 2.2 GB |
| `fedora` | Fedora | 2.3 GB |
| `nixos` | NixOS | 2.4 GB |
| `cachy` | CachyOS | 2.6 GB |
| `mint` | Linux Mint | 2.8 GB |
| `ubuntus` | Ubuntu Server | 3.0 GB |
| `debian` | Debian | 3.3 GB |
| `gentoo` | Gentoo | 3.6 GB |
| `slack` | Slackware | 3.7 GB |
| `kali` | Kali Linux | 3.8 GB |
| `zorin` | Zorin OS | 3.8 GB |
| `xubuntu` | Xubuntu | 4.0 GB |
| `manjaro` | Manjaro | 4.1 GB |
| `kubuntu` | Kubuntu | 4.4 GB |
| `ubuntu` | Ubuntu Desktop | 6.0 GB |
| `centos` | CentOS | 7.0 GB |

**O padrão aqui é `alpine`**, onde o upstream usa `mint`. Com 60 MB ele prova o
caminho inteiro — KVM, tun, disco, viewer — em cerca de um minuto, em vez de
2,8 GB de download antes de você descobrir se alguma coisa funciona.

O `BOOT` também aceita a URL de qualquer ISO, e é por isso que uma resposta
fora da lista é aceita como veio em vez de recusada:

```bash
BOOT=https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-virt-3.19.1-x86_64.iso
```

## Segurança — ler antes de pôr na tailnet

**O viewer da 8007 não tem login.** Quem abre aquela URL tem o console, o
teclado e o mouse da VM. A unit sai com as labels do tsdproxy ligadas, seguindo
o padrão deste repositório, o que significa que todo dispositivo da sua tailnet
— e tudo que roda neles — alcança aquilo.

Diferente do [Windows](../windows/), aqui não existe uma segunda porta com
senha: não há RDP nem conta a proteger. O console é a superfície inteira.

Se essa troca não for o que você quer, instalar com `--access local` — as
labels do tsdproxy são comentadas em vez de apagadas, então mudar de ideia
depois é um `--update` com outro modo
([Instalando e operando](../../docs/pt-BR/instalacao.md)).

Vale dizer com todas as letras: este container recebe `/dev/kvm`,
`/dev/net/tun` e `NET_ADMIN`, e roda o SO que você apontou. É uma superfície de
confiança grande por construção, não por descuido.

## Hardening — o que não foi tentado

Só o `PidsLimit=512` além dos padrões, pelos mesmos motivos do
[Windows](../windows/):

| Ajuste | Situação |
| --- | --- |
| `PidsLimit=512` | ligado — QEMU mais os processos auxiliares do entrypoint |
| `AddCapability=NET_ADMIN` | exigido pelo upstream, pra rede tun da VM |
| `ReadOnly=true` | **não tentado** — o entrypoint escreve em `/run` e descompacta mídia |
| `User=` | **não tentado** — o QEMU é iniciado como root pelo entrypoint |
| `DropCapability=ALL` | **não tentado** — não medido, e uma lista errada aparece como VM que sobe sem rede, não como erro claro |

Testar qualquer um significa uma instalação completa de SO por tentativa. O
`alpine` torna isso bem mais barato do que é no Windows, então se você medir
algum, registrar aqui com o erro.

Memória não tem teto na unit. Um teto precisa passar do `RAM_SIZE` com folga
pro próprio QEMU — `Memory=4G` pro `RAM_SIZE=2G` do padrão.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`7.44`), bump na mão
([regra 9](../../docs/pt-BR/convencoes.md)). A tag é do invólucro do QEMU, não
do convidado: subir ela atualiza o emulador e o viewer e deixa o SO instalado
em paz.

O `install.ini` carrega um override de `[upstream]` porque o usuário no Docker
Hub é `qemux` (com x) e a org no GitHub é `qemus` (com s) — sem essa linha o
`updates.py` deriva o nome errado e reporta que não há releases.

## Backup & recuperação

```bash
systemctl --user stop qemu
tar -czf qemu-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes qemu
systemctl --user start qemu
```

A frio de propósito — copiar o disco de uma VM ligada dá um arquivo que só se
revela corrompido na hora de restaurar. O arquivo é o disco virtual inteiro,
então reparar no tamanho.

## Comandos úteis

```bash
systemctl --user status qemu
podman logs -f qemu                 # o progresso da instalação está aqui
podman exec qemu df -h /storage     # quanto o disco cresceu de fato
```

## Créditos

Deploy Quadlet baseado no [qemus/qemu](https://github.com/qemus/qemu) (MIT).

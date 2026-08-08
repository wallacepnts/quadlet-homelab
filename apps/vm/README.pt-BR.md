# VM — Podman Quadlet (rootless)

**[🇺🇸 Read in English](./README.md)**

Sistemas operacionais inteiros em VMs, cada um no seu container, com a tela
servida no navegador. Três convidados, um motor só.

| Unit | Convidado | Imagem | Viewer | Também |
| --- | --- | --- | --- | --- |
| `vm-qemu` | qualquer Linux, ou a sua ISO | [qemus/qemu](https://github.com/qemus/qemu) | 8007 | — |
| `vm-windows` | Windows 11 até 2000 | [dockur/windows](https://github.com/dockur/windows) | 8006 | RDP 3389 |
| `vm-macos` | macOS 11 a 26 | [dockur/macos](https://github.com/dockur/macos) | 8008 | VNC 5900 |
| `vm-windows-arm` | Windows ARM64, num host ARM | [dockur/windows-arm](https://github.com/dockur/windows-arm) | 8006 | RDP 3389 |
| `vm-zima` | ZimaOS, interface de NAS | [dockur/zima](https://github.com/dockur/zima) | 8012 | UI web 8011 |
| `vm-chromeos` | ChromeOS Flex | [dockur/chromeos](https://github.com/dockur/chromeos) | 8013 | VNC 5901 |

Os três são o mesmo motor: `dockur/windows` e `dockur/macos` são ambos
construídos `FROM qemux/qemu`, com um instalador por cima. É por isso que todos
querem a porta 8006 por dentro, e por isso que estão numa pasta só em vez de
três.

Leve os que quiser — nada aqui exige o resto:

```bash
python3 install.py vm-qemu --apply          # só o de Linux
python3 install.py vm --apply               # os três
```

## Requisitos

**Escolher a unit que casa com o host.** O KVM só acelera convidado da mesma
arquitetura do host, então quem decide é o convidado, não a imagem do
container. As quatro imagens são multi-arch, e esse multi-arch é sobre em qual
*host* elas rodam, não qual Windows elas instalam:

| Host | Windows | Linux | macOS |
| --- | --- | --- | --- |
| x86_64 | `vm-windows` | `vm-qemu` | `vm-macos` |
| ARM64 | `vm-windows-arm` | [qemus/qemu-arm](https://github.com/qemus/qemu-arm/), não empacotado aqui | — |

O `vm-windows` e o `vm-windows-arm` são imagens de fato diferentes — mesma tag,
digests distintos — e publicam as mesmas portas de propósito, porque um host é
de uma arquitetura ou da outra e os dois nunca rodam juntos. É pra isso que
serve a linha `# check: ignore ports` na unit ARM.

O macOS não tem caminho ARM nenhum: o `dockurr/macos` é só `amd64`, e ele emula
um Mac Intel, que é outra máquina em relação ao Apple Silicon.

**Nada do lado ARM foi testado aqui** — o host deste repositório é x86_64,
então o `vm-windows-arm` foi escrito a partir da documentação do upstream, não
medido. Tratar como ponto de partida, e registrar o que descobrir.

Comuns aos três, além do Podman rootless de sempre:

- **KVM no host.** O `/dev/kvm` precisa existir e ser legível e gravável pelo
  usuário que roda o Podman. Sem ele a VM ou recusa subir, ou cai em emulação
  por software, que é inutilizável de tão lenta.

  ```bash
  ls -l /dev/kvm                          # precisa existir
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo ok
  ```

  O `/dev/kvm` existir é o teste melhor: quem cria esse device é o módulo do
  kernel, então a presença dele prova que a virtualização está de fato ligada,
  não só presente na CPU. Se estiver `crw-rw----` e for de `root:kvm`, entrar
  no grupo `kvm` e relogar.

- **`/dev/net/tun`**, pra rede das VMs.
- **RAM.** O `RAM_SIZE` fica reservado pela vida inteira da VM, não é
  emprestado sob demanda. O que você der é RAM que o host não tem mais.
- **Disco.** As imagens crescem sob demanda mas moram no volume, dentro da sua
  home. O Windows fica em torno de 20 GB, o macOS quer uns 40.

**O macOS pede mais um: AVX2 na CPU.** É requisito duro, não nota de
desempenho — Intel Haswell (Core de 4ª geração) ou AMD Zen (Ryzen 1000) pra
cima:

```bash
grep -qo avx2 /proc/cpuinfo && echo ok || echo "sem AVX2 — o macOS não roda"
```

## Arquitetura

Cada unit roda QEMU com um volume em `/storage`, guardando o disco virtual
daquele convidado e a mídia baixada. Os volumes não se misturam:
`volumes/vm/{qemu,windows,macos}`.

Não existe `Requires=` entre elas — são alternativas, não uma stack. Rodar duas
ao mesmo tempo funciona, se o host tiver RAM.

O primeiro start de qualquer uma baixa vários GB e roda um instalador, e é por
isso que todas trazem `TimeoutStartSec=600` e `HealthStartPeriod` longos. O
`install.py` segue o log do container enquanto o systemd espera, então essa
espera é visível em vez de um terminal com cara de travado.

## Arquivos

```
vm-qemu.container       vm-qemu.env.example
vm-windows.container    vm-windows.env.example
vm-macos.container      vm-macos.env.example
vm-windows-arm.container  vm-windows-arm.env.example
vm-zima.container       vm-zima.env.example
vm-chromeos.container   vm-chromeos.env.example
install.ini             # perguntas por unit, o secret do Windows, overrides de upstream
```

## Instalação

```bash
python3 install.py vm            # dry-run: mostra o que vai fazer
python3 install.py vm --apply    # os três
```

Instalar a pasta escreve as três units e para sem subir nada — sem uma unit
principal única ele não adivinha qual convidado você quer:

```bash
systemctl --user start vm-qemu        # ou vm-windows, ou vm-macos
```

Nomear uma unit instala e sobe só aquela. De qualquer jeito as units caem em
`systemd/vm/`, então acrescentar outra depois é o mesmo comando de novo.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit que você quer (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd/vm
wget -P ~/.config/containers/systemd/vm/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vm/vm-qemu.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/vm/qemu/storage
mkdir -p ~/.config/containers/env

# 3. Ambiente
wget -O ~/.config/containers/env/vm-qemu.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vm/vm-qemu.env.example

# 4. Só pro Windows — a senha de RDP da conta `Docker`
podman secret create vm-windows-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 5. Subir
systemctl --user daemon-reload
systemctl --user start vm-qemu
```

</details>

## Escolhendo o convidado

O `install.py` pergunta uma vez por unit, na primeira instalação. Só vale ali —
depois o SO está baixado e instalado, e o valor nunca mais é lido. Mudar de
ideia significa apagar o volume daquele convidado.

### `vm-qemu` — `BOOT`

23 distribuições Linux, do Alpine com 60 MB ao CentOS com 7 GB:

`alpine` · `suse` · `arch` · `zima` · `tails` · `rocky` · `alma` · `mx` ·
`fedora` · `nixos` · `cachy` · `mint` · `ubuntus` · `debian` · `gentoo` ·
`slack` · `kali` · `zorin` · `xubuntu` · `manjaro` · `kubuntu` · `ubuntu` ·
`centos`

**O padrão aqui é `alpine`**, onde o upstream usa `mint`. Com 60 MB ele prova o
caminho inteiro — KVM, tun, disco, viewer — em cerca de um minuto, em vez de
2,8 GB de download antes de você descobrir se alguma coisa funciona.

O `BOOT` também aceita a URL de qualquer ISO, e é por isso que uma resposta
fora da lista é aceita como veio em vez de recusada.

### `vm-windows` — `VERSION` e `LANGUAGE`

| Valor | Edição | Download |
| --- | --- | --- |
| `11` | Windows 11 Pro | 7,9 GB |
| `11l` | Windows 11 LTSC | 4,7 GB |
| `11e` | Windows 11 Enterprise | 6,6 GB |
| `10` | Windows 10 Pro | 5,7 GB |
| `10l` | Windows 10 LTSC | 4,6 GB |
| `10e` | Windows 10 Enterprise | 5,2 GB |
| `2025` `2022` `2019` `2016` `2012` `2008` `2003` | Windows Server | 3,0–7,6 GB |
| `tiny11` | Tiny11 | 5,3 GB |
| `core11` | Tiny11 Core | 3,0 GB |
| `tiny10` | Tiny10 | 3,6 GB |
| `8e` | Windows 8.1 Enterprise | 3,7 GB |
| `7u` | Windows 7 Ultimate | 3,1 GB |
| `vu` | Windows Vista Ultimate | 3,0 GB |
| `xp` | Windows XP Professional | 0,6 GB |
| `2k` | Windows 2000 Professional | 0,4 GB |
| `reactos` | ReactOS | 0,1 GB |

O `LANGUAGE` aceita qualquer um de 33 nomes em inglês (`German`, `Portuguese`,
…). Pra português do Brasil, escolher `Portuguese` e definir `REGION=pt-BR` e
`KEYBOARD=pt-BR` no `.env`.

**O `xp` e o `2003` não funcionam hoje.** O upstream fixa um controlador
virtio-blk pra eles:

```bash
# dockur/windows, src/install.sh
"winxpx"* | "win2003"* )
  writeState "type" "blk"
```

enquanto o `getDriverFolder()` do `src/define.sh` não tem entrada abaixo do
Vista — ou seja, não existe driver virtio pra instalar. O setup termina, e aí o
sistema instalado para em **STOP 0x7B INACCESSIBLE_BOOT_DEVICE**, porque não
tem driver pro disco em que foi instalado. Definir `DISK_TYPE` não ajuda: a
escrita hardcoded roda a cada start e sobrescreve. Vista pra cima vai bem.

### `vm-windows-arm` — `VERSION` e `LANGUAGE`

Lista mais curta que a do x64, porque essas são as únicas edições de Windows
que chegaram a ter build ARM64 — sem XP, Vista, 7 ou Server:

| Valor | Edição | Download |
| --- | --- | --- |
| `11` | Windows 11 Pro | 7,5 GB |
| `11l` | Windows 11 LTSC | 4,7 GB |
| `11e` | Windows 11 Enterprise | 4,3 GB |
| `10` | Windows 10 Pro | 3,5 GB |
| `10l` | Windows 10 LTSC | 4,1 GB |
| `10e` | Windows 10 Enterprise | 3,4 GB |
| `tiny11` | Tiny11 | 5,1 GB |
| `core11` | Tiny11 Core | 3,0 GB |

O `LANGUAGE` funciona igual ao da unit x64.

### `vm-macos` — `VERSION`

| Valor | Versão | Nome |
| --- | --- | --- |
| `15` | macOS 15 | Sequoia |
| `14` | macOS 14 | Sonoma |
| `13` | macOS 13 | Ventura |
| `12` | macOS 12 | Monterey |
| `11` | macOS 11 | Big Sur |
| `26` | macOS 26 | Tahoe |

O `26` é aceito mas o upstream desaconselha — roda muito devagar, por motivo
que eles dizem não ter identificado.

**O macOS é só em hardware Apple.** O upstream diz com todas as letras:

> *ao instalar o macOS da Apple, você precisa aceitar o contrato de licença de
> usuário final deles, que não permite instalação em hardware não oficial.
> Então rode este container apenas em hardware vendido pela Apple; qualquer
> outro uso será uma violação dos termos e condições.*

É mais duro que o caso do Windows: lá você compra uma licença e pronto, aqui o
EULA da Apple não oferece caminho nenhum pra hardware que não seja deles. O
software vai rodar; se você tem permissão pra rodar é uma pergunta separada, e
a resposta é sua.

Diferente do Windows, a instalação do macOS **não** é desassistida: você
conduz. Os dois passos que as pessoas erram: apagar o maior disco `Apple Inc.
VirtIO Block Media` no `Disk Utility` antes de o instalador aceitá-lo, e
escolher `Set Up Later` e depois `Skip` na tela do `Apple ID`.

### `vm-zima` — não há o que escolher

O ZimaOS é o convidado, e não existe versão pra escolher: a imagem instala a
release que ela traz. Diferente dos outros, o que você usa no dia a dia não é o
viewer e sim **a interface web do próprio ZimaOS**, encaminhada do convidado:

| Porta no host | O quê |
| --- | --- |
| `8011` | a interface do ZimaOS — a que você de fato usa |
| `8012` | o viewer do QEMU, pro primeiro boot e pra quando o convidado não sobe |

Esse encaminhamento é a razão de esta unit existir: o `vm-qemu` também instala
ZimaOS (`BOOT=zima`), mas só te dá uma tela. Esta aqui publica os serviços que
o convidado roda.

A imagem também expõe a **445** pra SMB, que não é publicada aqui: o Podman
rootless não binda porta abaixo de 1024 sem baixar o
`net.ipv4.ip_unprivileged_port_start`, e o compose do próprio upstream também
não publica. O [netbootxyz](../netbootxyz/README.pt-BR.md) documenta essa
mudança de sysctl, se você decidir que quer.

### `vm-chromeos` — `VERSION`, e as duas coisas que só ele tem

O ChromeOS Flex acompanha um canal, não uma versão:

| Valor | Canal | Cadência |
| --- | --- | --- |
| `stable` | Stable | ~4 semanas |
| `ltc` | Long-Term Channel | ~6 meses |
| `ltr` | Long-Term Release | ~18 meses |
| `beta` | Beta | ~semanal |

**É a única unit daqui com login no viewer.** O `PROTECT=Y` põe basic auth HTTP
na frente da porta 8006, com a senha gerada pelo `install.py`:

```bash
podman secret inspect --showsecret vm-chromeos-password
```

O padrão do upstream é `Docker` / `admin`; o `.env` define o usuário e o secret
define a senha. As outras units desta pasta não têm essa opção — os viewers
delas ficam abertos pra quem alcançar.

**Também é a única que usa a GPU.** A unit monta `/dev/dri` e acrescenta uma
regra de cgroup pro major do DRM, que é o que o upstream exige pro backend
VirGL do QEMU:

```ini
Volume=/dev/dri:/dev/dri:rw
PodmanArgs=--device-cgroup-rule=c 226:* rwm
```

Sem `:Z` nesse mount, de propósito — reetiquetar os device nodes do host não é
coisa que container deva fazer. Conferir se o seu usuário alcança o render node
antes de esperar aceleração:

```bash
[ -r /dev/dri/renderD128 ] && [ -w /dev/dri/renderD128 ] && echo ok
```

Se não alcançar, entrar nos grupos `render` e `video`. Sem um node utilizável o
container cai em renderização por software, que o upstream mede em 3–15 fps —
funciona, mas é sofrido.

**Só x86_64.** O `dockurr/chromeos` não publica imagem `arm64`, a segunda unit
daqui nessa situação, depois do `vm-macos`.

## Apps do Windows no desktop Linux (WinApps)

O [WinApps](https://github.com/winapps-org/winapps) desenha programas do
Windows como janelas comuns ao lado das do Linux, usando esta VM de backend e o
FreeRDP de renderizador. Ele se divide em dois, e só uma metade mora aqui.

**A metade container é o `vm-windows`, já.** Mesma imagem `dockur/windows`, RDP
publicado na 3389 em TCP e UDP, senha do Windows já como secret do podman.
Comparando o `compose.yaml` do upstream com esta unit, faltavam dois mounts, e
os dois estão no lugar agora:

| mount | pra que serve |
| --- | --- |
| `oem/` → `/oem` | o dockur roda o `/oem/install.bat` uma vez, depois que o Windows instala. Ele importa o `RDPApps.reg` — a mudança de registro que faz o RDP entregar janela por aplicativo em vez do desktop inteiro. Sem isso não existe WinApps. |
| `shared/` → `/shared` | aparece dentro do Windows como `\\host.lan\Data`, pra levar arquivo de um lado pro outro |

Os arquivos do `oem/` **não** ficam neste repositório — são baixados direto do
WinApps, uma vez, antes do primeiro boot:

```bash
mkdir -p ~/.config/containers/volumes/vm/windows/oem
for f in install.bat RDPApps.reg Container.reg NetProfileCleanup.ps1 TimeSync.ps1; do
  wget -O ~/.config/containers/volumes/vm/windows/oem/$f https://raw.githubusercontent.com/winapps-org/winapps/main/oem/$f
done
```

Não são versionados de propósito. O `LICENSE.md` do WinApps diz que as partes
herdadas do projeto original "não são software livre […] All Rights Reserved
by the original author", que a maioria do resto é AGPLv3, e manda "consultar
cada arquivo pela licença dele" — e nenhum desses cinco traz nota nenhuma.
Baixar do repositório deles deixa essa questão onde ela pertence.

**Ele precisa estar lá antes do primeiro boot.** O dockur roda o hook do `/oem`
uma única vez, como parte da instalação do Windows; pôr os arquivos depois não
faz nada, e o conserto é apagar o volume de storage e instalar o Windows de
novo.

### Uma diferença proposital em relação ao upstream

O upstream monta a **sua home inteira** como `/shared`. Esta unit monta uma
pasta `shared/` dedicada, porque neste host a home guarda o
`~/.config/containers/secrets/` — a senha de cada serviço, em texto puro. Uma
VM Windows roda software Windows arbitrário; dar a ela leitura e escrita nesse
diretório não é uma troca que este repositório faz por padrão.

Se quiser o mount largo mesmo assim, é uma linha na unit:
`Volume=%h:/shared:z`.

### A metade host não é Quadlet

O WinApps em si é um script shell, um conjunto de `.desktop` e o FreeRDP 3+,
instalados no host pelo `installer.sh` do upstream, com configuração em
`~/.config/winapps/winapps.conf`. É a mesma categoria do Tailscale
([regra 21](../../docs/pt-BR/convencoes.md)): ele precisa estar *na* sessão
gráfica, não num container.

No openSUSE MicroOS isso significa o FreeRDP entrando por
`transactional-update`, que exige reboot — então é decisão a tomar de
propósito, não passo pra rodar no meio de uma instalação.

## Segurança — ler antes de pôr qualquer uma na tailnet

**Quase nenhum viewer tem login.** Quem abre a URL tem a tela, o teclado e o
mouse daquela VM, já logado. Todas saem com as labels do tsdproxy ligadas,
seguindo o padrão deste repositório, o que significa que todo dispositivo da
sua tailnet — e tudo que roda neles — alcança.

O `vm-chromeos` é a exceção: ele suporta `PROTECT=Y`, e a unit liga. As outras
cinco não têm equivalente — a opção não existe nas imagens delas.

O Windows tem uma segunda porta com senha: o RDP na 3389, onde o padrão do
upstream é o usuário `Docker` com a senha literal `admin` e o `install.ini`
troca por uma gerada:

```bash
podman secret inspect --showsecret vm-windows-password
```

Isso protege a 3389. Não faz nada pelo viewer.

Se essa troca não for o que você quer, instalar com `--access local` — as
labels do tsdproxy são comentadas em vez de apagadas, então mudar de ideia
depois é um `--update` com outro modo
([Instalando e operando](../../docs/pt-BR/instalacao.md)).

Vale dizer com todas as letras: estes containers recebem `/dev/kvm`,
`/dev/net/tun` e `NET_ADMIN`, e rodam sistemas operacionais inteiros que você
não auditou. É uma superfície de confiança grande por construção, não por
descuido.

## Hardening — o que não foi tentado

Só o `PidsLimit=512` além dos padrões, nas três:

| Ajuste | Situação |
| --- | --- |
| `PidsLimit=512` | ligado — QEMU mais os processos auxiliares do entrypoint |
| `AddCapability=NET_ADMIN` | exigido pelo upstream, pra rede tun das VMs |
| `ReadOnly=true` | **não tentado** — o entrypoint escreve em `/run` e descompacta mídia |
| `User=` | **não tentado** — o QEMU é iniciado como root pelo entrypoint |
| `DropCapability=ALL` | **não tentado** — não medido, e uma lista errada aparece como VM que sobe sem rede, não como erro claro |

Testar qualquer um significa uma instalação completa de SO por tentativa. O
`vm-qemu` com `alpine` torna isso bem mais barato que nos outros dois — se você
medir algum, registrar aqui com o erro.

Memória não tem teto. Um teto precisa passar do `RAM_SIZE` com folga pro
próprio QEMU.

## Auto-update

Sem `AutoUpdate=` — tags explícitas, bump na mão
([regra 9](../../docs/pt-BR/convencoes.md)). Cada tag é a versão do
*container*, não a do convidado: subir ela atualiza o QEMU e os scripts
auxiliares e deixa o SO instalado em paz.

O `install.ini` carrega overrides de `[upstream]` pra dois dos três, porque os
nomes das imagens não batem com os dos repositórios — `dockurr` tem dois erres,
e a org do QEMU é `qemus` com s. Sem essas linhas o `updates.py` deriva os
nomes errados e não acha nada.

## Backup & recuperação

Por convidado, e a frio de propósito — copiar o disco de uma VM ligada dá um
arquivo que só se revela corrompido na hora de restaurar:

```bash
systemctl --user stop vm-windows
tar -czf vm-windows-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes/vm windows
systemctl --user start vm-windows
```

Reparar no tamanho: são discos virtuais inteiros, dezenas de gigabytes cada —
outra conversa em relação a todos os outros backups deste repositório.

## Comandos úteis

```bash
podman ps --filter "name=vm-"
systemctl --user status vm-qemu
podman logs -f vm-windows                 # o progresso da instalação está aqui
podman exec vm-macos df -h /storage       # quanto o disco cresceu de fato
```

## Créditos

Deploy Quadlet baseado no [qemus/qemu](https://github.com/qemus/qemu), no
[dockur/windows](https://github.com/dockur/windows) e no
[dockur/macos](https://github.com/dockur/macos), todos MIT. Sem afiliação,
endosso ou patrocínio da Microsoft ou da Apple.

A integração com o WinApps segue o
[winapps-org/winapps](https://github.com/winapps-org/winapps); os arquivos do
`oem/` dele são baixados daquele repositório em vez de copiados pra este, pelo
motivo de licença explicado acima.

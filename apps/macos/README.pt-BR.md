# macOS — Podman Quadlet (rootless)

**[🇺🇸 Read in English](./README.md)**

Deploy do [dockur/macos](https://github.com/dockur/macos) via Podman Quadlet,
usando a imagem oficial `docker.io/dockurr/macos`.

Uma VM de macOS sob QEMU/KVM, embrulhada num container. Ela baixa a imagem de
recuperação da Apple no primeiro boot e você toca o instalador pelo navegador
na porta 8008, ou por VNC na 5900.

## Leia isto antes: só em hardware Apple

O projeto é open source e não distribui código da Apple. Mas o que ele instala
não é livre de termos, e o upstream diz isso com todas as letras:

> *ao instalar o macOS da Apple, você precisa aceitar o contrato de licença de
> usuário final deles, que não permite instalação em hardware não oficial.
> Então rode este container apenas em hardware vendido pela Apple; qualquer
> outro uso será uma violação dos termos e condições.*

É uma restrição mais dura que a do [Windows](../windows/): lá você compra uma
licença e pronto, aqui o EULA da Apple não oferece caminho nenhum pra hardware
que não seja deles. Se este host não é um Mac, instalar macOS nele viola esses
termos — o software vai rodar, e isso é uma pergunta separada de você ter
permissão pra rodar.

A unit está aqui porque o resto deste repositório documenta o que implanta. Se
vale implantar, a decisão é sua.

## Requisitos

Além do Podman rootless de sempre:

- **KVM no host**, igual ao [Windows](../windows/) e ao [QEMU](../qemu/):

  ```bash
  ls -l /dev/kvm                          # precisa existir
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo ok
  ```

- **AVX2 na CPU** — este é específico do macOS, e é requisito duro, não nota de
  desempenho. Intel Haswell (Core de 4ª geração) ou AMD Zen (Ryzen 1000) pra
  cima:

  ```bash
  grep -qo avx2 /proc/cpuinfo && echo ok || echo "sem AVX2 — não vai rodar"
  ```

- **`/dev/net/tun`**, pra rede da VM.
- **Disco.** O upstream pede 64 GB livres, e só o instalador quer uns 40 GB. É
  o convidado mais pesado do repositório.
- **RAM.** O `RAM_SIZE` fica reservado pela vida inteira da VM. O piso do
  upstream é 4 GB, que são 4 GB que o host não tem mais.

## Arquitetura

Um container só rodando QEMU. Um volume, `/storage`, com o disco virtual e a
imagem de recuperação baixada. Duas formas de entrar:

| Porta | O quê |
| --- | --- |
| `8008` | o viewer web — a tela no navegador (8006 dentro do container) |
| `5900/tcp`, `5900/udp` | VNC, pra um cliente de verdade |

A 8006 e a 8007 já são do [Windows](../windows/) e do [QEMU](../qemu/), que são
o mesmo motor por baixo — daí a 8008 aqui.

## Arquivos

```
macos.container     # unit principal
.env.example        # versão, RAM, núcleos, tamanho do disco
install.ini         # a pergunta da versão + o override de upstream
```

## Instalação

```bash
python3 install.py macos            # dry-run: mostra o que vai fazer
python3 install.py macos --apply
```

Ele pergunta qual macOS instalar e depois baixa a imagem com o progresso do
podman na tela — ver [Instalando e operando](../../docs/pt-BR/instalacao.md).

Depois abrir `http://<ip-do-host>:8008`. Diferente do Windows, **a instalação
não é desassistida**: você conduz. O passo a passo do upstream é a referência, e
os dois pontos que as pessoas erram são

1. No `Disk Utility`, apagar o maior disco `Apple Inc. VirtIO Block Media`
   antes de o instalador aceitá-lo como destino.
2. Na tela do `Apple ID`, escolher `Set Up Later` e depois `Skip`.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/macos/macos.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/macos/storage
mkdir -p ~/.config/containers/env

# 3. Ambiente — editar VERSION se não quiser o Sequoia
wget -O ~/.config/containers/env/macos.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/macos/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start macos
```

</details>

## Escolhendo a versão

O `install.py` pergunta na primeira instalação. Só vale ali — depois a imagem
de recuperação está baixada e o valor nunca mais é lido.

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

## Segurança — ler antes de pôr na tailnet

**O viewer da 8008 não tem login**, e o VNC da 5900 também não, por padrão.
Quem abre aquela URL tem a tela, o teclado e o mouse da VM. A unit sai com as
labels do tsdproxy ligadas, seguindo o padrão deste repositório, o que
significa que todo dispositivo da sua tailnet — e tudo que roda neles — alcança
aquilo.

Se essa troca não for o que você quer, instalar com `--access local` — as
labels do tsdproxy são comentadas em vez de apagadas, então mudar de ideia
depois é um `--update` com outro modo
([Instalando e operando](../../docs/pt-BR/instalacao.md)).

Vale dizer com todas as letras: este container recebe `/dev/kvm`,
`/dev/net/tun` e `NET_ADMIN`, e roda um sistema operacional inteiro. É uma
superfície de confiança grande por construção, não por descuido.

## Hardening — o que não foi tentado

Só o `PidsLimit=512` além dos padrões, pelos mesmos motivos do
[Windows](../windows/) e do [QEMU](../qemu/):

| Ajuste | Situação |
| --- | --- |
| `PidsLimit=512` | ligado — QEMU mais os processos auxiliares do entrypoint |
| `AddCapability=NET_ADMIN` | exigido pelo upstream, pra rede tun da VM |
| `ReadOnly=true` | **não tentado** — o entrypoint escreve em `/run` e descompacta mídia |
| `User=` | **não tentado** — o QEMU é iniciado como root pelo entrypoint |
| `DropCapability=ALL` | **não tentado** — não medido, e uma lista errada aparece como VM que sobe sem rede, não como erro claro |

Testar qualquer um significa uma instalação completa de macOS por tentativa, o
teste mais caro do repositório. Nenhum foi medido.

Memória não tem teto na unit. Um teto precisa passar do `RAM_SIZE` com folga
pro próprio QEMU — `Memory=6G` pro `RAM_SIZE=4G` do padrão.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`3.09`), bump na mão
([regra 9](../../docs/pt-BR/convencoes.md)). A tag é a versão do container, não
a do macOS: subir ela atualiza o QEMU e os scripts auxiliares e deixa o sistema
instalado em paz.

O `install.ini` carrega um override de `[upstream]` porque a imagem é
`dockurr/macos` (com dois erres) e o repositório é `dockur/macos` — sem essa
linha o `updates.py` deriva o nome errado e não acha nada.

## Backup & recuperação

```bash
systemctl --user stop macos
tar -czf macos-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes macos
systemctl --user start macos
```

A frio de propósito — copiar o disco de uma VM ligada dá um arquivo que só se
revela corrompido na hora de restaurar. É o maior backup do repositório: o
disco virtual inteiro, dezenas de gigabytes.

## Comandos úteis

```bash
systemctl --user status macos
podman logs -f macos                 # o progresso do download está aqui
podman exec macos df -h /storage     # quanto o disco cresceu de fato
```

## Créditos

Deploy Quadlet baseado no [dockur/macos](https://github.com/dockur/macos)
(MIT), que usa o [qemus/qemu](https://github.com/qemus/qemu) — a mesma base do
[QEMU](../qemu/) e do [Windows](../windows/) daqui. Sem afiliação, endosso ou
patrocínio da Apple Inc.

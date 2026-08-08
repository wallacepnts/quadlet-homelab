# Windows — Podman Quadlet (rootless)

**[🇺🇸 Read in English](./README.md)**

Deploy do [dockur/windows](https://github.com/dockur/windows) via Podman
Quadlet, usando a imagem oficial `docker.io/dockurr/windows`.

Uma VM de Windows de verdade sob QEMU/KVM, embrulhada num container. Ela se
instala sozinha no primeiro boot — a imagem baixa a edição escolhida dos
servidores da própria Microsoft — e depois você alcança a área de trabalho pelo
navegador na porta 8006 ou por RDP na 3389. Serve pro único programa que não
tem versão Linux, e pra testar algo que você prefere não rodar no host.

**Você continua precisando de licença do Windows.** A imagem busca a mídia
oficial da Microsoft, que é livre pra baixar; ativar o que ela instala é entre
você e a Microsoft, e este repositório não muda isso.

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

  Se o dispositivo estiver `crw-rw----` e for de `root:kvm`, entrar no grupo
  `kvm` e relogar.

- **`/dev/net/tun`**, que o container usa pra rede da VM.
- **Disco.** O upstream pede 32 GB livres; uma instalação de Windows 11 fica em
  torno de 20 GB e cresce. Vai pro volume, dentro da sua home — ver "Onde o
  disco fica" abaixo.
- **RAM.** O `RAM_SIZE` fica reservado pela vida inteira da VM, não é
  emprestado sob demanda. Os 4 GB do padrão são 4 GB que o host não tem mais.

## Arquitetura

Um container só rodando QEMU. Um volume, `/storage`, com o disco virtual e a
mídia de instalação baixada. Três portas publicadas:

| Porta | O quê |
| --- | --- |
| `8006` | o viewer web — a área de trabalho no navegador, sem cliente pra instalar |
| `3389/tcp`, `3389/udp` | RDP, pra um cliente de verdade com som e área de transferência |

O primeiro start não é como os outros: ele baixa vários GB e roda o instalador
inteiro do Windows de forma desassistida. O `TimeoutStartSec=600` e os cinco
minutos de `HealthStartPeriod` existem por causa disso. Dá pra assistir em
`http://<ip-do-host>:8006`.

## Arquivos

```
windows.container   # unit principal
.env.example        # edição, RAM, núcleos, tamanho do disco, idioma
install.ini         # receita do secret + o override de upstream
```

## Instalação

```bash
python3 install.py windows            # dry-run: mostra o que vai fazer
python3 install.py windows --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access both`. O
script cria o diretório, escreve o `.env`, gera a senha, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md).

Depois abrir `http://<ip-do-host>:8006` e acompanhar a instalação. Demora.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/windows/windows.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/windows/storage
mkdir -p ~/.config/containers/env

# 3. Ambiente
wget -O ~/.config/containers/env/windows.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/windows/.env.example

# 4. Secret — a senha de RDP da conta `Docker`
podman secret create windows-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 5. Subir
systemctl --user daemon-reload
systemctl --user start windows
```

</details>

## Escolhendo a edição e o idioma

O `install.py` pergunta, na primeira instalação:

```
  Which Windows to install (downloaded on first boot)
    1) 11        Windows 11 Pro — 7.9 GB  (default)
    2) 11l       Windows 11 LTSC — 4.7 GB, no Store, long-term servicing
   ...
  number or value [11]:
```

Responder com o número, com o próprio valor, ou Enter pro padrão. As duas
configurações só valem no **primeiro** start — a edição e o idioma dela são
baixados ali e nunca mais consultados. Mudar de ideia depois significa apagar o
volume e começar de novo.

Sem terminal (`--prefix`, script, CI) ele não pergunta: mantém os padrões e
avisa qual arquivo editar antes do primeiro start.

### Edições

| Valor | Edição | Download |
| --- | --- | --- |
| `11` | Windows 11 Pro | 7.9 GB |
| `11l` | Windows 11 LTSC | 4.7 GB |
| `11e` | Windows 11 Enterprise | 6.6 GB |
| `10` | Windows 10 Pro | 5.7 GB |
| `10l` | Windows 10 LTSC | 4.6 GB |
| `10e` | Windows 10 Enterprise | 5.2 GB |
| `2025` | Windows Server 2025 | 7.6 GB |
| `2022` | Windows Server 2022 | 6.0 GB |
| `2019` | Windows Server 2019 | 5.3 GB |
| `2016` | Windows Server 2016 | 6.5 GB |
| `2012` | Windows Server 2012 | 4.3 GB |
| `2008` | Windows Server 2008 | 3.0 GB |
| `2003` | Windows Server 2003 | 0.6 GB |
| `tiny11` | Tiny11 | 5.3 GB |
| `core11` | Tiny11 Core | 3.0 GB |
| `tiny10` | Tiny10 | 3.6 GB |
| `8e` | Windows 8.1 Enterprise | 3.7 GB |
| `7u` | Windows 7 Ultimate | 3.1 GB |
| `vu` | Windows Vista Ultimate | 3.0 GB |
| `xp` | Windows XP Professional | 0.6 GB |
| `2k` | Windows 2000 Professional | 0.4 GB |
| `reactos` | ReactOS | 0.1 GB |

O `VERSION` também aceita a URL de uma ISO sua, e é por isso que uma resposta
fora da lista é aceita como veio em vez de recusada. As builds Tiny são remixes
da comunidade, não mídia da Microsoft. O ReactOS não é Windows e não precisa de
licença. Host ARM64 usa o
[dockur/windows-arm](https://github.com/dockur/windows-arm/).

### Idiomas

Alemão, árabe, búlgaro, chinês, coreano, croata, dinamarquês, eslovaco,
esloveno, espanhol, estoniano, finlandês, francês, grego, hebraico, holandês,
húngaro, inglês, italiano, japonês, letão, lituano, norueguês, polonês,
português, romeno, russo, sérvio, sueco, tailandês, tcheco, turco e ucraniano —
escritos em inglês no valor (`German`, `Portuguese`, …).

O prompt lista os mais comuns; digitar qualquer um dos nomes acima funciona.
Pra português do Brasil, escolher `Portuguese` e depois definir a variante no
`.env`:

```bash
REGION=pt-BR
KEYBOARD=pt-BR
```

## Segurança — ler antes de pôr na tailnet

**O viewer da 8006 não tem login.** Quem abre aquela URL está sentado na área
de trabalho do Windows, já logado. A unit sai com as labels do tsdproxy
ligadas, seguindo o padrão deste repositório, o que significa que todo
dispositivo da sua tailnet — e tudo que roda neles — alcança aquilo.

A conta de RDP é a peça que tem senha: o padrão do upstream é o usuário
`Docker` com a senha literal `admin`, e o `install.ini` troca por uma gerada:

```bash
podman secret inspect --showsecret windows-password
```

Isso protege a 3389. Não faz nada pela 8006.

Se essa troca não for o que você quer, instalar com `--access local` — as
labels do tsdproxy são comentadas em vez de apagadas, então mudar de ideia
depois é um `--update` com outro modo
([Instalando e operando](../../docs/pt-BR/instalacao.md)).

Vale dizer com todas as letras: este container recebe `/dev/kvm`,
`/dev/net/tun` e `NET_ADMIN`, e roda um sistema operacional inteiro que você
não auditou. É uma superfície de confiança grande por construção, não por
descuido.

## Onde o disco fica

O `DISK_SIZE` padrão é 64 GB. A imagem é esparsa — cresce conforme o Windows
escreve, em vez de ser alocada de cara — mas ainda assim vai parar em
`~/.config/containers/volumes/windows/storage`, que provavelmente está no mesmo
sistema de arquivos que todo o resto que é seu.

Pra pôr num lugar com mais espaço, apontar o volume pra lá:

```ini
Volume=/mnt/disco-grande/windows:/storage:Z
```

Mudar **antes** do primeiro start. Depois, mover significa parar o serviço e
mover o diretório na mão.

## Hardening — o que não foi tentado

Só o `PidsLimit=512` além dos padrões. A escada da
[regra 20](../../docs/pt-BR/convencoes.md) não se aplica bem aqui, e os motivos
merecem ficar escritos em vez de virarem omissão:

| Ajuste | Situação |
| --- | --- |
| `PidsLimit=512` | ligado — QEMU mais os processos auxiliares do entrypoint |
| `AddCapability=NET_ADMIN` | exigido pelo upstream, pra rede tun da VM |
| `ReadOnly=true` | **não tentado** — o entrypoint escreve em `/run` e descompacta mídia nas camadas da própria imagem |
| `User=` | **não tentado** — o QEMU é iniciado como root pelo `tini`/`entry.sh` |
| `DropCapability=ALL` | **não tentado** — não medido, e uma lista errada aqui aparece como VM que sobe sem rede, não como erro claro |

Testar qualquer um desses direito significa uma instalação completa de Windows
por tentativa, e é por isso que nenhum foi medido. Se você medir algum,
registrar aqui com o erro.

Memória não tem teto na unit. Se quiser um, ele precisa passar do `RAM_SIZE`
com folga pro próprio QEMU — `Memory=6G` pro `RAM_SIZE=4G` do padrão.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`6.04`), bump na mão
([regra 9](../../docs/pt-BR/convencoes.md)). A tag é a versão do *container*,
não do Windows: subir ela atualiza o QEMU e os scripts do instalador e deixa o
Windows instalado em paz, que segue se atualizando por dentro como qualquer
Windows.

O `install.ini` carrega um override de `[upstream]` porque a imagem é
`dockurr/windows` (com dois erres) e o repositório é `dockur/windows` — sem
essa linha o `updates.py` deriva o nome errado e não acha nada.

## Backup & recuperação

```bash
systemctl --user stop windows
tar -czf windows-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes windows
systemctl --user start windows
```

A frio de propósito — copiar o disco de uma VM ligada dá um arquivo que só se
revela corrompido na hora de restaurar. Reparar no tamanho: isto é o disco
virtual inteiro, dezenas de gigabytes, o que é outra conversa em relação a
todos os outros backups deste repositório.

## Comandos úteis

```bash
systemctl --user status windows
podman logs -f windows                 # o progresso da instalação está aqui
podman exec windows df -h /storage     # quanto o disco cresceu de fato
```

## Créditos

Deploy Quadlet baseado no [dockur/windows](https://github.com/dockur/windows)
(MIT), que por sua vez usa o [qemus/qemu](https://github.com/qemus/qemu).

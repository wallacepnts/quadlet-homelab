# Toolbx — Podman Quadlet (rootless)

**[🇺🇸 Read in English](./README.md)**

Shells de distro descartáveis. `dnf`, `apt` e `pacman` moram todos aqui dentro,
então uma ferramenta avulsa, uma compilação rápida ou um binário desconhecido
rodam num container em vez de no host. Quatro caixas, paradas até você entrar
em uma.

```bash
podman exec -it toolbx-fedora bash
```

É toda a interface. Instala o que precisa, usa, e quando a caixa ficar suja
apaga o volume e começa limpo — o host não mudou em momento nenhum.

## As quatro

As imagens são as que o projeto [Toolbx](https://containertoolbx.org/) publica,
e as quatro distros são as que ele suporta oficialmente. São feitas pra uso
interativo — `bash`, `git` e o ferramental de shell de sempre já vêm dentro,
coisa que imagem base de distro não dá.

| | Unit | Imagem | Gerenciador de pacotes |
| --- | --- | --- | --- |
| <img src="https://cdn.simpleicons.org/archlinux/1793D1" width="24" height="24" alt=""> | `toolbx-arch` | `quay.io/toolbx/arch-toolbox` (por digest) | `pacman -S` |
| <img src="https://cdn.simpleicons.org/fedora/51A2DA" width="24" height="24" alt=""> | `toolbx-fedora` | `registry.fedoraproject.org/fedora-toolbox:45` | `dnf install` |
| <img src="https://cdn.simpleicons.org/redhat/EE0000" width="24" height="24" alt=""> | `toolbx-rhel` | `registry.access.redhat.com/ubi10/toolbox:10.2` | `dnf install` |
| <img src="https://cdn.simpleicons.org/ubuntu/E95420" width="24" height="24" alt=""> | `toolbx-ubuntu` | `quay.io/toolbx/ubuntu-toolbox:26.04` | `apt install` |

**Não é o CLI `toolbox`.** Estes pegam emprestado as imagens do projeto e a
lista de distros dele, não a ferramenta: não tem comando `toolbox` aqui nem
`toolbox enter` — só units de Quadlet e `podman exec`. A troca é que estes estão
declarados neste repositório e sobrevivem a reboot, enquanto o `toolbox create`
é imperativo e local à máquina onde você rodou.

As imagens documentam o `toolbox init-container` como entrypoint delas, e estas
units rodam `sleep infinity` no lugar. O trabalho daquele comando é criar um
usuário correspondente dentro do container e montar caminhos do host —
`/run/libvirt`, `/run/systemd/journal`, `/var/log/journal` — pra dissolver a
fronteira entre container e host. A integração com o host é justamente a parte
que vale pular aqui; o usuário que ele criaria, o `UserNS=keep-id` já entrega,
que é por que `whoami` e `$HOME` funcionam lá dentro. As imagens não trazem
entrypoint próprio (o projeto exige isso), então o `Exec=` fica livre.

## Arquitetura

Cada unit roda `sleep infinity` e nada mais. Sem portas, sem healthcheck, sem
label de tsdproxy ou homepage — não há serviço pra alcançar aqui, só um shell
pra entrar. Sobem no boot pro `podman exec` sempre funcionar, e um `sleep`
parado não custa nada.

Duas decisões que vale conhecer:

- **`UserNS=keep-id`.** Os arquivos que você criar em `/work` caem no host com
  o seu dono, não com um subuid mapeado que exigiria `podman unshare` pra
  tocar. Isso não é hardening ([regra 20](../../docs/pt-BR/convencoes.md)) — é
  puramente sobre quem é dono dos arquivos. É também por isso que instalar
  pacote pede uma flag a mais, logo abaixo.
- **Um volume por caixa**, em `/work`, que também é o `HOME` e o diretório de
  trabalho. Um binário compilado na caixa Arch não pertence à do Fedora, então
  elas não compartilham. O `HOME=/work` é o que aponta o shell pro volume: o
  Podman sintetiza a entrada do `/etc/passwd` a partir dele, então histórico de
  shell, config do `npm` e tudo que segue `$HOME` caem num lugar que sobrevive
  a restart em vez da camada descartável do container.

## Arquivos

```
toolbx-arch.container
toolbx-fedora.container
toolbx-rhel.container
toolbx-ubuntu.container
install.ini               # [upstream] = "-" pras quatro
```

## Instalação

```bash
python3 install.py toolbx            # dry-run: mostra o que vai fazer
python3 install.py toolbx --apply
```

O script escreve as units e cria os quatro diretórios de volume, e para por
aí: sem uma unit principal única ele não adivinha qual caixa você quer, então
subir na mão — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md).

```bash
systemctl --user start toolbx-arch toolbx-fedora toolbx-rhel toolbx-ubuntu
```

## Só uma caixa

Nomear a unit em vez da pasta:

```bash
python3 install.py toolbx-ubuntu --apply
```

Isso escreve um arquivo de unit, cria um diretório de volume e sobe. Na mão são
as mesmas quatro linhas com um `wget` só:

```bash
mkdir -p ~/.config/containers/systemd/toolbx ~/.config/containers/volumes/toolbx/ubuntu
wget -P ~/.config/containers/systemd/toolbx/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/toolbx/toolbx-ubuntu.container
systemctl --user daemon-reload
systemctl --user start toolbx-ubuntu
```

**Se você já rodou `install.py toolbx`**, os quatro arquivos estão no disco, e
pela [regra 4](../../docs/pt-BR/convencoes.md) o `[Install]` deles já foi
aplicado na geração — então as outras três sobem sozinhas no próximo boot, e
unit gerada por Quadlet não aceita `disable`. Apagar o arquivo é o único jeito
de não ter a caixa:

```bash
rm ~/.config/containers/systemd/toolbx/toolbx-{arch,fedora,rhel}.container
systemctl --user daemon-reload
```

Antes do primeiro start elas não custam nada — a imagem só é puxada quando a
unit sobe. É o boot seguinte que pega.

## Usando uma

```bash
podman exec -it toolbx-fedora bash
```

Isso te larga lá dentro como **o seu próprio usuário**, que é o que mantém os
arquivos de `/work` seus. Instalar pacote precisa de root, então pede
`--user root`:

```bash
podman exec -it --user root toolbx-fedora dnf install -y ripgrep
podman exec -it toolbx-fedora rg --version
```

Esquecer a flag dá erro de permissão do gerenciador de pacotes, não erro de
comando inexistente — esse é o sinal. O `sudo` está instalado mas não ajuda: as
imagens trazem a regra `%wheel NOPASSWD` comentada, e quem normalmente
descomenta é o `toolbox init-container`, que estas units pulam.

Pacote instalado vive na camada gravável do container, então sobrevive a um
`restart` mas **não** a um `podman rm` nem a um bump de imagem. O que você quer
guardar vai pra `/work`.

Pra recomeçar do zero numa caixa:

```bash
systemctl --user stop toolbx-fedora
rm -rf ~/.config/containers/volumes/toolbx/fedora   # só se quiser apagar os dados também
systemctl --user restart toolbx-fedora
```

### A caixa RHEL instala de um conjunto menor

O `ubi10/toolbox` é a imagem redistribuível da Red Hat, e num host sem
subscription o `dnf` dela alcança **só os repositórios UBI** — um subconjunto do
RHEL. Pacote que está lá instala normal; o que está fora volta como pacote
inexistente, não como problema de permissão:

```
$ podman exec --user root toolbx-rhel dnf install -y wget    # está no UBI  -> instala
$ podman exec --user root toolbx-rhel dnf install -y tree    # não está no UBI
No match for argument: tree
Error: Unable to find a match: tree
```

Serve pra conferir comportamento no userland do RHEL. Pra "instalar uma
ferramenta qualquer", ir na caixa do Fedora ou do Arch.

## Rodando o Claude Code numa delas

Precisa de três coisas que as caixas peladas não têm.

**Node, primeiro.** Nenhuma das quatro traz:

```bash
podman exec -it --user root toolbx-ubuntu bash
apt update && apt install -y curl ca-certificates
curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt install -y nodejs
npm install -g @anthropic-ai/claude-code
```

**Credencial, segundo.** Ou exportar `ANTHROPIC_API_KEY`, ou logar
interativamente — o perfil OAuth cai dentro do `HOME`, que aqui é `/work`,
então sobrevive a restart em vez de forçar relogin toda vez.

**O seu projeto, terceiro — e é essa parte que decide se algo disso valeu.**
Montar o repositório em que você está trabalhando, e *só* ele:

```ini
Volume=%h/HD/Projetos/meu-projeto:/work/meu-projeto:Z
```

Montar `%h` no lugar devolve ao agente exatamente tudo de que o container ia
mantê-lo longe.

**O que o container não faz**, nas palavras da própria Anthropic: um dev
container *"não impede um projeto malicioso de exfiltrar qualquer coisa
acessível dentro do container, incluindo as credenciais do Claude Code
guardadas em `~/.claude`"*. Mount estreito limita o que pode ser
**danificado**; não limita o que pode ser **lido e mandado pra fora**, porque o
container isola o filesystem e não a rede. Tudo lá dentro alcança o que o host
alcança.

Esse aviso pesa mais aqui do que na configuração de referência: o `HOME=/work`
põe o token OAuth no mesmo volume que o projeto. Tratar estas caixas como
exclusivas pra repositório confiável, e preferir token de escopo curto a montar
qualquer coisa vinda do host.

**A peça que falta é filtro de egresso.** O devcontainer de referência resolve
com um [`init-firewall.sh`](https://github.com/anthropics/claude-code/blob/main/.devcontainer/init-firewall.sh)
que nega todo tráfego de saída fora de uma allowlist. Rodar ele exige
`AddCapability=NET_ADMIN` e `AddCapability=NET_RAW` na unit mais o script no
start — ainda não ligado aqui.

**Existem opções mais leves.** Se o objetivo for só "menos prompts", o modo
`auto` passa um classificador nas ações em vez de desligar a checagem. E o
Claude Code já traz um sandbox de Bash embutido que talvez resolva sem nada
disso — ver [Sandbox environments](https://code.claude.com/docs/en/sandbox-environments).

## Auto-update

Sem `AutoUpdate=` — tags explícitas, bump na mão
([regra 9](../../docs/pt-BR/convencoes.md)). O Arch é a exceção: o
`arch-toolbox` publica só `latest`, então ele fica pinado **por digest**, do
mesmo jeito que o [mdrop](../mdrop/) faz com a imagem dele. Subir de versão ali
é ler o digest novo:

```bash
podman pull quay.io/toolbx/arch-toolbox:latest
podman inspect quay.io/toolbx/arch-toolbox:latest --format '{{index .RepoDigests 0}}'
```

O `updates.py` não ajuda com nenhuma das quatro: nenhuma vem de release do
GitHub, e é por isso que o `install.ini` declara `[upstream] = "-"` pra todas.
Elas continuam aparecendo em *"cannot compare"* — o `-` diz pro `updates.py`
não tentar, mas a linha impressa é a mesma "declare it in [upstream]".
Acompanhar as notas de release de cada distro.

## Backup & recuperação

Os containers em si são descartáveis — reinstala e pronto. Só o `/work` guarda
algo que valha:

```bash
tar -czf toolbx-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes toolbx
```

## Comandos úteis

```bash
podman ps --filter "name=toolbx-"
podman exec -it toolbx-fedora bash                    # como você
podman exec -it --user root toolbx-fedora bash        # pra instalar pacote
systemctl --user restart toolbx-fedora
```

## Créditos

As imagens vêm do [Toolbx](https://containertoolbx.org/)
([containers/toolbox](https://github.com/containers/toolbox), Apache-2.0), cuja
lista oficial de distros esta pasta segue.

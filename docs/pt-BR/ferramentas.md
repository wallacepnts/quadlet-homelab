# Ferramentas

Os três falam português quando o sistema fala, como o `qh`. O `QH_LANG=en` ou
`QH_LANG=pt` força um dos dois, e o `NO_COLOR=1` desliga a cor — que já sai
desligada sozinha sempre que a saída não é um terminal.

## `qh-check`

Lê todas as units de `apps/` e reprova o que falha em silêncio. Roda também no
CI a cada push, então erro aqui reprova o build.

```bash
qh-check
```

O que ele pega: unit com basename diferente do app, dois serviços publicando a
mesma porta do host, `Secret=` sem receita no `app.json`, serviço faltando na
tabela de serviços do README, README de serviço cuja linha de versão não bate
mais com as units, `PodmanArgs=` levando o que o Quadlet já tem chave para ou um
espaço que ele não sobrevive, linha do
[`endurecimento.md`](./endurecimento.md) que não bate mais com a unit, `$` em
`HealthCmd` sem o escape duplo, barra invertida em valor de `Label=`, valor com espaço sem aspas, `Notify=healthy`
sem `HealthCmd`, e unit fora do layout padrão — os blocos descritos na
[referência](./referencia.md#anatomia-de-um-container). Esse ele também conserta:

```bash
qh-check --format      # reescreve todas as units no layout; só ordem e linhas em branco
```

Ele também passa cada unit pelo **gerador do próprio Quadlet** do Podman (`quadlet -dryrun -user`,
todas as units num diretório só, como no host), que sabe o que o resto do arquivo não sabe: chave
não suportada, `Network=` que cita um arquivo que não existe, seção que ele não consegue ler. Isso
só aparecia na instalação. Roda quando a máquina tem um gerador do Podman 5 ou mais novo e é
pulado em silêncio caso contrário; `qh-check --quadlet` faz a ausência dele virar erro, que é o que
o CI usa (um job à parte, na imagem oficial `podman/stable`, já que o Podman do runner é mais antigo
do que as chaves pedem). O gerador não interpreta todo valor (`Notify=maybe` passa), então isto é um
piso sob as outras checagens, não um substituto. A tela Personalizar da loja já valida um drop-in
com o mesmo gerador antes de gravá-lo.

Pra dispensar uma regra de propósito, a unit diz isso e o motivo é obrigatório:

```ini
# check: ignore ports vm-windows and vm-windows-arm never run together
```

## `qh-updates`

Compara cada tag de `Image=` com a última release do projeto no GitHub e mostra
só o que está desatualizado. O `--all` acrescenta o que está em dia e o que não
deu pra comparar.

```bash
qh-updates
```

O repositório no GitHub é derivado do nome da imagem quando dá, e o
`app.json` traz um override de `upstream` quando não dá — a imagem quase
nunca tem o nome do repositório (`dockurr/windows` contra `dockur/windows`).

O `--bump` pega o que ele encontrou: reescreve o `Image=` e todo lugar que o
espelha — a página por unit e a coluna Versão de uma pasta que documenta suas units em
separado. A tabela de serviços do README raiz não tem versão. Sem `--apply`, só
mostra o plano.

O `--host` compara o que está instalado nesta máquina, não o que o repositório
fixa, então dá pra saber o que está atrás do upstream antes mesmo do bump no
repositório. O `--json` imprime cada linha em JSON, que é o que a loja lê.

```bash
qh-updates --host            # o instalado aqui, contra a release de cada projeto
qh-updates memos --bump      # um serviço só (nome da pasta ou da unit)
```

```bash
qh-updates --bump            # o que ele pegaria
qh-updates --bump --apply    # pegar
```

Ele recusa major, listando para você pegar um de cada vez com `--major`. A regra
9 das [convenções](./convencoes.md) é que versão se escolhe, não se recebe: o wud
9 sai no boot sem um administrador que antes não existia, o wger 2.7 converte
dados antigos com uma configuração que precisa estar certa antes e não pode
mudar depois. A recusa é filtro, não garantia — versão de calendário não tem
major, então 2026.8 para 2026.9 lê como minor e trouxe oito mudanças
incompatíveis. Ler as notas da release continua sendo o trabalho.

Secundário rastreado por `compose:` sobe para o que aquele compose declara,
digest incluído. Quando o compose roda duas imagens de mesmo nome — o do Postiz tem
`postgres:17-alpine` para o app e `postgres:16` para o Temporal — compara-se a que
tem a tag com a mesma forma da fixada. Pegar a primeira fazia o banco do Temporal
aparecer como um major atrasado.

Antes de perguntar se existe imagem mais nova, ele pergunta se a fixada ainda
existe, e reporta como sumida a que não. Duas chegaram lá por caminhos
diferentes: a imagem do Chrome que o karakeep usava foi retirada do registry, e
o digest do arch-toolbox foi coletado debaixo de uma imagem rolling. As duas
seguiam rodando da cópia local enquanto toda instalação nova falhava.

Release no GitHub não é imagem publicada: a release pode sair horas antes de o
registry ter a tag. Esse caso é reportado à parte — a tag é conferida no
registry antes de a atualização ser dada como disponível.

Secundário segue a versão que o compose do próprio app valida, não o upstream
dele — o Postgres do compose do immich se move quando o immich o move:

```ini
`upstream`
immich-postgres = compose:immich-app/immich:docker/docker-compose.yml
authentik-postgres = compose:https://goauthentik.io/docker-compose.yml
```

O compose é lido na versão em que a unit principal está fixada, que é a versão
pra qual você iria. URL direta também vale, pra projeto que publica o compose no
site em vez de no repositório.

Quando os dois lados fixam por digest, são os digests que se comparam — uma tag
como a `valkey:9` do immich se lê igual em duas releases enquanto a imagem
embaixo dela muda, e comparar tag ali só diria "em dia". Quando o compose não
fixa nada, isso é reportado como tal em vez de virar "em dia", que seria uma
comparação que nunca aconteceu.

Imagem que não versiona por release do GitHub — tag de distribuição, projeto
que só publica tags git, imagem versionada à parte do repositório — compara
com o registry:

```ini
`upstream`
netbootxyz = registry
```

Ele lista as tags do registry e pega a mais nova com o mesmo formato da nossa:
com `1.30.4-alpine` instalada, as candidatas são `\d+.\d+.\d+-alpine`, então
`-perl` e `latest` nunca vencem.

Um padrão depois dos dois-pontos estreita essa lista onde o formato sozinho não
dá conta — o nginx deixa a stable nas minors pares e a mainline nas ímpares, e
publica `-alpine` para as duas:

```ini
`upstream`
nginx = registry:^1\.\d*[02468]\.\d+-alpine$
```

Um valor é especial. O `registry:latest` pergunta em qual tag numerada o
`latest` resolve hoje, e compara com ela. Serve para projeto que numera também
as prereleases: o Fedora publica lado a lado a release estável, a branched e a
rawhide, todas numeradas, então o número mais alto é sempre a resposta errada —
o `46` é idêntico byte a byte à `rawhide`, enquanto o `latest` é a `44`.

```ini
`upstream`
toolbx-fedora = registry:latest
```

E `-` diz que não há o que comparar — a imagem Arch do toolbx só publica
`latest`, então ela é fixada por digest e tag nenhuma responderia por ela.

Tag flutuante (`latest`, major solto) não tem versão pra comparar, então a
comparação é por digest: se a tag hoje aponta pra outro lugar que a imagem
deste host, ele diz. Isso exige podman e a imagem já baixada.

## `qh-store`

O painel web, e a forma como este repositório deve ser usado: o `bootstrap.sh` o sobe, e
instalar, atualizar, fazer backup, restaurar, personalizar e remover acontece nele. É uma camada
sobre o `qh`: mostra o catálogo (`qh --catalog`), e
cada ação roda um comando do `qh`: primeiro o plano em simulação, depois
`qh <app> --apply` (e também `--update` e `--remove`), além de
iniciar/parar/reiniciar e logs de cada unit. Nada nela é uma segunda implementação, então o que o
terminal faz e o que o painel faz não podem divergir.

Apagar dados também é no painel, com a mesma trava de uma restauração: o formulário **Remover**
tem "Apagar também os dados, os secrets e o .env", que pede o nome do serviço digitado, e o `qh`
o pede de novo por conta própria. **Configurações** (no cabeçalho) guarda a regra de acesso (rede
local, tailnet ou ambas, `qh --set-access`) e mostra quais serviços instalados não a seguem, com
um botão que a aplica a eles (uma atualização cada). **Atualizar todos**, em Meus apps, pega todo
serviço que tem algo a pegar, um depois do outro: uma falha não interrompe os demais, e o job diz
no fim que uma falhou. Cada unit instalada mostra a tag dela
ao lado da última release do projeto (`qh-updates --host`, guardado em disco
por um dia e consultado de novo só para o serviço que uma instalação,
atualização ou remoção acabou de mexer; o **Verificar agora** força), então dá pra ver o que está atrás sem
depender de um bump neste repositório.
O **Atualizar para X** leva a release nova. Num app cuja versão não está no repositório (veja
[auto-update](./auto-update.md)) isso é `qh <app> --update --latest --apply`: a tag nova é
fixada no drop-in do host e não sobra nada para commitar. Numa imagem que ainda tem a tag na
unit (um apoio, um digest) é `qh-updates <app> --bump --apply` só daquele serviço (o
`Image=`, no clone de onde a loja roda) e então `qh <app> --update
--apply`, e a mudança fica no git para você revisar e commitar. Uma major fica retida nos
dois caminhos.
Existe um botão de atualizar só, e ele só aparece quando há algo para
atualizar, e clicar nele já roda a atualização, sem plano e sem confirmação.
Enquanto roda, o painel mostra todas as releases do GitHub entre a tag
instalada e a do upstream (sem prereleases). Remover e restaurar continuam
mostrando o plano e pedindo confirmação, porque mexem com dados. O **Login** mostra a credencial que o `login` do
`app.json` indica, a mesma que o `qh` imprime depois de instalar. O
**Backups** roda o `qh --backup` em `~/.local/share/quadlet-homelab/backups`,
lista os arquivos e permite baixá-los ou enviar um de volta. A restauração roda
o `qh --restore`, e é preciso digitar o nome do serviço antes, igual no
terminal. Um serviço que guarda dados ganha também a caixa **Backup antes** ao lado de
Atualizar (lembrada no navegador, desligada por padrão): a atualização roda depois de um
`qh --backup`, encadeado, então um backup que falha impede a atualização antes de mudar
qualquer coisa. O backup é o a frio (para o serviço por um instante), então custa uma
parada curta. O que o terminal perguntaria durante
uma instalação, o formulário pergunta antes: secrets `manual` e `vars` ainda
não definidas. Eles são gravados com as mesmas funções e a mesma checagem
`validate` que o `qh` usa.

**Configurar** edita o `.env` do serviço, o arquivo que o `qh` instalou a partir
do `.env.example`. Uma opção opcional vem comentada: marcar liga, e desmarcar
uma ativa a comenta de novo. Só são aceitas chaves que o arquivo já cita, o
valor é uma linha só, e o arquivo anterior fica em `<nome>.env.bak` (modo
0600). Salvar reinicia as units que leem o arquivo com `try-restart`, então um
serviço parado continua parado. Chaves com cara de credencial viram campo de
senha.

Uma opção pode dizer o que guarda com uma linha `# type:` entre os comentários logo
acima dela no `.env.example`: `number`, `bool`, `email`, `url`, `ip` ou `password`
(texto, quando não há). O formulário mostra a caixa certa — campo numérico, caixa de
marcar que escreve no estilo do próprio arquivo (`Y`/`N`, `yes`/`no`, `1`/`0`,
`true`/`false`), campo mascarado — e o servidor recusa valor que não seja do tipo. Valor
vazio nunca é recusado: significa não definido. O `check.py` reprova tipo desconhecido,
dica sem opção embaixo e valor de exemplo que não é do tipo. Só declare `bool` onde o app
não aceita outra coisa (`GPU=Y` também aceita `intel` ou `nvidia`, então fica texto).
```
# Quantos núcleos a VM recebe.
# type: number
CPU_CORES=2
```

O painel também mostra CPU, memória e disco, e as arquiteturas para as quais as
imagens são construídas, com um aviso quando a do host não está entre elas. CPU
e memória vêm de `/proc` e do cgroupfs, porque o `podman stats` responde 0B de
memória para containers rootless aqui (o controlador de memória não é delegado
ao cgroup do usuário); a memória é o tamanho residente, que conta uma página
compartilhada entre os processos de um container uma vez por processo, então é
um tamanho para comparar, não uma contabilidade. O disco é o
`podman unshare du` sobre os volumes que o `qh --backup` empacotaria, nunca uma
raiz de mídia compartilhada, e fica em cache por dez minutos. As arquiteturas
vêm do manifest da imagem no registry e ficam em cache por uma semana.

A página tem duas telas, como o CasaOS. **Meus apps** é o que está instalado,
em azulejos com o estado, o selo de versão e CPU e memória: o azulejo abre o app
em outra aba quando ele tem um endereço só, e a engrenagem ao lado gerencia o
serviço. Um app com várias interfaces web (a media-stack) ou nenhuma não tem um
lugar único para ir, então o azulejo dele abre o painel. A **Loja** é o catálogo
inteiro, com categorias e busca, e marca o que já está instalado. A tela fica
guardada na URL (`#apps` ou `#store`), então um reload ou um favorito volta para
a mesma; sem nada instalado ainda, abre na Loja.

Ela roda no host como serviço `systemd --user`, não como Quadlet. O trabalho
dela é comandar o systemd e o podman como você, então um container precisaria
do seu home, do socket do podman e do barramento do systemd. É o mesmo acesso,
só que menos visível. Pelo mesmo motivo a unit não tem `NoNewPrivileges=`: o
podman rootless precisa do `newuidmap` com setuid.

O `bootstrap.sh` a instala e a sobe: copia a unit para `~/.config/systemd/user/`, pergunta uma
vez de onde o painel será aberto (gravando `QH_STORE_LISTEN` num drop-in para a rede local ou a
tailnet), a inicia, e mostra o endereço e o token de login. Rodar de novo mantém a resposta,
reinicia o painel com o código novo e os mostra outra vez. `NO_PANEL=1` pula tudo isso. A unit
chama `~/.local/bin/qh-store`, o link que o `bootstrap.sh` cria. Na mão:

```bash
systemctl --user enable --now ~/quadlet-homelab/store/qh-store.service
cat ~/.config/quadlet-homelab/store-token       # o login
```

Cada serviço instalado tem um seletor de **Acesso**: seguir a regra, rede
local, tailnet ou os dois. Escolher um salva uma exceção
(`qh --set-access MODO APP`) e aplica com `--update`. Instalar um serviço cuja
rede pertence a outro que não está instalado (o tsdproxy, para 80 dos 83)
instala esse outro antes, com as perguntas dele no mesmo formulário.

Ela escuta em `127.0.0.1:8484`, então só esta máquina alcança. Para abrir de
outro computador, use `ssh -L 8484:127.0.0.1:8484 <host>`. Para acessar também
pela tailnet, dê a ela o endereço da tailnet do host junto (endereços separados
por vírgula, cada um com seu listener; `0.0.0.0` incluiria a rede local) e
publique pelo `lists.yaml` do tsdproxy, do mesmo jeito que o Cockpit. A entrada
já vem comentada em `apps/tsdproxy/config/lists.yaml`:

```bash
systemctl --user edit qh-store      # [Service]  Environment=QH_STORE_LISTEN=127.0.0.1:8484,<tailscale-ip>:8484
```

```yaml
qh-store:
  ports:
    443/https:
      targets:
        - http://<tailscale-ip>:8484
```

O **Histórico** (o botão do cabeçalho, e um por serviço) lista toda ação que a
loja rodou — instalar, atualizar, remover, backup, restauração, acesso,
configuração e iniciar/parar/reiniciar — com quando foi, como terminou,
quanto durou e a saída. É uma linha de JSON por ação em
`~/.local/share/quadlet-homelab/store-history.jsonl` (modo 0600): da saída
fica só o último pedaço de 20 000 caracteres, as credenciais de login que o
`qh` imprime depois de uma instalação são mascaradas como `***`, e o arquivo é
cortado pela metade mais nova quando passa de 2 MB. O "de" é o endereço que a
loja viu; atrás do tsdproxy é o do proxy, já que existe um token só e portanto
um usuário só.

Cada painel também tem links para o projeto, a documentação e as issues dele, as
releases, a página da imagem no registry e a receita deste repositório. O
repositório do projeto só aparece onde algo diz qual é — o `upstream` do
`app.json`, ou uma imagem no `ghcr.io`/`lscr.io` — e nunca é adivinhado a
partir de um nome do Docker Hub, o que daria um link para um 404. Onde o caminho
da imagem não é o do repositório (a imagem do netbootxyz sai de outro
repositório), o ``links.repo` = dono/repo` (ou uma URL https completa) diz qual
é; **Problemas** e **Releases** saem dele, para GitHub, GitLab e Codeberg. A
**Documentação** é lida do link `[Documentação oficial](...)` da seção Créditos
do README de cada serviço, então é escrita uma vez, por uma pessoa, e um link
que só aponta de volta para o repositório fica de fora. Todos foram conferidos
quando entraram; o `check.py` não os busca, então um link ainda pode envelhecer.

As capturas de tela vêm do `app.json`, como imagens que o próprio projeto
hospeda:

```json
"screenshots": ["https://example.org/captura-1.png", "https://example.org/captura-2.png"]
```

O `check.py` limita a lista a URLs https, no máximo seis e sem repetição. O
navegador carrega as imagens de lá, então o host do projeto vê a requisição,
como já vê nos ícones. Alguns serviços trazem capturas como exemplo; os demais
ficam sem até alguém acrescentar uma imagem que valha a pena.

Um serviço descontinuado — arquivado no upstream, ou com a imagem fixada que sumiu
do registry — é marcado no mesmo arquivo:

```json
"deprecated": {"en": "Archived upstream on 2026-03-01; no release since 1.4.2.",
               "pt": "Arquivado no upstream em 01/03/2026; sem release desde a 1.4.2."}
```

A loja mostra um selo "descontinuado" com o motivo e não oferece a instalação, e o
servidor recusa uma também. Um serviço já instalado continua gerenciável, já que
remover é o passo mais provável. O `qh` avisa antes de instalá-lo e o `qh --all`
o deixa de fora; nomeá-lo ainda instala, porque o aviso não é uma proibição. O
`deprecated_pt` é opcional, e sem ele vale o motivo em inglês. O `check.py` pede
uma linha simples de até 300 caracteres. É uma decisão que uma pessoa registra:
nada marca um serviço sozinho.

**Console**: um botão Console numa unit rodando abre um shell dentro do container (`podman exec
-it`, bash se a imagem tiver, senão sh) por WebSocket, escrito só com a biblioteca padrão
(`wsterm.py`: o handshake, quadros de texto, ping/pong, fechamento e um pty). Quem tem o token já
controla todos os serviços, então isto não dá poder novo, mas é um shell, então: o `Origin` do
navegador tem de ser o do próprio servidor (um WebSocket não leva o cabeçalho `X-QH-Store`, e o
cookie é `SameSite=Strict`), no máximo quatro consoles ficam abertos, um parado há 15 minutos é
fechado, e cada sessão é uma linha no histórico. A página guarda a tela sozinha e entende o que um
shell com `TERM=dumb` envia (quebras de linha, backspace, tab; as cores são descartadas), então
programas de tela cheia (vim, top) não funcionam. Fechar a aba encerra a sessão com educação
(Ctrl-C, `exit`) e, se o shell ignorar, mata tudo o que ele iniciou por uma marca de ambiente:
fechar só o `podman exec` local deixa o shell do container rodando.

**Logs ao vivo**: o botão Logs de uma unit abre as últimas 200 linhas e depois as segue conforme
chegam (`journalctl -f`, enviado como Server-Sent Events), com uma caixa que filtra as linhas
enquanto você digita (sem diferenciar maiúsculas, sobre as últimas 5000 recebidas) e uma marca
"seguir" que mantém a vista no fim. Fechar o painel ou abrir outro log encerra o stream, e o
servidor mata o `journalctl` quando o navegador some (um batimento a cada 15 s percebe a aba fechada
num journal quieto). No máximo oito streams ficam abertos ao mesmo tempo.

**Filtros e resumo** em Meus apps: sob as abas, "Todos", "Com atualização" e "Com problema" são
botões que trazem a contagem, e uma linha diz quantos apps estão rodando, parados ou pausados. Um
serviço tem atualização quando há versão nova no upstream ou o repositório mudou desde a instalação;
problema é o que o selo mostra em vermelho (unit que falhou, loop de restart, container doente,
imagem que sumiu). Clicar de novo no filtro ativo o limpa, e trocar de aba também; a busca vale por
cima dele.

**Estado de falha** no card: uma unit que o systemd reiniciou, que falhou ou que espera para ser
reiniciada mostra o selo vermelho "loop de restart (7×)" ou "falhou (saída 125)", ou o amarelo
"reiniciou 2×" quando já se recuperou, com os detalhes ao passar o mouse e no painel: reinícios,
código de saída, resultado e a hora da última falha. Vem de um único `systemctl show` para todas as
units (`NRestarts`, `ExecMainStatus`, `Result`, `ExecMainExitTimestamp`) e está no `qh --catalog`
como `failure`. Um serviço parado de propósito nunca mostra isso.

**Iniciar, pausar e parar** (▶ ⏸ ■ em cada app instalado, em Meus apps e no painel) agem no
serviço inteiro. Iniciar sobe o que não está rodando e descongela o que está pausado; pausar
congela os containers que rodam com `podman pause` (as units seguem `active` para o systemd, o
app aparece como "pausado" e a memória continua alocada), e um reinício traz o app de volta rodando, já que os processos nunca
foram salvos; parar para todas as units do serviço juntas (descongelando antes um container
congelado, que ignora o SIGTERM) e as **mascara** (`systemctl --user mask --now`), que é o que
sobrevive a um reinício: as units são desejadas pelo `default.target`, então um stop simples é
desfeito no próximo boot. Iniciar desmascara e sobe. Um serviço mascarado aparece como "parado", não
como problema; o `qh --update` baixa a imagem nova e pula o restart (e avisa), e o `qh --remove`
tira a máscara para o nome poder ser instalado de novo. Mascarar não é enable/disable (regra 4): a
unit gerada mantém o próprio `[Install]`. Cada botão só fica
ativo onde faz algo. Rodam como jobs, então aparecem no histórico.

**Recursos** (o botão do cabeçalho, e uma dica depois de uma atualização) lista o que o
Podman guarda e nada usa: imagens, redes e volumes, com o espaço das imagens ("até":
camadas são compartilhadas). Cada atualização deixa a imagem anterior. "Sem uso" é mais
estrito que `podman image prune -a`: a imagem fica se um container a usa **ou se uma unit
instalada a pede em `Image=`**, então um serviço parado não baixa tudo de novo na próxima
partida. Rede fica se é a padrão, está em uso ou é declarada por um `.network`; volume só
sai quando nenhum container o monta e nenhum `.volume` o declara. Apagar pede duas vezes, e
volume (dados) pede a palavra digitada. No terminal: `python3 resources.py` para ver,
`prune images|networks|volumes --apply` para fazer.

**Funciona com** é uma sugestão no painel: `"works_with": ["grafana", "ntfy"]`
lista outras pastas de serviço que valem rodar junto, cada uma um link
para o seu painel, com ✓ quando instalada. Nunca é requisito (isso é o dono de uma
rede, que o `qh` já exige); o `check.py` reprova nome que não seja uma pasta.

**Podman mínimo**: uma unit com `Notify=healthy` exige o Podman 5.0, e `"min_podman": "5.4"`
sobe esse piso para um serviço que usa uma chave de Quadlet mais
nova. O `qh` avisa antes de instalar num host mais antigo e a loja mostra no
painel; não recusa. `QH_PODMAN_VERSION` substitui o que o host informa.

**Personalizar antes de instalar**: um app que não está instalado tem um botão Personalizar ao
lado de Instalar. O formulário é o mesmo, mas trabalha sobre a unit como o `qh` a escreveria (a do
repositório, renderizada para a regra de acesso em vigor); **Guardar para a instalação** confere a
escolha com as mesmas regras e o mesmo gerador do Quadlet, lembra dela, e a instalação a leva: ela é
validada de novo quando a instalação começa (uma ruim recusa a instalação antes de rodar qualquer
coisa) e gravada no drop-in logo depois de a unit existir, com a mesma volta atrás se o serviço não
subir. Só uma instalação leva uma, e só para units daquele app; nada é escrito no host até lá.

A **Personalizar** muda um serviço instalado sem tocar na unit do repositório:
portas, volumes, variáveis extras, dispositivos, capabilities extras e a
política de reinício, no desenho do formulário que o CasaOS tem para um app. A
mudança é um drop-in do Quadlet, `<unit>.container.d/50-store.conf`, ao lado da
unit. O `qh --update` não mexe nele e avisa (e avisa também quando a unit mudou
por baixo de uma personalização que zera uma lista, porque isso esconde o que é
novo), o `qh --status` marca o serviço, e o `qh --remove` leva o arquivo junto
com a unit. **Reverter**, ou apagar o arquivo, volta para a unit como o
repositório publica. A **Pré-visualização** mostra o arquivo exato e a linha do
`podman run` que o Quadlet faz dele; **Salvar e aplicar** grava, reinicia o
serviço e, se ele não subir, devolve o estado anterior e imprime as últimas
linhas do journal.

Só o que é novo é conferido, e o que a unit já tem é sempre aceito como está. Um
volume novo tem de ficar dentro de `~/.config/containers/volumes`, de uma pasta
que as units já pedem a você (`${MEDIA_DATA_DIR}`) ou de uma que você liste em
`~/.config/quadlet-homelab/store-roots` (um caminho por linha), e um **seletor de pasta** (o 📁 ao
lado do caminho do host) lista exatamente essas pastas e nada além: por caminho real, então um link
simbólico não leva para fora delas, sem pastas ocultas nem arquivos, e dá para digitar uma subpasta
nova (ela é criada quando a personalização é aplicada); uma porta tem de
estar a partir do piso sem privilégio e livre (não ser de outra unit nem estar
em uso); uma capability tem de estar numa lista curta (as padrão do Podman mais
`NET_RAW`, `SYS_NICE`, `MKNOD`, `AUDIT_WRITE`); um dispositivo tem de existir em
`/dev`. Não há campo de imagem ou tag, porque a versão é do repositório (regra
9), nem chave de privilégio: com o token da loja, qualquer das duas viraria um
shell no seu host. Para isso, edite a unit à mão. O arquivo `.env` continua em
**Configurar**; o formulário edita as linhas `Environment=`.

**Limites** (memória e CPU) só são oferecidos onde podem funcionar. Rootless, eles precisam que o
systemd do usuário delegue esses controladores, e onde ele não delega o `--memory` impede o
container de subir (`memory.swap.max: no such file or directory`), o que foi medido num host onde
só o `pids` é delegado. Por isso o formulário lê o `cgroup.controllers` do usuário e, quando ele
lista `memory` e `cpu`, mostra dois campos: **Memória** (`Memory=512m`, `2g`) e **CPUs**
(`PodmanArgs=--cpus=1.5`, que o Quadlet não tem chave para), gravados no mesmo drop-in e conferidos
contra a memória e o número de núcleos do host. Onde faltam os controladores os campos aparecem
desligados, com o motivo, e o servidor recusa salvar um limite de qualquer jeito. Um limite que a
própria unit traz não se tira por aqui. Vale na próxima partida do container. Confira o seu com
`cat /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.controllers`.
Delegá-los é uma mudança de root que este repositório não faz por você: um drop-in como
`/etc/systemd/system/user@.service.d/delegate.conf` com `[Service]` e `Delegate=cpu cpuset io
memory pids`, e depois sair e entrar de novo. Este caminho foi escrito e testado contra um
`cgroup.controllers` de mentira, não num host que delega.

O `store/test/ui.js` roda a página no Node contra um DOM de mentira, e o
`store/test/browser.js` a conduz num Chromium de verdade (`node
store/test/browser.js <url> <arquivo-do-token> <pasta-de-saída> [real|sandbox]`;
o `real` só lê e pré-visualiza, o `sandbox` também aplica, então aponte-o só
para uma loja iniciada com `--prefix`). Nenhum dos dois está no CI, que é só
Python.

Quem tiver o token instala e remove serviços como você. Trate-o como uma chave
SSH. Para revogar, apague o arquivo e reinicie o serviço.

`qh-store --prefix /tmp/test` aponta a loja para um sandbox, como o
`qh --prefix`. O `qh-store --selftest` cobre o login, as checagens das
requisições e uma instalação completa em sandbox.

// The store's page. Every string the server sends goes in through textContent:
// descriptions and command output come from files and processes, not from us.
"use strict";

const T = {
  pt: {
    search: "Buscar apps", tabApps: "Meus apps", tabStore: "Loja", all: "Todos", other: "Outros",
    noneInstalled: "Nenhum app instalado ainda.", goStore: "Abrir a Loja", manage: "Gerenciar",
    installedBadge: "instalado", deprecatedBadge: "descontinuado", deprecatedNote: "Descontinuado:",
    noInstall: "Não dá para instalar este app daqui.",
    play: "Iniciar / retomar", pause: "Pausar", stopApp: "Parar", pausedBadge: "pausado",
    notes: "Notas",
    settings: "Configurações", accessRule: "Como os apps são acessados", saveRule: "Salvar regra", applyRule: "Aplicar aos instalados",
    accessDesc: { local: "Só pela rede local (sem tsdproxy)", tailnet: "Só pela tailnet (fecha a porta da LAN)", both: "Rede local e tailnet" },
    power: "Servidor", powerDesc: "Reinicia ou desliga a máquina inteira, com todos os apps. Não funciona com uma tarefa em andamento.",
    powerReboot: "Reiniciar o servidor", powerOff: "Desligar o servidor", powerSure: "Confirmar", powerCancel: "Cancelar",
    powerRebooting: "Reiniciando… o painel volta sozinho quando o servidor responder.", powerOffDone: "Desligando. Para ligar de novo, só no botão da máquina.",
    ruleDefault: "Ainda não escolhida: vale tailnet.", ruleSaved: "Regra salva.",
    ruleDrift: (n, nomes) => `${n} serviço(s) instalado(s) não seguem esta regra: ${nomes}. Aplicar atualiza e reinicia cada um.`,
    tailnetOn: "Tailnet configurada: os endereços .ts.net aparecem nos apps.", tailnetOff: "Tailnet não configurada: os apps só abrem pelo endereço da rede local.",
    updateAll: (n) => `Atualizar todos (${n})`, updateAllSure: "Confirmar: reinicia cada um", updatingAll: "Atualizando…",
    purgeData: "Apagar também os dados, os secrets e o .env", purgeWarn: "Isto apaga os volumes do serviço, e não tem volta. Faça um backup antes se os dados importam.",
    pickFolder: "Escolher pasta", newFolder: "nova subpasta (opcional)", useFolder: "Usar esta pasta", up: "Subir",
    roots: "pastas permitidas", noSubfolders: "Sem subpastas aqui.", noRoots: "Nenhuma das pastas permitidas existe ainda: digite o caminho.",
    preIntro: "Antes de instalar: o que você escolher aqui é conferido agora e aplicado logo depois da instalação.",
    preSave: "Guardar para a instalação", preDiscard: "Descartar", preSaved: "Guardado: vai junto com a instalação.",
    preNone: "Nada mudou em relação ao padrão: nada a guardar.",
    preRides: (u) => `Personalização guardada para ${u}: será aplicada depois da instalação.`, pinnedOnHost: "versão no host",
    console: "Console", consoleFailed: "não foi possível abrir o console",
    consoleHint: "Um shell dentro do container (bash, ou sh). Clique na tela para digitar. Programas de tela cheia (vim, top) não funcionam.",
    logFilter: "Filtrar linhas…", logFollow: "seguir", logConnecting: "conectando…", logLive: "ao vivo", logEnded: "encerrado", logNoMatch: "(nenhuma linha casa com o filtro)",
    filterUpdates: "Com atualização", filterProblems: "Com problema",
    summaryLine: (r, p, z) => `${r} rodando · ${p} parado(s)${z ? ` · ${z} pausado(s)` : ""}`,
    failFailed: "falhou", failLoop: "reiniciando em loop", failRestarted: "reiniciou", failExit: "saída", failLast: "última falha",
    loopBadge: (n) => `loop de restart (${n}×)`, failedBadge: (c) => `falhou (saída ${c})`, restartedBadge: (n) => `reiniciou ${n}×`, stoppedBadge: "parado", ctlFailed: "Não foi possível:",
    backupFirst: "Backup antes",
    envType: { bool: "sim/não", number: "número", email: "e-mail", url: "URL", ip: "IP", password: "senha" },
    resources: "Recursos", resLoading: "Verificando o Podman…",
    files: "Arquivos", filesRoot: "Apps", filesEmpty: "Pasta vazia.", filesNone: "Nenhum app com dados próprios.", filesLink: "atalho (não é seguido)",
    filesDownload: "Baixar", filesBack: "Voltar à pasta", filesBinary: "Arquivo binário: só dá para baixar.", filesCut: (n) => `Mostrando só o começo (${n}).`,
    filesMore: "A pasta tem mais itens do que cabem na lista.", filesNote: "Mexer nos arquivos de um app que está rodando pode corromper os dados dele: pare o app antes de apagar ou trocar o que ele usa.",
    filesDenied: "Sem permissão para ler isto.",
    filesUnits: "Units (systemd)", filesEnv: "Variáveis (.env)",
    filesRO: "Somente leitura: dá para ver e baixar, não alterar. Para mudar uma unit use Personalizar; para um .env, Configurar. Os secrets nunca aparecem aqui.",
    rawTitle: "O .container (código)", rawRepo: "É o arquivo do repositório, como ele será instalado.", rawCustom: "É o seu .container, guardado ao lado das configurações do painel: as atualizações usam este, não o do repositório.",
    rawWarn: "Este é o arquivo que o systemd lê. Um .container escrito à mão pode executar comandos e abrir o acesso ao host. O painel confere a sintaxe e avisa o que você acrescentou ao do repositório, mas não impede.",
    rawCheck: "Verificar", rawRestore: "Voltar ao do repositório", rawCopy: "Copiar", rawCopied: "Copiado.", rawOk: "Sem problemas.", rawRunning: "O que roda agora (unit instalada e personalização)",
    rawAck: "Entendo os riscos e quero usar este .container", rawNeedAck: "Marque que entendeu os avisos para continuar.", rawFormOff: "Com um .container próprio, o formulário desta unidade não é aplicado: o que você quer mudar vai no código.",
    rawSaved: "Salvar este .container", rawDiff: "Diferente do repositório.", rawSame: "Igual ao repositório.", rawUnitReset: "O painel volta ao .container do repositório e reinicia o serviço.", rawChanged: "Edite o código ou use o formulário, não os dois ao mesmo tempo.",
    podmanTitle: "Podman", podmanLine: (v) => `Neste servidor: Podman ${v}.`,
    podmanLate: (v, rec) => `O repositório foi verificado no Podman ${rec}. As versões 6.1.1 a 6.1.3 corrigiram falhas de segurança (extração de arquivos fora da pasta, importação de imagens e volumes, imagens de checkpoint). Atualize o pacote do host quando puder: ${v} é mais antiga.`,
    podmanOk: (rec) => `Igual ou mais nova que a ${rec}, com a qual o repositório foi verificado.`,
    driftTitle: (units) => `O .container de ${units} mudou no repositório desde a instalação`, driftHint: "Atualizar escreve o arquivo novo e reinicia o serviço. A diferença (− o que roda agora, + o que o repositório diz):", driftNone: "Sem diferença.",
    legacyTitle: (velho, n) => `Uma instalação antiga do ${velho} foi encontrada (${n} apps)`,
    legacyBody: "Cada um deles agora é um app independente, com a própria pasta de dados e as próprias configurações. Migrar move os dados e as configurações para os apps novos (nada é copiado nem apagado, só renomeado), reescreve as units a partir do repositório e liga de novo o que estava rodando.",
    legacyButton: "Migrar", legacyRunning: "Migrando…", migrateAction: "Migração",
    prStep: (n, total) => `Passo ${n} de ${total}`, prElapsed: "decorrido", prDone: "Concluído", prFailed: "Falhou neste passo", prWaiting: "esperando…",
    stMkdir: "Criar as pastas", stMkdirData: "Criar a pasta dos dados", stMkdirUnits: "Criar a pasta das units", stCopyUnit: "Copiar a unit", stCopyEnv: "Copiar as configurações (.env)", stSecret: "Criar o secret", stChown: "Ajustar o dono dos dados", stReload: "Recarregar o systemd",
    stRestart: (u) => `Reiniciar ${u}`, stHealthy: (n) => `Esperar ficar saudável (até ${n}s)`, stKeep: "Guardar a versão atual, para poder voltar", stPull: "Baixar a imagem", stStart: (u) => `Iniciar ${u}`,
    stStop: (u) => `Parar ${u}`, stRemoveUnit: "Remover a unit", stBackup: "Empacotar os dados", stRestore: "Restaurar os dados",
    prSteps: "Passos", prTerminal: "Terminal", prView: "Como mostrar o andamento",
    fGrid: "Grade", fList: "Lista", fColName: "Nome", fColSize: "Tamanho", fColDate: "Modificado", fPlaces: "Locais",
    fUpload: "Enviar", fNewFolder: "Nova pasta", fRename: "Renomear", fCopy: "Copiar", fCut: "Recortar", fPaste: "Colar", fDelete: "Apagar",
    fSure: (n) => `Confirmar: apagar ${n} ${n === 1 ? "item" : "itens"}`, fCancel: "Cancelar", fOk: "OK", fName: "Nome", fSel: (n) => `${n} selecionado${n === 1 ? "" : "s"}`,
    fSending: (i, n, nome) => `Enviando ${i} de ${n}: ${nome}`, fSent: (n) => `${n} enviado${n === 1 ? "" : "s"}.`, fDrop: "Solte os arquivos aqui para enviar", fReadHere: "Escolha uma pasta de um app para mexer nos arquivos.",
    fEdit: "Editar", fSave: "Salvar", fSaved: "Salvo.", fClip: (n, modo) => `${n} ${modo === "move" ? "recortado" : "copiado"}${n === 1 ? "" : "s"}`, fExists: "Já existe.", fRefresh: "Atualizar", fSelectAll: "Selecionar tudo",
    resUsage: "Espaço por app", resUsageNote: "Quanto os dados de cada app ocupam em disco (as pastas em volumes/; uma pasta sua, como a de mídia, não entra).",
    resUsageRefresh: "Recalcular", resUsageLoading: "Calculando…", resUsageNone: "Nenhum app com dados próprios.", resUsageTotal: "Total",
    powerLater: "Agendar", powerWhen: { "15": "em 15 minutos", "60": "em 1 hora", "240": "em 4 horas", at: "num horário…" },
    powerAction: "O quê", powerSchedule: "Agendar", powerScheduled: (acao, quando) => `${acao === "reboot" ? "Reiniciar" : "Desligar"} agendado para ${quando}.`, powerUnschedule: "Cancelar agendamento",
    hTab: "Saúde", hStatus: { healthy: "saudável", unhealthy: "com problema", starting: "iniciando", none: "sem sonda" }, hNotRunning: "O container não está rodando.",
    hStreak: (n) => `${n} ${n === 1 ? "falha seguida" : "falhas seguidas"}`, hEvery: "A cada", hTimeout: "tempo máximo", hRetries: "tentativas", hStartPeriod: "janela de início", hCommand: "Comando",
    hOnFail: "Quando fica doente", hOnFailNone: "nada: o systemd não age (a unit pode pedir `HealthOnFailure=kill` em Personalizar → código)", hRun: "Rodar agora", hRunning: "Rodando…",
    hResult: (rc) => (rc === 0 ? "A sonda passou." : `A sonda falhou (saída ${rc}).`), hRuns: "Últimas execuções", hStartedAt: "Início", hExit: "Saída", hOutput: "O que imprimiu", hNoRuns: "Nenhuma execução ainda.",
    rtTab: "Detalhes", rtIntro: "O que roda de verdade, como o Podman o vê. O Personalizar mostra o que a unit diz; aqui está o resultado.", rtImage: "Imagem", rtDigest: "Digest", rtCommand: "Comando", rtUser: "Usuário", rtWorkdir: "Pasta de trabalho",
    rtCreated: "Criado", rtStarted: "Iniciado", rtRestarts: "Reinícios", rtNetworks: "Redes", rtPorts: "Portas publicadas", rtNoPorts: "Nenhuma: só se chega por uma rede.", rtMounts: "Montagens", rtRW: "leitura e escrita", rtRO: "só leitura",
    rtEnv: "Variáveis de ambiente", rtShow: "Mostrar os valores", rtHide: "Esconder os valores", rtSecret: "secret", rtRevealNote: "Os valores aparecem mascarados: um `Secret=` do tipo env fica no ambiente do container.",
    rtLimits: "Limites e permissões", rtReadOnly: "sistema de arquivos somente leitura", rtPids: "processos", rtMemory: "memória", rtCapsDrop: "capacidades removidas", rtCapsAdd: "capacidades acrescentadas", rtSecurity: "segurança",
    forceStop: "Parar à força", forceRestart: "Reiniciar à força", forceSure: "Confirmar: mata na hora", forceHint: "Mata o container na hora (SIGKILL) e depois para ou reinicia a unit. Serve para quando ele não responde ao stop; pode perder o que não foi gravado.",
    imgTitle: "Todas as imagens", imgNote: "Tamanho em disco, quem usa, quando foi construída e o que a própria imagem diz de si. Só se apaga a que ninguém usa e nenhuma unit instalada pede.",
    imgName: "Imagem", imgUsedBy: "Usada por", imgBuilt: "Criada", imgVersion: "Versão", imgRevision: "Revisão", imgNoUse: "ninguém", imgWanted: "uma unit pede", imgInUse: "em uso", imgFree: "sem uso",
    imgDetails: "Detalhes", imgHistory: "Camadas", imgRemove: "Apagar", imgSure: "Confirmar", imgRemoving: "Apagando…", imgNone: "Nenhuma imagem.",
    resImages: "Imagens sem uso", resNetworks: "Redes sem uso", resVolumes: "Volumes sem uso",
    resImagesNote: (n, s) => `${n} imagem(ns) que nenhuma unit instalada nem container usa, até ${s}. Cada atualização deixa a anterior aqui. O espaço real pode ser menor: camadas são compartilhadas entre imagens.`,
    resNone: "Nada sobrando.", resRemove: "Apagar", resSure: "Confirmar", resVolumesWarn: "Volume guarda dados. Digite volumes para apagar:",
    cleanHint: (n, s) => `${n} imagem(ns) sem uso ocupam até ${s}.`, cleanOpen: "Limpar…",
    resWorking: "Apagando…",
    permsTitle: "Permissões", perm: {
      privileged: "Container privilegiado: tem acesso quase total ao host",
      podman_socket: "Controla todo o seu Podman: vê, para e cria qualquer container",
      host_network: "Usa a rede do host, sem isolamento de rede",
      cgroupns_host: "Enxerga os cgroups do host",
      selinux_off: "Sem o rótulo SELinux: pode ler volumes de outros apps",
      devices: "Acessa dispositivos do host", capabilities: "Capabilities extras do kernel" },
    alerts: "Alertas", alertsDesc: "Avisa um tópico do ntfy quando algo falha. Desligado por padrão; o mesmo aviso não se repete dentro do intervalo.",
    alertsOn: "Ativar alertas", alertServer: "Servidor ntfy (ex.: https://ntfy.exemplo.org)", alertTopic: "Tópico", alertToken: "Token (opcional)",
    alertTokenSet: "já definido; deixe em branco para manter", alertCooldown: "Não repetir antes de (horas)", alertDisk: "Disco acima de (%)",
    alertKinds: { failed: "Unit falhou", unhealthy: "Container unhealthy", restart_loop: "Loop de reinício", backup: "Backup falhou",
                  update: "Versão nova do projeto", disk: "Disco cheio" },
    alertSave: "Salvar alertas", alertTest: "Enviar teste", alertSaved: "Alertas salvos.", alertTested: "Teste enviado.",
    optionsTitle: "Opções de instalação", optionLocked: "escolhido na instalação; mudar move os dados (remova o app com os dados e instale de novo)",
    newInstance: "Nova instância", instanceName: "Nome da instância (letras minúsculas, números e -)", instanceCreate: "Criar instância",
    instanceOf: (b) => `instância de ${b}`,
    readyToInstall: (n) => `Pronto para instalar ${n}. Leva cerca de um minuto.`,
    planTitle: "O que vai acontecer",
    dockerImage: "Imagem Docker", dockerTag: "Tag", containerName: "Nome do contêiner", noLimit: "sem limite", latestPinned: "a última versão",
    emptyRows: "Clique em “+” para adicionar um.", hHost: "Host", hContainer: "Contêiner", hProto: "Protocolo", hIp: "IP (opcional)", hKey: "Chave", hValue: "Valor", hLabel: "Rótulo",
    qlPlaceholder: "Buscar apps… (Enter abre, Esc fecha)", qlOpen: "Abrir", qlStore: "Ver na loja", qlManage: "Gerenciar", qlWeb: (q) => `Buscar “${q}” na web`, qlNone: "Nenhum app com esse nome.",
    appearance: "Aparência", apTheme: "Tema", apThemes: { system: "Como o sistema", light: "Claro", dark: "Escuro" }, apAccent: "Cor de destaque",
    apAccents: { orange: "Laranja", blue: "Azul", green: "Verde", teal: "Petróleo", purple: "Roxo", pink: "Rosa", red: "Vermelho", slate: "Grafite" },
    apCard: "Cartões", apCards: { shadow: "Com sombra", hairline: "Com borda fina" }, apDensity: "Densidade", apDensities: { comfortable: "Confortável", compact: "Compacta" },
    apBg: "Imagem de fundo", apBgPick: "Escolher imagem…", apBgRemove: "Tirar o fundo", apBgBlur: "Desfoque", apBgDim: "Véu sobre a imagem",
    apBgHint: "PNG, JPEG ou WebP, até 8 MB. Fica no servidor, para todos os navegadores.", apSaved: "Aparência salva.",
    monDown: "não responde", monStatus: (c) => `responde com erro ${c}`, monMs: (ms) => `responde em ${ms} ms`,
    svcField: { photos: "fotos", videos: "vídeos", storage: "armazenamento", queries: "consultas", blocked: "bloqueadas", blocked_pct: "bloqueado",
      latency: "latência", documents: "documentos", inbox: "na caixa de entrada", up: "no ar", down: "fora do ar", wanted: "faltando", queued: "na fila",
      series: "séries", movies: "filmes", streams: "tocando agora", songs: "músicas" },
    svcNames: { immich: "Immich", adguard: "AdGuard Home", paperless: "Paperless-ngx", "uptime-kuma": "Uptime Kuma", sonarr: "Sonarr", radarr: "Radarr", jellyfin: "Jellyfin" },
    svcTitle: "Números do app", svcSetup: "Configurar widget", svcConnect: "Conecte para ver os números do app aqui.", svcSave: "Salvar", svcForget: "Esquecer",
    svcKey: "Chave de API", svcUser: "Usuário", svcPassword: "Senha", svcSlug: "Slug da página de status", svcUrl: "Endereço (opcional)",
    svcKeyKept: "já definida; deixe em branco para manter", svcNoUrl: "Sem endereço: o app não tem uma página publicada.",
    svcHelp: { immich: "Em Immich: Conta → Chaves de API, com a permissão server.statistics.", adguard: "O usuário e a senha de entrar no AdGuard Home.",
      paperless: "Em Paperless: Meu perfil → Token de API.", "uptime-kuma": "Crie uma página de status no Uptime Kuma e use o slug do endereço dela.",
      sonarr: "Em Sonarr: Settings → General → API Key.", radarr: "Em Radarr: Settings → General → API Key.", jellyfin: "Em Jellyfin: Painel → Chaves de API." },
    svcSecure: "A chave fica no servidor; o navegador só recebe os números.",
    netTitle: "Rede (tailnet)", netModes: { local: "Só local", tailscale: "Tailscale", headscale: "Headscale" },
    netDesc: { local: "Sem tailnet: os apps abrem pela porta na rede local e o tsdproxy fica desligado. É o jeito mais simples.",
      tailscale: "O host entra numa tailnet do Tailscale e o tsdproxy dá a cada app um nome HTTPS (um nome por app).",
      headscale: "Uma rede sua, sem conta em terceiros: o projeto roda o servidor Headscale, o host e o tsdproxy entram nele. Os apps ficam em HTTP na tailnet (o Headscale não emite certificado HTTPS)." },
    netState: "Como está", netTs: "Tailscale no host", netHs: "Servidor Headscale", netTsd: "tsdproxy",
    netNotInstalled: "não instalado", netNotRunning: "parado", netRunning: "rodando", netInstalledOnly: "instalado, parado", netNoKey: "sem a chave (authkey) ainda",
    netTailnet: "Nome da rede", netTailnetHint: "os apps ganham nomes nela", netServer: "Endereço do servidor Headscale", netServerHint: "um endereço que seus aparelhos alcancem (a LAN serve em casa)",
    netApply: "Aplicar", netNeed: "Falta no host (uma vez, com sudo):", netNowTs: "O Tailscale vai fazer o login: se aparecer um link abaixo, abra-o.", netDone: "Rede aplicada.",
    netHttps: "Os apps que exigem HTTPS não funcionam com Headscale:",
    pageApps: "Meus apps", hello2: ["Bom dia", "Boa tarde", "Boa noite"], helloLine: (n, u) => `${n} apps${u ? `, ${u} com atualização` : ""}. Clique com o botão direito num app para ver o estado.`,
    recent: "Usados recentemente", allApps: "Todos os apps", navCollapse: "Recolher a barra lateral", navExpand: "Expandir a barra lateral",
    hStat: { cpu: "Processador", mem: "Memória", disk: "Disco", net: "Rede" }, ctxStart: "Iniciar", ctxResume: "Retomar", ctxPause: "Pausar",
    apIconSize: "Tamanho dos ícones", apIconSizes: { small: "Pequeno", medium: "Médio", large: "Grande" }, apDepth: "Fundo", apDepths: { flat: "Chapado", soft: "Com profundidade e cor" },
    remove: "Remover", 
    linkName: "Nome", linkUrl: "https://…", linkBad: "Use um endereço http:// ou https://",
    updateAvailable: "Atualização disponível",
    getApp: "Instalar", factCategory: "Categoria", factAuthor: "Desenvolvedor", factSize: "Download", factArch: "Arquitetura", factVersion: "Versão", installing: (n) => `Instalando ${n}`, inBackground: "Continuar em segundo plano", installNow: "Instalar agora", advanced: "Avançado", rolledBack: "voltou à versão anterior", techDetails: "Detalhes técnicos", logTitle: "O que foi feito", closeLabel: "Fechar",
    httpsNeeded: "precisa de HTTPS",
    httpsWarn: "Este app precisa de HTTPS: pela rede local (HTTP) o cofre e o service worker falham sem avisar. Use o acesso pela tailnet.",
    podmanOld: (need, host) => `Este app precisa do Podman ${need}+; o host tem ${host}. Atualize o Podman antes de instalar.`,
    hostCpu: "carga", hostMem: "RAM", hostUp: "ligado há",
    trialLabel: "Experimentar", trialKeep: "Manter", trialBadge: "experimento",
    trialNone: "instalar de vez", trialReboot: "até reiniciar o servidor",
    trialPurge: "apagar também os dados no fim",
    trialHint: "Remove sozinho no fim, por um timer do systemd. Só o serviço pedido, não o que ele trouxe junto.",
    trialEnds: (q, purge) => `Experimento: ${q}. Os dados ${purge ? "serão apagados" : "ficam"} no fim.`,
    trialIn: (s) => `termina em ${s}`, trialAtReboot: "termina no próximo reinício",
    trialUnits: { h: "h", d: "dias" },
    tabSummary: "Resumo", tabConfig: "Configurar", removeHint: "Remover o app e, se você quiser, os dados dele",
    cfgEnvHint: "Variáveis e opções do app", cfgLoginHint: "Usuário e senha de entrada", cfgCustomHint: "Portas, volumes e o .container", cfgInstanceHint: "Outra cópia do app, com dados próprios",
    customize: "Personalizar", customizedBadge: "personalizado", cPorts: "Portas", cVolumes: "Volumes",
    cEnv: "Variáveis de ambiente", cDevices: "Dispositivos", cCaps: "Permissões extras do container",
    cRestart: "Política de reinício", add: "Adicionar", fromUnit: "(vem da unit)", removeRow: "Remover",
    ipOpt: "IP (opcional)", hostPort: "Porta no host", contPort: "Porta no container",
    hostPath: "Pasta no host", contPath: "Caminho no container", labelZ: "rótulo privado (Z)",
    labelz: "compartilhado (z)", labelNone: "sem rótulo", readOnly: "só leitura", envKey: "NOME",
    envValue: "valor", devPath: "/dev/…", previewBtn: "Pré-visualizar", saveApply: "Salvar e aplicar",
    revertBtn: "Reverter ao padrão", fileToWrite: "Arquivo que será gravado", generated: "Comando que o Quadlet gera",
    nothingChanged: "Nada diferente da unit do repositório.", filePath: "Arquivo",
    custIntro: "Muda esta instalação sem tocar na unit do repositório: a mudança fica num arquivo ao lado, " +
      "sobrevive ao Atualizar e some ao Reverter. Imagem e versão são do repositório, e não há chave de privilégio " +
      "(para isso, edite a unit à mão).",
    portsHint: "Publicar uma porta abre o app na rede local, qualquer que seja a regra de acesso.",
    volumesHint: (r) => `Pastas permitidas para volumes novos: ${r.join(", ")}. Para liberar outra, escreva o ` +
      "caminho em ~/.config/quadlet-homelab/store-roots.",
    custEnvHint: "As variáveis do arquivo .env ficam em Configurar; aqui entram as extras.",
    capsHint: "Por padrão o container começa sem nenhuma permissão especial do sistema. Cada caixa devolve uma, só para este app. Em geral não precisa mexer: marque só se o log do app reclamar de uma operação negada. Para uma que não esteja na lista, edite a unit à mão.",
    capInfo: { CHOWN: "trocar o dono de arquivos", DAC_OVERRIDE: "ignorar as permissões dos arquivos", FOWNER: "agir como dono dos arquivos", FSETID: "manter os bits setuid/setgid",
      KILL: "mandar sinais a processos de outro usuário", NET_BIND_SERVICE: "escutar em portas abaixo de 1024", NET_RAW: "sockets crus (ping e ferramentas de rede)",
      SETFCAP: "definir permissões em arquivos", SETGID: "trocar o grupo do processo", SETPCAP: "mexer nas permissões de processos", SETUID: "trocar o usuário do processo",
      SYS_CHROOT: "usar chroot", SYS_NICE: "mudar a prioridade de processos", MKNOD: "criar arquivos de dispositivo", AUDIT_WRITE: "escrever no log de auditoria" },
    limitsOff: "O systemd do seu usuário não delega os controladores memory e cpu, e com um limite o container não " +
      "sobe. Ligar é uma mudança de root (Delegate= no user@.service): veja docs/tools.md.",
    cLimits: "Limites", limMemory: "Memória máxima", limCpus: "CPUs", limMemoryHint: "ex.: 512m, 2g",
    limCpusHint: "ex.: 1.5 (um núcleo e meio)", limitsHint: "Valem na próxima partida do container. Vazio, sem limite.",
    baseChanged: "A unit do repositório mudou desde que você personalizou. A personalização zera listas e pode " +
      "esconder o que é novo: reveja e salve de novo.",
    none: "Nenhum app encontrado.", installed: "instalado", running: "rodando",
    attention: "atenção", changed: "repo mudou", install: "Instalar", update: "Atualizar",
    remove: "Remover", logs: "Logs", open: "Abrir", confirm: "Confirmar", cancel: "Cancelar",
    plan: "Plano (nada foi feito ainda)", working: "Executando…", done: "Concluído.",
    failed: "Terminou com erro", unit: "Unit", service: "systemd", container: "Container",
    repo: "Repo", start: "Iniciar", stop: "Parar", restart: "Reiniciar",
    secretHint: "Vazio = pular e criar depois à mão (ver o README).",
    exists: "já existe — vazio mantém o atual",
    removeNote: "Remove as units e para o serviço. Volumes, secrets e .env ficam. O nó da tailnet não é desregistrado: isso é no admin do Tailscale.",
    busy: "Outra tarefa está rodando. Espere ela terminar.",
    synced: "em dia", duplicated: "duplicada",
    installedTag: "Instalada", upstream: "Upstream", newVersion: "nova versão",
    gone: "imagem sumiu", checking: "verificando upstream…", checked: "upstream verificado",
    recheck: "Verificar agora", upToDate: "atualizado", pending: "release sem imagem ainda",
    login: "Login", user: "Usuário", password: "Senha", show: "Mostrar", hide: "Ocultar",
    copy: "Copiar", copied: "Copiado", noLogin: "Sem credencial para mostrar (o secret ainda não existe).",
    backups: "Backups", backupNow: "Fazer backup agora", download: "Baixar", restoreAction: "Restaurar",
    upload: "Enviar backup", noBackups: "Nenhum backup ainda.", backupDir: "Pasta",
    backupNote: "O backup para o serviço, empacota os dados e sobe de novo.",
    restoreNote: "Restaurar SOBRESCREVE os dados atuais com os do arquivo, sem volta.",
    typeToConfirm: "Digite o nome do serviço para confirmar:",
    notesFrom: "Releases desde a instalada", noNotes: "Nenhuma release nova para ler.",
    onGithub: "ver no GitHub",
    upgradeTo: (v) => `Atualizar para ${v}`,
    nothingToDo: "Nada a fazer: o instalado já é igual ao que o repositório fixa.",
    installWith: (deps) => `Instalar (com ${deps})`,
    requiresNote: (deps) => `Este app precisa de ${deps}, que ainda não está instalado. ` +
      `A instalação instala antes, na ordem certa.`,
    access: "Acesso", followRule: (m) => `Seguir a regra (${m})`,
    modes: { local: "Rede local", tailnet: "Tailnet", both: "Rede local e tailnet" },
    configure: "Configurar", envSave: "Salvar e reiniciar", envHint: "Marque para ativar uma opção; desmarcar a comenta.",
    envNote: "Salvar reinicia o serviço (se estiver rodando). O arquivo anterior fica em .bak.",
    noEnv: "Este serviço não tem arquivo de configuração para editar.", active: "ativa",
    disk: "Disco", cpu: "CPU", mem: "Memória", runsOn: "Roda em", counting: "calculando…",
    noArm: (host, units) => `Sem imagem para ${host}: ${units}. Não vai rodar neste servidor.`,
    history: "Histórico", noHistory: "Nenhuma ação registrada ainda.", when: "Quando", what: "Ação", result: "Resultado",
    took: "Duração", from: "de", output: "Saída",
    act: { pause: "Pausar", resume: "Retomar", install: "Instalar", update: "Atualizar", upgrade: "Atualizar versão", remove: "Remover", backup: "Backup",
           restore: "Restaurar", access: "Acesso", env: "Configuração", start: "Iniciar", stop: "Parar", restart: "Reiniciar",
           customize: "Personalizar", revert: "Reverter", prune: "Limpar", "custom-unit": ".container próprio", migrate: "Migração", "force-stop": "Parada à força", "force-restart": "Reinício à força", "image-rm": "Imagem apagada" },
    link: { repo: "Projeto", docs: "Documentação", issues: "Problemas", releases: "Releases", image: "Imagem", recipe: "Receita neste repositório" },
    shots: "Capturas de tela",
    lang: "English",
  },
  en: {
    search: "Search apps", tabApps: "My apps", tabStore: "Store", all: "All", other: "Other",
    noneInstalled: "No app installed yet.", goStore: "Open the Store", manage: "Manage",
    installedBadge: "installed", deprecatedBadge: "discontinued", deprecatedNote: "Discontinued:",
    noInstall: "It cannot be installed from here.",
    play: "Start / resume", pause: "Pause", stopApp: "Stop", pausedBadge: "paused",
    notes: "Notes",
    settings: "Settings", accessRule: "How apps are reached", saveRule: "Save rule", applyRule: "Apply to the installed",
    accessDesc: { local: "Local network only (no tsdproxy)", tailnet: "Tailnet only (closes the LAN port)", both: "Local network and tailnet" },
    power: "Server", powerDesc: "Restarts or shuts down the whole machine, with every app. It does not work while a task is running.",
    powerReboot: "Restart the server", powerOff: "Shut down the server", powerSure: "Confirm", powerCancel: "Cancel",
    powerRebooting: "Restarting… the panel comes back by itself when the server answers.", powerOffDone: "Shutting down. To turn it on again, use the machine's button.",
    ruleDefault: "Not chosen yet: tailnet applies.", ruleSaved: "Rule saved.",
    ruleDrift: (n, nomes) => `${n} installed service(s) do not follow this rule: ${nomes}. Applying updates and restarts each one.`,
    tailnetOn: "Tailnet set: the .ts.net addresses show up on the apps.", tailnetOff: "Tailnet not set: apps open only at their local-network address.",
    updateAll: (n) => `Update all (${n})`, updateAllSure: "Confirm: restarts each one", updatingAll: "Updating…",
    purgeData: "Also delete the data, the secrets and the .env", purgeWarn: "This deletes the service's volumes, with no way back. Take a backup first if the data matters.",
    pickFolder: "Choose folder", newFolder: "new sub-folder (optional)", useFolder: "Use this folder", up: "Up",
    roots: "permitted folders", noSubfolders: "No sub-folders here.", noRoots: "None of the permitted folders exists yet: type the path.",
    preIntro: "Before installing: what you choose here is checked now and applied right after the install.",
    preSave: "Keep for the install", preDiscard: "Discard", preSaved: "Kept: it goes with the install.",
    preNone: "Nothing differs from the default: nothing to keep.",
    preRides: (u) => `Customization kept for ${u}: it will be applied after the install.`, pinnedOnHost: "version on the host",
    console: "Console", consoleFailed: "could not open the console",
    consoleHint: "A shell inside the container (bash, or sh). Click the screen to type. Full-screen programs (vim, top) do not work.",
    logFilter: "Filter lines…", logFollow: "follow", logConnecting: "connecting…", logLive: "live", logEnded: "ended", logNoMatch: "(no line matches the filter)",
    filterUpdates: "With updates", filterProblems: "With problems",
    summaryLine: (r, p, z) => `${r} running · ${p} stopped${z ? ` · ${z} paused` : ""}`,
    failFailed: "failed", failLoop: "restart loop", failRestarted: "restarted", failExit: "exit", failLast: "last failure",
    loopBadge: (n) => `restart loop (${n}×)`, failedBadge: (c) => `failed (exit ${c})`, restartedBadge: (n) => `restarted ${n}×`, stoppedBadge: "stopped", ctlFailed: "Could not:",
    backupFirst: "Back up first",
    envType: { bool: "yes/no", number: "number", email: "email", url: "URL", ip: "IP", password: "password" },
    resources: "Resources", resLoading: "Asking Podman…",
    files: "Files", filesRoot: "Apps", filesEmpty: "Empty folder.", filesNone: "No app with data of its own.", filesLink: "link (not followed)",
    filesDownload: "Download", filesBack: "Back to the folder", filesBinary: "A binary file: it can only be downloaded.", filesCut: (n) => `Showing only the start (${n}).`,
    filesMore: "The folder has more items than the list holds.", filesNote: "Changing the files of a running app can corrupt its data: stop the app before deleting or replacing what it uses.",
    filesDenied: "No permission to read this.",
    filesUnits: "Units (systemd)", filesEnv: "Environment (.env)",
    filesRO: "Read only: you can look and download, not change. To change a unit use Customize; for a .env, Configure. The secrets never show here.",
    rawTitle: "The .container (code)", rawRepo: "This is the repository's file, as it will be installed.", rawCustom: "This is your own .container, kept beside the panel's settings: updates use it, not the repository's.",
    rawWarn: "This is the file systemd reads. A hand-written .container can run commands and open the host up. The panel checks the syntax and flags what you added to the repository's, but does not stop you.",
    rawCheck: "Check", rawRestore: "Back to the repository's", rawCopy: "Copy", rawCopied: "Copied.", rawOk: "No problems.", rawRunning: "What runs now (installed unit and customization)",
    rawAck: "I understand the risks and want to use this .container", rawNeedAck: "Tick that you understood the warnings to go on.", rawFormOff: "With your own .container the form of this unit is not applied: what you want to change goes in the code.",
    rawSaved: "Save this .container", rawDiff: "Different from the repository's.", rawSame: "Same as the repository's.", rawUnitReset: "The panel goes back to the repository's .container and restarts the service.", rawChanged: "Edit the code or use the form, not both at once.",
    podmanTitle: "Podman", podmanLine: (v) => `On this server: Podman ${v}.`,
    podmanLate: (v, rec) => `The repository was verified on Podman ${rec}. Versions 6.1.1 to 6.1.3 fixed security flaws (files written outside a folder, image and volume imports, checkpoint images). Update the host package when you can: ${v} is older.`,
    podmanOk: (rec) => `The same as or newer than ${rec}, which the repository was verified on.`,
    driftTitle: (units) => `The .container of ${units} changed in the repository since the install`, driftHint: "Updating writes the new file and restarts the service. The difference (− what runs now, + what the repository says):", driftNone: "No difference.",
    legacyTitle: (velho, n) => `An old install of ${velho} was found (${n} apps)`,
    legacyBody: "Each of them is now an independent app, with its own data folder and its own settings. Migrating moves the data and the settings to the new apps (nothing is copied or deleted, only renamed), writes the units again from the repository and starts what was running again.",
    legacyButton: "Migrate", legacyRunning: "Migrating…", migrateAction: "Migration",
    prStep: (n, total) => `Step ${n} of ${total}`, prElapsed: "elapsed", prDone: "Done", prFailed: "Failed at this step", prWaiting: "waiting…",
    stMkdir: "Create the folders", stMkdirData: "Create the data folder", stMkdirUnits: "Create the units folder", stCopyUnit: "Copy the unit", stCopyEnv: "Copy the settings (.env)", stSecret: "Create the secret", stChown: "Set the owner of the data", stReload: "Reload systemd",
    stRestart: (u) => `Restart ${u}`, stHealthy: (n) => `Wait until it is healthy (up to ${n}s)`, stKeep: "Keep the current version, to be able to go back", stPull: "Pull the image", stStart: (u) => `Start ${u}`,
    stStop: (u) => `Stop ${u}`, stRemoveUnit: "Remove the unit", stBackup: "Pack the data", stRestore: "Restore the data",
    prSteps: "Steps", prTerminal: "Terminal", prView: "How to show the progress",
    fGrid: "Grid", fList: "List", fColName: "Name", fColSize: "Size", fColDate: "Modified", fPlaces: "Places",
    fUpload: "Upload", fNewFolder: "New folder", fRename: "Rename", fCopy: "Copy", fCut: "Cut", fPaste: "Paste", fDelete: "Delete",
    fSure: (n) => `Confirm: delete ${n} ${n === 1 ? "item" : "items"}`, fCancel: "Cancel", fOk: "OK", fName: "Name", fSel: (n) => `${n} selected`,
    fSending: (i, n, nome) => `Uploading ${i} of ${n}: ${nome}`, fSent: (n) => `${n} uploaded.`, fDrop: "Drop the files here to upload", fReadHere: "Open a folder of an app to work on its files.",
    fEdit: "Edit", fSave: "Save", fSaved: "Saved.", fClip: (n, modo) => `${n} ${modo === "move" ? "cut" : "copied"}`, fExists: "Already exists.", fRefresh: "Refresh", fSelectAll: "Select all",
    resUsage: "Space per app", resUsageNote: "How much each app's data takes on disk (the folders under volumes/; a folder of yours, such as the media one, is not counted).",
    resUsageRefresh: "Recalculate", resUsageLoading: "Calculating…", resUsageNone: "No app with data of its own.", resUsageTotal: "Total",
    powerLater: "Schedule", powerWhen: { "15": "in 15 minutes", "60": "in 1 hour", "240": "in 4 hours", at: "at a time…" },
    powerAction: "What", powerSchedule: "Schedule", powerScheduled: (acao, quando) => `${acao === "reboot" ? "Restart" : "Shutdown"} scheduled for ${quando}.`, powerUnschedule: "Cancel the schedule",
    hTab: "Health", hStatus: { healthy: "healthy", unhealthy: "unhealthy", starting: "starting", none: "no probe" }, hNotRunning: "The container is not running.",
    hStreak: (n) => `${n} failing in a row`, hEvery: "Every", hTimeout: "timeout", hRetries: "retries", hStartPeriod: "start period", hCommand: "Command",
    hOnFail: "When it turns unhealthy", hOnFailNone: "nothing: systemd does not act (the unit can ask for `HealthOnFailure=kill` in Customize → code)", hRun: "Run now", hRunning: "Running…",
    hResult: (rc) => (rc === 0 ? "The probe passed." : `The probe failed (exit ${rc}).`), hRuns: "Last runs", hStartedAt: "Started", hExit: "Exit", hOutput: "What it printed", hNoRuns: "No run yet.",
    rtTab: "Details", rtIntro: "What really runs, as Podman has it. Customize shows what the unit says; this is the result.", rtImage: "Image", rtDigest: "Digest", rtCommand: "Command", rtUser: "User", rtWorkdir: "Working folder",
    rtCreated: "Created", rtStarted: "Started", rtRestarts: "Restarts", rtNetworks: "Networks", rtPorts: "Published ports", rtNoPorts: "None: it is reached over a network only.", rtMounts: "Mounts", rtRW: "read and write", rtRO: "read only",
    rtEnv: "Environment variables", rtShow: "Show the values", rtHide: "Hide the values", rtSecret: "secret", rtRevealNote: "Values are masked: a `Secret=` of type env ends up in the container's environment.",
    rtLimits: "Limits and permissions", rtReadOnly: "read-only filesystem", rtPids: "processes", rtMemory: "memory", rtCapsDrop: "capabilities dropped", rtCapsAdd: "capabilities added", rtSecurity: "security",
    forceStop: "Force stop", forceRestart: "Force restart", forceSure: "Confirm: kills at once", forceHint: "Kills the container at once (SIGKILL), then stops or restarts the unit. For when it does not answer the stop; what was not written is lost.",
    imgTitle: "All images", imgNote: "Disk size, who uses it, when it was built and what the image says about itself. Only an image that nobody uses and no installed unit asks for can be deleted.",
    imgName: "Image", imgUsedBy: "Used by", imgBuilt: "Created", imgVersion: "Version", imgRevision: "Revision", imgNoUse: "nobody", imgWanted: "a unit asks for it", imgInUse: "in use", imgFree: "unused",
    imgDetails: "Details", imgHistory: "Layers", imgRemove: "Delete", imgSure: "Confirm", imgRemoving: "Deleting…", imgNone: "No images.",
    resImages: "Unused images", resNetworks: "Unused networks", resVolumes: "Unused volumes",
    resImagesNote: (n, s) => `${n} image(s) that no installed unit or container uses, up to ${s}. Every update leaves the previous one here. The real space may be less: layers are shared between images.`,
    resNone: "Nothing left over.", resRemove: "Delete", resSure: "Confirm", resVolumesWarn: "A volume holds data. Type volumes to delete:",
    cleanHint: (n, s) => `${n} unused image(s) take up to ${s}.`, cleanOpen: "Clean up…",
    resWorking: "Deleting…",
    permsTitle: "Permissions", perm: {
      privileged: "Privileged container: near-total access to the host",
      podman_socket: "Controls all of your Podman: sees, stops and creates any container",
      host_network: "Uses the host network, with no network isolation",
      cgroupns_host: "Sees the host's cgroups",
      selinux_off: "No SELinux label: can read other apps' volumes",
      devices: "Accesses host devices", capabilities: "Extra kernel capabilities" },
    alerts: "Alerts", alertsDesc: "Tells an ntfy topic when something fails. Off by default; the same alert is not repeated within the interval.",
    alertsOn: "Turn alerts on", alertServer: "ntfy server (e.g. https://ntfy.example.org)", alertTopic: "Topic", alertToken: "Token (optional)",
    alertTokenSet: "already set; leave blank to keep it", alertCooldown: "Do not repeat within (hours)", alertDisk: "Disk above (%)",
    alertKinds: { failed: "Unit failed", unhealthy: "Container unhealthy", restart_loop: "Restart loop", backup: "Backup failed",
                  update: "New upstream release", disk: "Disk almost full" },
    alertSave: "Save alerts", alertTest: "Send a test", alertSaved: "Alerts saved.", alertTested: "Test sent.",
    optionsTitle: "Install options", optionLocked: "chosen at the install; changing it moves the data (remove the app with its data and install again)",
    newInstance: "New instance", instanceName: "Instance name (lowercase letters, digits and -)", instanceCreate: "Create instance",
    instanceOf: (b) => `instance of ${b}`,
    readyToInstall: (n) => `Ready to install ${n}. It takes about a minute.`,
    planTitle: "What will happen",
    dockerImage: "Docker image", dockerTag: "Tag", containerName: "Container name", noLimit: "no limit", latestPinned: "the latest version",
    emptyRows: "Click “+” to add one.", hHost: "Host", hContainer: "Container", hProto: "Protocol", hIp: "IP (optional)", hKey: "Key", hValue: "Value", hLabel: "Label",
    qlPlaceholder: "Search apps… (Enter opens, Esc closes)", qlOpen: "Open", qlStore: "See in the store", qlManage: "Manage", qlWeb: (q) => `Search the web for “${q}”`, qlNone: "No app by that name.",
    appearance: "Appearance", apTheme: "Theme", apThemes: { system: "Like the system", light: "Light", dark: "Dark" }, apAccent: "Accent colour",
    apAccents: { orange: "Orange", blue: "Blue", green: "Green", teal: "Teal", purple: "Purple", pink: "Pink", red: "Red", slate: "Slate" },
    apCard: "Cards", apCards: { shadow: "With a shadow", hairline: "With a thin border" }, apDensity: "Density", apDensities: { comfortable: "Comfortable", compact: "Compact" },
    apBg: "Background image", apBgPick: "Choose an image…", apBgRemove: "Remove the background", apBgBlur: "Blur", apBgDim: "Veil over the image",
    apBgHint: "PNG, JPEG or WebP, up to 8 MB. Kept on the server, for every browser.", apSaved: "Appearance saved.",
    monDown: "not answering", monStatus: (c) => `answers with error ${c}`, monMs: (ms) => `answers in ${ms} ms`,
    svcField: { photos: "photos", videos: "videos", storage: "storage", queries: "queries", blocked: "blocked", blocked_pct: "blocked",
      latency: "latency", documents: "documents", inbox: "in the inbox", up: "up", down: "down", wanted: "wanted", queued: "queued",
      series: "series", movies: "movies", streams: "playing now", songs: "songs" },
    svcNames: { immich: "Immich", adguard: "AdGuard Home", paperless: "Paperless-ngx", "uptime-kuma": "Uptime Kuma", sonarr: "Sonarr", radarr: "Radarr", jellyfin: "Jellyfin" },
    svcTitle: "The app's numbers", svcSetup: "Set up the widget", svcConnect: "Connect it to see the app's numbers here.", svcSave: "Save", svcForget: "Forget",
    svcKey: "API key", svcUser: "User", svcPassword: "Password", svcSlug: "Status page slug", svcUrl: "Address (optional)",
    svcKeyKept: "already set; leave blank to keep it", svcNoUrl: "No address: the app has no published page.",
    svcHelp: { immich: "In Immich: Account → API keys, with the server.statistics permission.", adguard: "The user and password you sign in to AdGuard Home with.",
      paperless: "In Paperless: My profile → API token.", "uptime-kuma": "Create a status page in Uptime Kuma and use the slug of its address.",
      sonarr: "In Sonarr: Settings → General → API Key.", radarr: "In Radarr: Settings → General → API Key.", jellyfin: "In Jellyfin: Dashboard → API keys." },
    svcSecure: "The key stays on the server; the browser only gets the numbers.",
    netTitle: "Network (tailnet)", netModes: { local: "Local only", tailscale: "Tailscale", headscale: "Headscale" },
    netDesc: { local: "No tailnet: apps open on the LAN port and tsdproxy is off. The simplest way.",
      tailscale: "The host joins a Tailscale tailnet and tsdproxy gives each app an HTTPS name (a name per app).",
      headscale: "A network of your own, no account at a third party: the project runs the Headscale server, the host and tsdproxy join it. Apps are served over HTTP on the tailnet (Headscale issues no HTTPS certificate)." },
    netState: "Where it stands", netTs: "Tailscale on the host", netHs: "Headscale server", netTsd: "tsdproxy",
    netNotInstalled: "not installed", netNotRunning: "stopped", netRunning: "running", netInstalledOnly: "installed, stopped", netNoKey: "no authkey yet",
    netTailnet: "Network name", netTailnetHint: "the apps get names in it", netServer: "Headscale server address", netServerHint: "an address your devices can reach (the LAN does at home)",
    netApply: "Apply", netNeed: "What the host still needs (once, with sudo):", netNowTs: "Tailscale will sign in: if a link shows up below, open it.", netDone: "Network applied.",
    netHttps: "Apps that insist on HTTPS do not work with Headscale:",
    pageApps: "My apps", hello2: ["Good morning", "Good afternoon", "Good evening"], helloLine: (n, u) => `${n} apps${u ? `, ${u} with an update` : ""}. Right-click an app to see its state.`,
    recent: "Used recently", allApps: "All apps", navCollapse: "Collapse the sidebar", navExpand: "Expand the sidebar",
    hStat: { cpu: "Processor", mem: "Memory", disk: "Disk", net: "Network" }, ctxStart: "Start", ctxResume: "Resume", ctxPause: "Pause",
    apIconSize: "Icon size", apIconSizes: { small: "Small", medium: "Medium", large: "Large" }, apDepth: "Background", apDepths: { flat: "Flat", soft: "With depth and colour" },
    remove: "Remove", 
    linkName: "Name", linkUrl: "https://…", linkBad: "Use an http:// or https:// address",
    updateAvailable: "Update available",
    getApp: "Install", factCategory: "Category", factAuthor: "Developer", factSize: "Download", factArch: "Architecture", factVersion: "Version", installing: (n) => `Installing ${n}`, inBackground: "Continue in the background", installNow: "Install now", advanced: "Advanced", rolledBack: "rolled back to the previous version", techDetails: "Technical details", logTitle: "What was done", closeLabel: "Close",
    httpsNeeded: "needs HTTPS",
    httpsWarn: "This app needs HTTPS: over the local network (HTTP) the vault and the service worker fail without saying why. Use tailnet access.",
    podmanOld: (need, host) => `This app needs Podman ${need}+; the host has ${host}. Update Podman before installing.`,
    hostCpu: "load", hostMem: "RAM", hostUp: "up",
    trialLabel: "Try it", trialKeep: "Keep", trialBadge: "trial",
    trialNone: "install for good", trialReboot: "until the server reboots",
    trialPurge: "also delete the data at the end",
    trialHint: "Removes itself at the end, by a systemd timer. Only the service asked for, not what it pulled in.",
    trialEnds: (q, purge) => `Trial: ${q}. The data ${purge ? "will be deleted" : "stays"} at the end.`,
    trialIn: (s) => `ends in ${s}`, trialAtReboot: "ends at the next reboot",
    trialUnits: { h: "h", d: "days" },
    tabSummary: "Summary", tabConfig: "Configure", removeHint: "Remove the app and, if you want, its data",
    cfgEnvHint: "The app's variables and options", cfgLoginHint: "Username and password to sign in", cfgCustomHint: "Ports, volumes and the .container", cfgInstanceHint: "Another copy of the app, with its own data",
    customize: "Customize", customizedBadge: "customized", cPorts: "Ports", cVolumes: "Volumes",
    cEnv: "Environment variables", cDevices: "Devices", cCaps: "Extra container permissions",
    cRestart: "Restart policy", add: "Add", fromUnit: "(from the unit)", removeRow: "Remove",
    ipOpt: "IP (optional)", hostPort: "Host port", contPort: "Container port",
    hostPath: "Host folder", contPath: "Path in the container", labelZ: "private label (Z)",
    labelz: "shared (z)", labelNone: "no label", readOnly: "read-only", envKey: "NAME",
    envValue: "value", devPath: "/dev/…", previewBtn: "Preview", saveApply: "Save and apply",
    revertBtn: "Revert to default", fileToWrite: "File that will be written", generated: "Command Quadlet generates",
    nothingChanged: "Nothing different from the repository's unit.", filePath: "File",
    custIntro: "Changes this installation without touching the repository's unit: the change lives in a file " +
      "beside it, survives Update and goes away on Revert. The image and version belong to the repository, and " +
      "there is no privilege switch (for that, edit the unit by hand).",
    portsHint: "Publishing a port opens the app on the local network, whatever the access rule says.",
    volumesHint: (r) => `Folders allowed for new volumes: ${r.join(", ")}. To allow another, write its path ` +
      "in ~/.config/quadlet-homelab/store-roots.",
    custEnvHint: "Variables of the .env file are under Configure; extras go here.",
    capsHint: "By default the container starts with no special system permission. Each box gives one back, for this app only. You rarely need to touch it: tick one only if the app's log complains about a denied operation. For one that is not on the list, edit the unit by hand.",
    capInfo: { CHOWN: "change file owners", DAC_OVERRIDE: "ignore file permissions", FOWNER: "act as the files' owner", FSETID: "keep setuid/setgid bits",
      KILL: "send signals to another user's processes", NET_BIND_SERVICE: "listen on ports below 1024", NET_RAW: "raw sockets (ping and network tools)",
      SETFCAP: "set permissions on files", SETGID: "change the process's group", SETPCAP: "change process permissions", SETUID: "change the process's user",
      SYS_CHROOT: "use chroot", SYS_NICE: "change process priority", MKNOD: "create device files", AUDIT_WRITE: "write to the audit log" },
    limitsOff: "Your user's systemd does not delegate the memory and cpu controllers, and with a limit the container " +
      "does not start. Turning that on is a root change (Delegate= in user@.service): see docs/tools.md.",
    cLimits: "Limits", limMemory: "Memory limit", limCpus: "CPUs", limMemoryHint: "e.g. 512m, 2g",
    limCpusHint: "e.g. 1.5 (a core and a half)", limitsHint: "Takes effect the next time the container starts. Empty means no limit.",
    baseChanged: "The repository's unit changed since you customized it. The customization resets lists and may " +
      "hide what is new: review it and save again.",
    none: "No app found.", installed: "installed", running: "running",
    attention: "attention", changed: "repo changed", install: "Install", update: "Update",
    remove: "Remove", logs: "Logs", open: "Open", confirm: "Confirm", cancel: "Cancel",
    plan: "Plan (nothing done yet)", working: "Running…", done: "Done.",
    failed: "Finished with an error", unit: "Unit", service: "systemd", container: "Container",
    repo: "Repo", start: "Start", stop: "Stop", restart: "Restart",
    secretHint: "Empty = skip and create it by hand later (see the README).",
    exists: "already exists — empty keeps it",
    removeNote: "Removes the units and stops the service. Volumes, secrets and .env stay. The tailnet node is not deregistered: do that in the Tailscale admin.",
    busy: "Another job is running. Wait for it to finish.",
    synced: "in sync", duplicated: "duplicated",
    installedTag: "Installed", upstream: "Upstream", newVersion: "new version",
    gone: "image gone", checking: "checking upstream…", checked: "upstream checked",
    recheck: "Check now", upToDate: "up to date", pending: "released, image not out yet",
    login: "Login", user: "User", password: "Password", show: "Show", hide: "Hide",
    copy: "Copy", copied: "Copied", noLogin: "No credential to show (the secret does not exist yet).",
    backups: "Backups", backupNow: "Back up now", download: "Download", restoreAction: "Restore",
    upload: "Upload backup", noBackups: "No backups yet.", backupDir: "Folder",
    backupNote: "The backup stops the service, packs the data and starts it again.",
    restoreNote: "Restoring OVERWRITES the current data with the archive's, with no way back.",
    typeToConfirm: "Type the service name to confirm:",
    notesFrom: "Releases since the installed one", noNotes: "No new release to read.",
    onGithub: "see on GitHub",
    upgradeTo: (v) => `Update to ${v}`,
    nothingToDo: "Nothing to do: what is installed already matches what the repository pins.",
    installWith: (deps) => `Install (with ${deps})`,
    requiresNote: (deps) => `This app needs ${deps}, which is not installed yet. ` +
      `The install puts it in first, in the right order.`,
    access: "Access", followRule: (m) => `Follow the rule (${m})`,
    modes: { local: "Local network", tailnet: "Tailnet", both: "Local network and tailnet" },
    configure: "Configure", envSave: "Save and restart", envHint: "Tick to turn an option on; unticking comments it out.",
    envNote: "Saving restarts the service (if it is running). The previous file stays as .bak.",
    noEnv: "This service has no settings file to edit.", active: "on",
    disk: "Disk", cpu: "CPU", mem: "Memory", runsOn: "Runs on", counting: "counting…",
    noArm: (host, units) => `No image for ${host}: ${units}. It will not run on this server.`,
    history: "History", noHistory: "No action recorded yet.", when: "When", what: "Action", result: "Result",
    took: "Took", from: "from", output: "Output",
    act: { pause: "Pause", resume: "Resume", install: "Install", update: "Update", upgrade: "Update version", remove: "Remove", backup: "Backup",
           restore: "Restore", access: "Access", env: "Settings", start: "Start", stop: "Stop", restart: "Restart",
           customize: "Customize", revert: "Revert", prune: "Clean up", "custom-unit": "own .container", migrate: "Migration", "force-stop": "Force stop", "force-restart": "Force restart", "image-rm": "Image deleted" },
    link: { repo: "Project", docs: "Documentation", issues: "Issues", releases: "Releases", image: "Image", recipe: "Recipe in this repository" },
    shots: "Screenshots",
    lang: "Português",
  },
};

const S = {
  lang: localStorage.getItem("qh-lang") || (navigator.language.startsWith("pt") ? "pt" : "en"),
  backupFirst: localStorage.getItem("qh-backup-first") === "1",   // the box next to Update, remembered
  rule: "tailnet",          // the host's access rule (qh --set-access)
  apps: [], group: null, filter: null, search: "", current: null, rhist: {}, preCustom: {}, preUnit: {}, preUnitAck: {},
  view: null,               // "apps" (what is installed) or "store" (the catalog); kept in the URL hash
  stats: {},                // unit -> {cpu, mem}, from /api/stats
  upd: {}, checked: null,   // unit -> qh-updates --host row; when it was asked
};
const t = (k) => T[S.lang][k];
const $ = (id) => document.getElementById(id);

// h("div", {class: "x"}, "text", child) — strings become text nodes, never HTML.
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

// -- Markdown, for release notes ---------------------------------------------
// Headings, lists, quotes, code and links, built as DOM nodes — never as HTML:
// the notes are someone else's text. Raw HTML in them (badges, store buttons)
// is stripped to its text, and images are dropped.

function mdInline(text) {
  const out = [];
  const re = /(`[^`]+`)|\[((?:[^\[\]]|\[[^\]]*\])+)\]\((https?:\/\/[^)\s]+)[^)]*\)|\*\*([^*]+)\*\*|__([^_]+)__|(https?:\/\/[^\s<>)\]]+)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const link = (href, label) => h("a", { href, target: "_blank", rel: "noopener noreferrer" }, label);
    if (m[1]) out.push(h("code", {}, m[1].slice(1, -1)));
    else if (m[2]) out.push(link(m[3], m[2]));
    else if (m[4] || m[5]) out.push(h("strong", {}, m[4] || m[5]));
    else if (m[6]) out.push(link(m[6], m[6]));
    last = re.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

function md(src) {
  const text = (src || "").replace(/\r/g, "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/?(p|div|h[1-6]|ul|ol|li|details|summary|table|tr|td|th|picture)\b[^>]*>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\[\s*\]\([^)]*\)/g, "")
    .replace(/&nbsp;/g, " ").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, "&");
  const nodes = [];
  let para = [], list = null, code = null;
  const flushPara = () => { if (para.length) nodes.push(h("p", {}, mdInline(para.join(" ")))); para = []; };
  const flushList = () => { if (list) nodes.push(list); list = null; };
  const flush = () => { flushPara(); flushList(); };
  for (const line of text.split("\n")) {
    if (code) {
      if (/^\s*```/.test(line)) { nodes.push(h("pre", { class: "code" }, code.join("\n"))); code = null; }
      else code.push(line);
      continue;
    }
    let m;
    if (/^\s*```/.test(line)) { flush(); code = []; }
    else if (!line.trim()) flush();
    else if ((m = line.match(/^\s{0,3}(#{1,6})\s+(.*?)[\s#]*$/))) {
      flush();
      nodes.push(h("p", { class: `md-h md-h${m[1].length}` }, mdInline(m[2])));
    } else if (/^\s{0,3}([-*_])(\s*\1){2,}\s*$/.test(line)) { flush(); nodes.push(h("hr")); }
    else if ((m = line.match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/))) {
      flushPara();
      if (!list) list = h("ul", {});
      const nivel = Math.min(3, Math.floor(m[1].replace(/\t/g, "  ").length / 2));
      list.append(h("li", { class: `md-l${nivel}` }, mdInline(m[3])));
    } else if ((m = line.match(/^\s*>\s?(.*)$/))) { flush(); nodes.push(h("blockquote", {}, mdInline(m[1]))); }
    else if (list && /^\s+\S/.test(line)) list.lastChild.append(" ", ...mdInline(line.trim()));
    else { flushList(); para.push(line.trim()); }
  }
  if (code) nodes.push(h("pre", { class: "code" }, code.join("\n")));
  flush();
  return nodes;
}

// The README descriptions carry markdown links; the text is what reads well here.
const plain = (s) => (s || "").replace(/\[([^\]]+)\]\([^)]*\)/g, "$1").replace(/`/g, "");

// replaceChildren turns a null or false argument into the words "null" and "false"
// (h() skips them): every fill of a container goes through here.
const fill = (el, ...kids) => el.replaceChildren(...kids.filter((k) => k !== null && k !== undefined && k !== false));

async function api(path, body) {
  const opts = body === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-QH-Store": "1" },
    body: JSON.stringify({ ...body, lang: S.lang }),
  };
  const r = await fetch(path, opts);
  if (r.status === 401) { location.href = "/login"; throw new Error("login"); }
  const data = await r.json();
  if (!r.ok) throw Object.assign(new Error(data.error || r.status), { status: r.status });
  return data;
}

// -- state of an app --------------------------------------------------------

// The tag of an image reference; a digest-only reference has none to show.
function tagOf(image) {
  if (!image) return "";
  const s = image.split("@")[0];
  const i = s.lastIndexOf(":");
  if (i > s.lastIndexOf("/")) return s.slice(i + 1);
  return image.includes("@") ? "digest" : "latest";
}

function mainUnit(app) {
  const inst = app.units.filter((u) => u.installed);
  return inst.find((u) => u.unit === app.main_unit) || inst[0];
}

// Order is priority: a broken service matters more than a new release.
// What systemd knows about a unit that is not simply running: restarts, exit code, last failure.
function failText(u) {
  const f = u.failure;
  const quando = f.last ? new Date(f.last * 1000).toLocaleString(S.lang === "pt" ? "pt-BR" : "en") : null;
  return [`${u.unit}:`, f.state === "failed" ? t("failFailed") : f.sub === "auto-restart" ? t("failLoop") : t("failRestarted"),
    f.restarts ? `${f.restarts}×` : null, `${t("failExit")} ${f.exit}`, f.result !== "success" ? `(${f.result})` : null,
    quando ? `· ${t("failLast")} ${quando}` : null].filter(Boolean).join(" ");
}

function failBadge(inst) {
  const com = inst.filter((u) => u.failure && !u.stopped);
  if (!com.length) return null;
  const laco = com.find((u) => u.failure.sub === "auto-restart");
  const caiu = com.find((u) => u.failure.state === "failed");
  const mais = Math.max(...com.map((u) => u.failure.restarts));
  const titulo = com.map(failText).join("\n");
  if (laco) return ["bad", t("loopBadge")(laco.failure.restarts), titulo];
  if (caiu) return ["bad", t("failedBadge")(caiu.failure.exit), titulo];
  return mais ? ["warn", t("restartedBadge")(mais), titulo] : null;
}

function health(app) {
  const inst = app.units.filter((u) => u.installed);
  if (!inst.length) return null;
  // Stopped on purpose (masked): not an alarm, and it will stay so after a reboot.
  if (inst.every((u) => u.stopped)) return ["plain", t("stoppedBadge")];
  const falha = failBadge(inst);
  if (falha && falha[0] === "bad") return falha;
  if (inst.some((u) => u.service !== "active" || ["unhealthy", "down"].includes(u.container)))
    return ["bad", t("attention")];
  const rows = inst.map((u) => S.upd[u.unit]).filter(Boolean);
  if (rows.some((r) => r.bucket === "GONE")) return ["bad", t("gone")];
  if (inst.some((u) => u.container === "paused")) return ["warn", t("pausedBadge")];
  if (app.deprecated) return ["warn", t("deprecatedBadge")];
  if (app.trial) return ["warn", t("trialBadge")];
  if (falha) return falha;
  const atras = rows.find((r) => r.bucket === "BEHIND");
  if (atras) return ["warn", `${t("newVersion")} ${atras.there}`];
  if (inst.some((u) => u.drift)) return ["warn", t("changed")];
  return ["ok", t("running")];
}

// The upstream cell: what upstream released, coloured by whether it asks anything.
function upstreamCell(u) {
  const r = S.upd[u.unit];
  if (!r) return ["", S.checked ? "—" : "…"];
  if (r.bucket === "BEHIND") return ["warn", r.there];
  if (r.bucket === "GONE") return ["bad", t("gone")];
  if (r.bucket === "up to date") return ["ok", t("upToDate")];
  if (r.bucket === "PENDING") return ["warn", `${r.there} (${t("pending")})`];
  return ["", r.status];
}

// Marked in app.json (deprecated): why a service is discontinued, in the page's language.
// "ends in 5 h 20 min" / "ends at the next reboot", from the record the catalog carries.
function trialWhen(tr) {
  if (tr.expires === null || tr.expires === undefined) return t("trialAtReboot");
  const min = Math.max(1, Math.round((tr.expires - Date.now() / 1000) / 60));
  const q = min < 60 ? `${min} min` : min < 2880 ? `${Math.floor(min / 60)} h ${String(min % 60).padStart(2, "0")} min`
    : `${Math.round(min / 1440)} ${t("trialUnits").d}`;
  return t("trialIn")(q);
}
const depReason = (a) => (a.deprecated ? a.deprecated[S.lang] || a.deprecated.en : null);

const groupOf = (app) => (app.group ? app.group[S.lang] : t("other"));

// -- grid -------------------------------------------------------------------

function renderChrome() {
  document.documentElement.lang = S.lang === "pt" ? "pt-BR" : "en";
  $("search").placeholder = t("search");
  // Icon buttons: the glyph is drawn in CSS; the words are the accessible name and the tooltip.
  $("lang").textContent = t("lang");
  for (const [id, key] of [["recheck", "recheck"]]) {
    $(id).textContent = "";
    $(id).title = t(key);
    $(id).setAttribute("aria-label", t(key));
  }
  for (const [id, key] of [["history-btn", "history"], ["files-btn", "files"], ["resources-btn", "resources"], ["settings-btn", "settings"]]) {
    fill($(id), h("span", { class: "nl" }, t(key)));
    $(id).title = t(key);
  }
  renderHead();
  const fechada = document.body.dataset.nav === "collapsed";
  $("nav-toggle").textContent = fechada ? "⇥" : "⇤";
  $("nav-toggle").title = $("nav-toggle").getAttribute && fechada ? t("navExpand") : t("navCollapse");
  $("nav-toggle").setAttribute("aria-label", fechada ? t("navExpand") : t("navCollapse"));
  $("p-close").setAttribute("aria-label", t("closeLabel"));
  $("p-tech-title").textContent = t("techDetails");
  $("p-log-title").textContent = t("logTitle");
  renderTabs();
}

// The page title and the tabs: cheap, so the grid may call it at every refresh.
function renderHead() {
  $("page-title").textContent = S.view === "store" ? t("tabStore") : t("pageApps");
  renderTabs();
}

const installed = () => S.apps.filter((a) => a.installed);

// Two screens, as CasaOS has them: what is installed (a launcher) and the catalog
// (somewhere to find and install). The choice lives in the URL hash, so a reload
// or a bookmark lands on the same one.
function renderTabs() {
  const aba = (id, key, view, n) => {
    fill($(id), h("span", { class: "nl" }, t(key)), h("span", { class: "count" }, String(n)));
    $(id).title = t(key);
    $(id).setAttribute("aria-selected", String(S.view === view));
  };
  aba("tab-apps", "tabApps", "apps", installed().length);
  aba("tab-store", "tabStore", "store", S.apps.length);
}

function setView(view) {
  S.view = view;
  S.group = null;
  S.filter = null;
  if (typeof history !== "undefined" && history.replaceState) history.replaceState(null, "", `#${view}`);
  renderTabs();
  renderGroups();
  renderGrid();
}

// What needs a look among the installed: something newer to take (a release upstream, or the
// repository changed since the install), and anything the badge calls a problem.
const hasUpdate = (a) => behind(a).length > 0 || a.units.some((u) => u.installed && u.drift);
const hasProblem = (a) => { const st = health(a); return !!st && st[0] === "bad"; };
const FILTERS = { updates: hasUpdate, problems: hasProblem };

// Meus apps: counters as filters, and one line of what is running. Categories are for the catalog.
function renderFilters() {
  const mine = installed();
  const contar = (f) => mine.filter(f).length;
  const chip = (key, label, n) => h("button", {
    type: "button", "aria-pressed": String(S.filter === key),
    onclick: () => { S.filter = S.filter === key ? null : key; renderGroups(); renderGrid(); },
  }, `${label} `, h("span", { class: "count" }, String(n)));
  const rodando = mine.filter((a) => runState(a) === "running").length;
  const pausados = mine.filter((a) => runState(a) === "paused").length;
  const parados = mine.length - rodando - pausados;
  $("groups").hidden = !mine.length;
  fill($("groups"), chip(null, t("all"), mine.length),
    chip("updates", t("filterUpdates"), contar(hasUpdate)), chip("problems", t("filterProblems"), contar(hasProblem)));
  $("summary").hidden = !mine.length;
  const comAtualizacao = contar(hasUpdate);
  fill($("summary"), t("summaryLine")(rodando, parados, pausados),
    comAtualizacao ? " " : null,
    comAtualizacao ? h("button", { type: "button", id: "update-all", class: "ghost",
      onclick: (ev) => {
        const b = ev.target;
        if (!b.dataset.sure) { b.dataset.sure = "1"; b.textContent = t("updateAllSure"); return; }
        jobWindow(t("updatingAll"), () => api("/api/update-all", {}));
      } }, t("updateAll")(comAtualizacao)) : null);
}

function renderGroups() {
  if (S.view === "apps") return renderFilters();
  $("summary").hidden = true;
  $("groups").hidden = S.view !== "store";
  const groups = [...new Set(S.apps.map(groupOf))].sort((a, b) => a.localeCompare(b, S.lang));
  const chip = (g, label) => h("button", {
    type: "button", "aria-pressed": String(S.group === g),
    onclick: () => { S.group = g; renderGroups(); renderGrid(); },
  }, label);
  fill($("groups"), chip(null, t("all")), ...groups.map((g) => chip(g, g)));
}

const matches = (a, q) =>
  !q || `${a.name} ${a.id} ${a.description.en} ${a.description.pt}`.toLowerCase().includes(q);

// The page of an installed app, when there is exactly one to open: the tile goes
// straight to it. A stack with a dozen web UIs has no single answer, and the tile
// opens its panel instead.
function openUrl(a) {
  const instaladas = new Set(a.units.filter((u) => u.installed).map((u) => u.unit));
  const urls = a.web.filter((w) => instaladas.has(w.unit)).map((w) => w.tailnet || w.local).filter(Boolean);
  return urls.length === 1 ? urls[0] : null;
}

// Where an installed app is: running, paused (frozen, still "active" to systemd), or stopped.
function runState(a) {
  const inst = a.units.filter((u) => u.installed);
  if (inst.some((u) => u.container === "paused")) return "paused";
  return inst.some((u) => u.service === "active") ? "running" : "stopped";
}

// ▶ ⏸ ■ for a whole app. Each is enabled only where it does something.
function controls(a) {
  const st = runState(a);
  const botao = (verb, glyph, titulo, ligado) => h("button", {
    type: "button", class: "ctl", title: titulo, "aria-label": `${titulo} ${a.name}`, disabled: !ligado,
    onclick: () => control(a, verb) }, glyph);
  return h("div", { class: "controls" },
    botao("play", "▶", t("play"), st !== "running"),
    botao("pause", "⏸", t("pause"), st === "running"),
    botao("stop", "■", t("stopApp"), st !== "stopped"));
}

// Restart the app's main unit in the background, like control(): only a failure is worth a word.
async function restartApp(a) {
  const u = mainUnit(a);
  if (!u) return;
  try {
    const { job } = await api("/api/unit", { unit: u.unit, verb: "restart" });
    let st;
    do {
      await new Promise((r2) => setTimeout(r2, 600));
      st = await api(`/api/job/${job}?from=0`);
    } while (st.rc === null);
    if (st.rc !== 0) toast(`${t("ctlFailed")} ${a.name} — ${(st.output || "").trim().split("\n").pop()}`);
  } catch (e) { toast(e.status === 409 ? t("busy") : `${t("ctlFailed")} ${e.message}`); }
  await load();
}

function toast(texto) {
  const el = $("toast");
  el.textContent = texto;
  el.hidden = false;
  clearTimeout(toast.fim);
  toast.fim = setTimeout(() => { el.hidden = true; }, 6000);
}

// Runs in the background and refreshes the grid; only a failure is worth a word.
async function control(a, verb) {
  try {
    const { job } = await api("/api/control", { app: a.id, verb });
    let st;
    do {
      await new Promise((r) => setTimeout(r, 600));
      st = await api(`/api/job/${job}?from=0`);
    } while (st.rc === null);
    if (st.rc !== 0) toast(`${t("ctlFailed")} ${a.name} — ${(st.output || "").trim().split("\n").pop()}`);
  } catch (e) { toast(e.status === 409 ? t("busy") : `${t("ctlFailed")} ${e.message}`); }
  await load();
}

// Running, paused and stopped are told by one coloured dot, nothing written; a newer version by a small
// arrow on the icon. Only what needs a decision (a failure, discontinued, a trial) keeps its words.
function runDot(a) {
  const st = health(a);
  if (st && st[0] === "bad") return ["bad", st[1]];
  const r = runState(a);
  // The site monitor: a running container whose app does not answer is a red dot, not a green one.
  const m = (S.mon || {})[a.id];
  if (r === "running" && m && !m.ok) return ["bad", m.status ? t("monStatus")(m.status) : t("monDown")];
  if (r === "running") return ["ok", m && m.ok ? `${t("running")} · ${t("monMs")(m.ms)}` : t("running")];
  return r === "paused" ? ["warn", t("pausedBadge")] : ["off", t("stoppedBadge")];
}

async function pollMonitor() {
  if (document.hidden || !S.apps.some((a) => a.installed)) return;
  try {
    S.mon = (await api("/api/monitor")).apps;
    if (S.view === "apps") renderGrid();
  } catch (e) { /* next turn */ }
}


// -- icon plates ----------------------------------------------------------------------------
// The logo sits on a squircle plate whose tone comes from the logo itself: read once from the image the server
// already serves (same origin, so the canvas may read it) — its hue, whether it is a full square, mostly white,
// vivid or grey, and how much room it takes, so every logo weighs the same. app.json `icon` overrides any of it.
let ICON_INFO = {};
try { ICON_INFO = JSON.parse(localStorage.getItem("qh-icons2")) || {}; } catch (e) { ICON_INFO = {}; }
const hueDe = (txt) => { let n = 0; for (const c of String(txt)) n = (n * 31 + c.charCodeAt(0)) % 360; return n; };
const preso = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

function analyseImage(img) {
  const N = 96, cv = document.createElement("canvas");
  cv.width = cv.height = N;
  const cx = cv.getContext("2d", { willReadFrequently: true });
  const ar = img.naturalWidth / img.naturalHeight || 1;
  let W = N, H = N;
  if (ar > 1) H = N / ar; else W = N * ar;
  cx.drawImage(img, (N - W) / 2, (N - H) / 2, W, H);
  let d;
  try { d = cx.getImageData(0, 0, N, N).data; } catch (e) { return null; }
  let x0 = N, y0 = N, x1 = -1, y1 = -1, n = 0, lum = 0, sat = 0, branco = 0, hx = 0, hy = 0;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const i = (y * N + x) * 4, a = d[i + 3];
    if (a <= 24) continue;
    n++; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    const r = d[i] / 255, g = d[i + 1] / 255, b = d[i + 2] / 255, mx = Math.max(r, g, b), mn = Math.min(r, g, b), s = mx ? (mx - mn) / mx : 0;
    const l = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    lum += l; sat += s;
    if (l > 0.9 && s < 0.12) branco++;
    if (s > 0.25 && a > 128) {
      const h = Math.atan2(Math.sqrt(3) * (g - b), 2 * r - g - b);
      hx += Math.cos(h) * s; hy += Math.sin(h) * s;
    }
  }
  if (!n) return null;
  const area = n / (N * N), caixa = Math.max(x1 - x0 + 1, y1 - y0 + 1) / N;
  const cantos = [[0, 0], [N - 1, 0], [0, N - 1], [N - 1, N - 1]].filter(([x, y]) => d[(y * N + x) * 4 + 3] > 200).length;
  const mLum = lum / n, mSat = sat / n, mBranco = branco / n;
  const matiz = hx || hy ? Math.round(((Math.atan2(hy, hx) * 180) / Math.PI + 360) % 360) : 220;
  let tone = "light";
  if (area > 0.9 || cantos >= 3) tone = "full";
  else if (mBranco > 0.2 || mLum > 0.82 || (mSat < 0.15 && mLum > 0.3 && mLum < 0.75)) tone = "dark";
  else if (mSat > 0.5) tone = "color";
  const reforco = preso(Math.pow(0.6 / area, 0.18), 0.95, 1.18);
  return { tone, h: matiz, fit: tone === "full" ? 1 : +preso(reforco / caixa, 0.9, 1.35).toFixed(2) };
}

function decoratePlate(p, a, img) {
  const cfg = a.icon_cfg || {};
  const aplica = (info) => {
    p.style.setProperty("--h", String(info.h));
    p.style.setProperty("--fit", String(cfg.fit || info.fit));
    const tone = cfg.tone || info.tone;
    if (tone && tone !== "light") p.setAttribute("data-tone", tone); else p.removeAttribute("data-tone");
    if (cfg.bg && tone !== "full") { p.setAttribute("data-custom", "1"); p.style.setProperty("--bgc", cfg.bg); } else p.removeAttribute("data-custom");
  };
  p.style.setProperty("--h", String(hueDe(a.id)));
  const conhecida = ICON_INFO[a.icon];
  if (conhecida) return aplica(conhecida);
  aplica({ h: hueDe(a.id), fit: 1, tone: "light" });
  const ler = () => {
    const info = analyseImage(img);
    if (!info) return;
    ICON_INFO[a.icon] = info;
    try { localStorage.setItem("qh-icons2", JSON.stringify(ICON_INFO)); } catch (e) { /* the cache is a courtesy */ }
    aplica(info);
  };
  if (img.complete && img.naturalWidth) ler(); else img.addEventListener("load", ler, { once: true });
}

function iconPlate(a, tam = "") {
  const img = h("img", { src: a.icon, alt: "", loading: "lazy", referrerpolicy: "no-referrer" });
  const p = h("span", { class: `plate ${tam}`.trim() }, img);
  decoratePlate(p, a, img);
  return p;
}

// -- recently used ----------------------------------------------------------------------------
function touchRecent(id) {
  S.recent = [id, ...(S.recent || []).filter((x) => x !== id)].slice(0, 8);
  try { localStorage.setItem("qh-recent", JSON.stringify(S.recent)); } catch (e) { /* kept for this session */ }
}

// -- the right-click menu of an app ----------------------------------------------------------
const hideCtx = () => $("ctx").classList.remove("open");
function ctxMenu(x, y, a) {
  const m = $("ctx"), [cls, estado] = runDot(a), rodando = runState(a) !== "stopped", pausado = runState(a) === "paused";
  const novo = behind(a)[0], mudou = a.units.find((u) => u.installed && u.drift), url = openUrl(a), principal = mainUnit(a);
  const item = (rotulo, acao, extra = "") => h("button", { type: "button", role: "menuitem", class: `it ${extra}`.trim(), onclick: () => { hideCtx(); acao(); } }, rotulo);
  const gerir = (f) => () => { openPanel(a.id); f(); };
  fill(m,
    h("div", { class: "hd" }, iconPlate(a, "xs"), h("div", {}, h("b", {}, a.name),
      h("small", {}, h("i", { class: `dot ${cls}` }), `${estado}${principal ? ` · ${tagOf(principal.installed_image)}` : ""}`))),
    novo ? item(`↑ ${t("upgradeTo")(S.upd[novo.unit].there)}`, gerir(() => updateNow("upgrade")), "up")
      : mudou ? item(`↑ ${t("update")}`, gerir(() => updateNow("update")), "up") : null,
    url ? item(t("open"), () => { touchRecent(a.id); window.open(url, "_blank", "noopener"); }) : null,
    item(t("manage"), () => openPanel(a.id)),
    item(t("customize"), gerir(() => showCustom(current()))),
    h("div", { class: "sep" }),
    rodando ? item(t("restart"), () => restartApp(a)) : item(t("ctxStart"), () => control(a, "play")),
    rodando && !pausado ? item(t("ctxPause"), () => control(a, "pause")) : null,
    pausado ? item(t("ctxResume"), () => control(a, "play")) : null,
    rodando ? item(t("stopApp"), () => control(a, "stop")) : null,
    principal ? item(t("logs"), gerir(() => showLogs(principal.unit))) : null,
    h("div", { class: "sep" }),
    item(t("remove"), gerir(() => plan("remove")), "dn"));
  m.classList.add("open");
  const w = m.offsetWidth || 280, alt = m.offsetHeight || 360, vw = globalThis.innerWidth || 1200, vh = globalThis.innerHeight || 800;
  m.style.left = `${Math.max(8, Math.min(x, vw - w - 8))}px`;
  m.style.top = `${Math.max(8, Math.min(y, vh - alt - 8))}px`;
}
document.addEventListener("click", hideCtx);
document.addEventListener("scroll", hideCtx, true);
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") hideCtx(); });

function tile(a) {
  const st = health(a), url = openUrl(a);
  const silencioso = !st || [t("running"), t("pausedBadge"), t("stoppedBadge"), t("changed")].includes(st[1]) || st[1].startsWith(t("newVersion"));
  let tempo;
  const corpo = [
    iconPlate(a),
    h("h3", {}, a.name),
    !silencioso && h("span", { class: `badge ${st[0]}`, title: st[2] || null }, st[1]),
    svcLine(a),
  ];
  const abre = () => touchRecent(a.id);
  const carta = h("div", { class: "card tile", "data-run": runState(a),      // a stopped or paused app greys out (CSS)
    oncontextmenu: (ev) => { ev.preventDefault(); ev.stopPropagation(); ctxMenu(ev.clientX, ev.clientY, a); },
    ontouchstart: (ev) => { const p = ev.touches && ev.touches[0]; if (p) tempo = setTimeout(() => ctxMenu(p.clientX, p.clientY, a), 550); },
    ontouchend: () => clearTimeout(tempo), ontouchmove: () => clearTimeout(tempo) },
    url
      ? h("a", { class: "tile-open", href: url, target: "_blank", rel: "noopener noreferrer", "aria-label": `${t("open")} ${a.name}`, title: a.name, onclick: abre }, ...corpo)
      : h("button", { class: "tile-open", type: "button", title: a.name, onclick: () => { abre(); openPanel(a.id); } }, ...corpo));
  return carta;
}

function storeCard(a) {
  return h("button", { class: "card", type: "button", onclick: () => openPanel(a.id) },
    iconPlate(a, "sm"),
    h("div", { class: "tx" }, h("h3", {}, a.name, a.deprecated ? h("span", { class: "badge warn" }, a.installed ? `${t("deprecatedBadge")} · ${t("installedBadge")}` : t("deprecatedBadge")) : null),
      h("p", { class: "desc" }, plain(a.description[S.lang] || a.description.en))),
    a.deprecated ? null : h("span", { class: a.installed ? "get got" : "get", "aria-hidden": "true",
      onclick: a.installed ? null : (ev) => { ev.stopPropagation(); instalar(a.id); } }, a.installed ? `✓ ${t("installedBadge")}` : t("getApp")));
}

// -- home: greeting, the server at a glance, what you used last --------------------------------------
S.hist = { cpu: [], mem: [], disk: [], net: [] };
function pushHist(d) {
  const poe = (k, v) => { if (v === null || v === undefined || Number.isNaN(v)) return; S.hist[k].push(v); if (S.hist[k].length > 24) S.hist[k].shift(); };
  poe("cpu", d.cpu && d.cpu.pct !== null && d.cpu.pct !== undefined ? d.cpu.pct : (d.load !== null && d.cpus ? Math.min(100, (d.load / d.cpus) * 100) : null));
  poe("mem", d.mem ? (d.mem.used / d.mem.total) * 100 : null);
  poe("disk", d.disk ? (d.disk.used / d.disk.total) * 100 : null);
  poe("net", d.net && d.net.rx_rate !== null && d.net.rx_rate !== undefined ? d.net.rx_rate : null);
}

function renderHome() {
  const el = $("home");
  const filtrando = !!S.search.trim() || !!S.filter;
  if (S.view !== "apps" || !installed().length || filtrando) { fill(el); return; }
  const hr = new Date().getHours(), saud = t("hello2")[hr < 12 ? 0 : hr < 18 ? 1 : 2];
  const d = S.hostData || {}, H = S.hist;
  const pct = (v) => (v === undefined || v === null ? "—" : `${Math.round(v)}%`);
  // Heights go through the style object (CSSOM), which the CSP allows; a style attribute it does not.
  const barras = (arr, escala) => h("div", { class: "spark" }, ...arr.map((v) => {
    const b = h("i");
    b.style.height = `${Math.max(4, Math.min(100, escala ? (v / escala) * 100 : v))}%`;
    return b;
  }));
  const ultimo = (arr) => (arr.length ? arr[arr.length - 1] : undefined);
  const maxRede = Math.max(1, ...H.net);
  const cartao = (rot, valor, corpo) => h("div", { class: "stat", "data-stat": rot }, h("small", {}, t("hStat")[rot]), h("b", {}, valor), corpo);
  const mine = installed(), subiu = mine.filter(hasUpdate).length;
  const recentes = (S.recent || []).map((id) => mine.find((a) => a.id === id)).filter(Boolean).slice(0, 6);
  fill(el,
    h("div", { class: "hello" }, h("b", {}, saud), h("span", {}, t("helloLine")(mine.length, subiu))),
    h("div", { class: "stats" },
      cartao("cpu", pct(ultimo(H.cpu)), barras(H.cpu)), cartao("mem", pct(ultimo(H.mem)), barras(H.mem)), cartao("disk", pct(ultimo(H.disk)), barras(H.disk)),
      cartao("net", d.net && d.net.rx_rate !== null && d.net.rx_rate !== undefined ? `↓ ${bytes(d.net.rx_rate)}/s` : "—", barras(H.net, maxRede))),
    recentes.length ? h("div", {}, h("div", { class: "sect" }, t("recent")), h("div", { class: "grid" }, ...recentes.map(tile))) : null,
    h("div", { class: "sect" }, t("allApps")));
}

// An install made under an app the repository split (media-stack): said above everything, with the way to move it.
function renderLegacy() {
  const el = $("legacy"), achados = S.legacy || [];
  el.hidden = !achados.length;
  fill(el, ...achados.flatMap((x) => [
    h("b", {}, t("legacyTitle")(x.from, x.units.length)),
    h("p", { class: "muted" }, t("legacyBody")),
    h("button", { type: "button", onclick: () => jobWindow(t("legacyRunning"), () => api("/api/migrate", { from: x.from })) }, t("legacyButton"))]));
}

function renderGrid() {
  renderLegacy();
  const q = S.search.trim().toLowerCase();
  const meus = S.view === "apps";
  const pool = meus ? installed().filter(FILTERS[S.filter] || (() => true))
                    : S.apps.filter((a) => !S.group || groupOf(a) === S.group);
  const shown = pool.filter((a) => matches(a, q));
  $("grid").className = meus ? "apps" : "";
  fill($("grid"), ...shown.map(meus ? tile : storeCard));
  renderHome();
  renderHead();
  $("empty").hidden = shown.length > 0;
  if (!shown.length) {
    const semApps = meus && !installed().length && !q;
    fill($("empty"), semApps ? t("noneInstalled") : t("none"),
      semApps ? h("button", { type: "button", onclick: () => setView("store") }, t("goStore")) : null);
  }
}

async function load() {
  const cat = await api(`/api/catalog?lang=${S.lang}`);
  S.apps = cat.apps;
  S.rule = cat.access;
  S.podman = cat.podman;
  S.podmanRec = cat.podman_recommended;
  S.podmanOutdated = !!cat.podman_outdated;
  S.legacy = cat.legacy || [];
  if (!S.view) {
    const hash = (location.hash || "").slice(1);
    S.view = ["apps", "store"].includes(hash) ? hash : (installed().length ? "apps" : "store");
  }
  renderTabs();
  renderGroups();
  renderGrid();
  if (S.current && $("panel").open) renderPanel();
  loadUpdates(false);
  pollStats();
}

// Asked after the catalog, never before it: the grid does not wait on GitHub.
async function loadUpdates(refresh) {
  $("checked").textContent = t("checking");
  $("recheck").disabled = true;
  try {
    const u = await api(`/api/updates${refresh ? "?refresh=1" : ""}`);
    S.upd = Object.fromEntries(u.rows.map((r) => [r.unit, r]));
    S.checked = u.checked;
    renderGroups();
    renderGrid();
    if (S.current && $("panel").open) renderPanel();
  } catch (e) { /* the store works without it */ }
  finally {
    $("recheck").disabled = false;
    $("checked").textContent = S.checked
      ? `${t("checked")} ${new Date(S.checked * 1000).toLocaleTimeString(S.lang === "pt" ? "pt-BR" : "en")}`
      : "";
  }
}

// -- panel ------------------------------------------------------------------

function openPanel(id, mostrar = true) {
  closeLogs();
  S.current = id;
  S.info = { disk: null, arch: null };       // asked per app, when its panel opens
  renderPanel();
  loadInfo(id);
  $("p-form").hidden = true;
  $("p-out").hidden = true;
  $("p-log").hidden = true;
  $("p-log").open = false;
  $("p-progress").hidden = true;             // the previous app's steps must not show on this one
  S.tab = "resumo";
  for (const n of TABS) $("panel").classList.toggle(`tab-${n}`, n === "resumo");
  setStatus(null);
  $("p-tech").open = false;
  $("p-clean").hidden = true;
  $("p-section").hidden = true;
  if (mostrar) $("panel").showModal();
}

const current = () => S.apps.find((a) => a.id === S.current);

// Disk and architecture are not in the catalog: they cost a walk of the volumes
// and a registry lookup, so they are asked for when someone opens the panel.
async function loadInfo(id) {
  const a = current();
  const pedidos = [];
  if (a.installed) pedidos.push(api(`/api/disk?app=${encodeURIComponent(id)}`).then((d) => { S.info.disk = d; }));
  pedidos.push(api(`/api/arch?app=${encodeURIComponent(id)}`).then((d) => { S.info.arch = d; }));
  api(`/api/links?app=${encodeURIComponent(id)}`).then(({ links }) => {
    if (S.current !== id) return;
    const site = a.website && !links.some((l) => l.url === a.website) ? [{ kind: "project", url: a.website }] : [];
    fill($("p-project"), ...site.concat(links).map((l) =>
      h("a", { href: l.url, target: "_blank", rel: "noopener noreferrer" }, `${t("link")[l.kind]} ↗`)));
  }).catch(() => {});
  fill($("p-project"));
  renderInfo();
  await Promise.allSettled(pedidos);
  if (S.current === id && $("panel").open) renderInfo();
}

// The card beside an app in the store: what is known before installing it. The size and the architectures come from
// the registry (asked when the panel opens), so this is painted again when they arrive. Memory is not here: nobody
// publishes it, and a made-up number is worse than none.
function renderFacts() {
  const a = current(), caixa = S.factsEl;
  if (!a || !caixa || a.installed) return;
  const info = S.info || {}, arq = info.arch || {};
  const ordem = ["amd64", "arm64", "arm", "386"];
  const roda = (arq.runs || []).map((x) => x.replace(/^linux\//, ""));
  const todas = [...ordem.filter((x) => roda.includes(x)), ...roda.filter((x) => !ordem.includes(x)).sort()];   // the usual ones first, then the rest
  const principal = a.units.find((u) => u.unit === a.main_unit) || a.units[0];
  const v = principal && tagOf(principal.image), versao = arq.version || (v && v !== "latest" ? v : null);   // the project's latest release, else the tag the unit pins
  const fato = (k, v) => v ? h("div", { class: "kv" }, h("span", {}, t(k)), h("span", {}, v)) : null;
  fill(caixa,
    fato("factCategory", a.group && (a.group[S.lang] || a.group.en)),
    fato("factAuthor", a.author),
    fato("factSize", arq.download ? `${sizeOf(arq.download)}` : null),
    fato("factArch", roda.length ? todas.join(", ") : null),
    fato("factVersion", versao));
}

function renderInfo() {
  const a = current(), info = S.info || {};
  if (!a) return;
  const partes = [];
  const r = a.installed && resources(a);
  if (r) partes.push(`${t("cpu")} ${r.cpu.toFixed(1)}%`, `${t("mem")} ${mib(r.mem)}`);
  if (a.installed) partes.push(`${t("disk")} ${info.disk ? (info.disk.bytes === null ? "—" : mib(info.disk.bytes)) : t("counting")}`);
  if (a.units.some((u) => u.installed && u.override)) partes.push(t("customizedBadge"));
  const arq = info.arch;
  if (a.installed && arq && arq.runs && arq.runs.length) partes.push(`${t("runsOn")} ${arq.runs.join(", ")}`);
  renderFacts();
  const sem = arq ? arq.units.filter((u) => u.ok === false).map((u) => u.unit) : [];
  const hist = S.rhist[a.id];
  const mini = (serie, teto) => {            // heights through the CSSOM: the CSP forbids a style attribute
    const el = h("div", { class: "spark mini" }, ...serie.map((v) => { const b = h("i"); b.style.height = `${Math.max(6, Math.min(100, (v / teto) * 100))}%`; return b; }));
    return el;
  };
  fill($("p-info"), 
    partes.join(" · "),
    hist && hist.cpu.length > 1 ? h("div", { class: "rsparks" }, h("div", {}, h("small", {}, t("cpu")), mini(hist.cpu, Math.max(10, ...hist.cpu))),
      h("div", {}, h("small", {}, t("mem")), mini(hist.mem, Math.max(1, ...hist.mem)))) : null,
    sem.length ? h("span", { class: "note" }, " ", t("noArm")(arq.host, sem.join(", "))) : null);
}

function stateClass(v) {
  if (v === "paused") return "warn";
  if (["active", "healthy", "up"].includes(v)) return "ok";
  if (["failed", "unhealthy", "down", "inactive"].includes(v)) return "bad";
  if (v === "changed" || v === "duplicated") return "warn";
  return null;
}

// The manager of an installed app is split by what you are doing: Summary (what it is and how it runs), Configure,
// Files, Backups, History. Files and History are screens of their own and open over the panel.
const TABS = ["resumo", "config", "files", "backups", "history"];

function renderPanelTabs(a) {
  const barra = $("p-tabs");
  barra.hidden = !a.installed;
  $("p-danger").hidden = !a.installed;
  if (!a.installed) { fill(barra); fill($("p-danger")); return; }
  const rot = { resumo: t("tabSummary"), config: t("tabConfig"), files: `${t("files")} ↗`, backups: t("backups"), history: `${t("history")} ↗` };
  fill(barra, ...TABS.filter((k) => k !== "files" || a.has_data).map((k) =>
    h("button", { type: "button", role: "tab", class: "tab" + (S.tab === k ? " on" : ""), "aria-selected": String(S.tab === k),
                  onclick: () => setTab(k) }, rot[k])));
  fill($("p-danger"),
    h("span", {}, t("removeHint")),
    h("button", { type: "button", class: "danger", onclick: () => plan("remove") }, t("remove")));
}

function setTab(k) {
  const a = current();
  if (k === "files") { $("panel").close(); openFiles(a.id); return; }
  if (k === "history") { openHistory(a.id); return; }
  S.tab = k;
  const p = $("panel");
  for (const n of TABS) p.classList.toggle(`tab-${n}`, n === k);
  $("p-form").hidden = true;
  if (k === "resumo") $("p-section").hidden = true;
  else if (k === "backups") showBackups(a);
  else if (k === "config") showConfigTab(a);
  renderPanelTabs(a);
}

// What can be changed on an installed app, one row each; picking one opens its own editor in this same place.
function showConfigTab(a) {
  const linha = (titulo, dica, acao) => h("div", { class: "cfg-row" },
    h("button", { type: "button", class: "ghost", onclick: acao }, titulo), h("span", { class: "muted" }, dica));
  section(
    ...(a.has_env ? [linha(t("configure"), t("cfgEnvHint"), () => showEnv(a))] : []),
    ...(a.has_login ? [linha(t("login"), t("cfgLoginHint"), () => showLogin(a))] : []),
    linha(t("customize"), t("cfgCustomHint"), () => showCustom(a)),
    ...(!a.instance_of && !a.deprecated && !a.units.some((u) => u.only_unit)
      ? [linha(t("newInstance"), t("cfgInstanceHint"), () => showInstance(a))] : []));
}

function renderPanel() {
  const a = current();
  $("p-icon").src = a.icon || "";
  decoratePlate($("p-plate"), a, $("p-icon"));
  $("p-name").textContent = a.name;
  $("p-meta").textContent = [a.installed ? runDot(a)[1] : "", (a.group && a.group[S.lang]) || "", a.installed ? a.author : ""].filter(Boolean).join(" · ");   // the store card has the developer
  // Two screens for one app. The store's (not installed) is about the app itself and about installing it: the long
  // description and the screenshots. The manager's (installed) is about running it: the short description, no screenshots.
  $("panel").classList.toggle("manage", !!a.installed);
  $("panel").classList.toggle("store", !a.installed);     // the store screen: content on the left, a card with Install on the right
  const sobre = !a.installed && a.about && (a.about[S.lang] || a.about.en);
  const deInst = a.instance_of ? ` — ${t("instanceOf")(a.instance_of)}` : "";
  $("p-desc").textContent = plain(sobre || a.description[S.lang] || a.description.en)
    + deInst;

  renderSvc(a);
  // Images the project hosts (app.json, screenshots); each opens full size in a new tab.
  fill($("p-shots"), ...(a.screenshots || []).map((u) =>
    h("a", { href: u, target: "_blank", rel: "noopener noreferrer", "aria-label": t("shots") },
      h("img", { src: u, alt: "", loading: "lazy", referrerpolicy: "no-referrer" }))));
  $("p-shots").hidden = a.installed || !(a.screenshots || []).length;

  const instaladas = new Set(a.units.filter((u) => u.installed).map((u) => u.unit));
  // With a single address the primary "Open" button already goes there; the list is for stacks with several.
  fill($("p-links"), ...a.web
    .filter((w) => a.web.length > 1 && instaladas.has(w.unit) && (w.tailnet || w.local))
    .map((w) => h("a", { href: w.tailnet || w.local, target: "_blank", rel: "noopener noreferrer" },
      `${t("open")} ${a.web.length > 1 ? w.unit : ""}`.trim() + " ↗")));

  const linhas = a.units.filter((u) => u.installed);
  $("p-units").hidden = !linhas.length;
  $("p-tech").hidden = !a.installed;          // the units table has nothing to say before the install
  fill($("p-units"), 
    h("tr", {}, ...["unit", "service", "container", "installedTag", "upstream", "repo", ""]
      .map((k) => h("th", {}, k ? t(k) : ""))),
    ...linhas.map((u) => h("tr", {},
      h("td", {}, u.unit),
      h("td", { class: stateClass(u.service) }, u.service || "—"),
      h("td", { class: stateClass(u.container) }, u.container || "—"),
      h("td", {}, tagOf(u.installed_image)),
      h("td", { class: upstreamCell(u)[0] || null }, upstreamCell(u)[1]),
      h("td", { class: u.drift ? stateClass(u.drift) : "ok" }, `${u.templated ? t("pinnedOnHost") : tagOf(u.image)} · ${t(u.drift || "synced")}`),
      h("td", {},
        ...(u.service === "active" ? ["restart", "stop"] : ["start"]).map((v) =>
          h("button", { type: "button", class: "ghost", onclick: () => unitVerb(u.unit, v) }, t(v))),
        h("button", { type: "button", class: "ghost", onclick: () => showLogs(u.unit) }, t("logs")),
        u.service === "active" && (u.container || "—") !== "—"
          ? h("button", { type: "button", class: "ghost", onclick: () => showConsole(u.unit) }, t("console")) : null,
        (u.container || "—") !== "—" ? h("button", { type: "button", class: "ghost", onclick: () => showHealth(u.unit) }, t("hTab")) : null,
        (u.container || "—") !== "—" ? h("button", { type: "button", class: "ghost", onclick: () => showRuntime(u.unit) }, t("rtTab")) : null,
        u.service === "active" ? forceButton(u.unit, "force-restart", "forceRestart") : null,
        u.service === "active" ? forceButton(u.unit, "force-stop", "forceStop") : null))));

  // The reason, where it is read; and a service that is discontinued is not offered for install.
  const motivo = depReason(a);
  const trial = a.installed && a.trial ? t("trialEnds")(trialWhen(a.trial), a.trial.purge) : null;
  const caidas = a.units.filter((u) => u.installed && u.failure && !u.stopped);
  $("p-fail").hidden = !caidas.length;
  fill($("p-fail"), ...caidas.map((u) => h("p", {}, failText(u))));
  const mudaram = a.installed ? a.units.filter((u) => u.installed && u.drift === "changed") : [];
  $("p-drift").hidden = !mudaram.length;
  if (mudaram.length) showDrift(a, mudaram);
  const velho = a.podman_too_old ? t("podmanOld")(a.min_podman, S.podman) : null;
  // What to do at the first run and what is odd about the app: the notes that live beside its unit (no README per app).
  const notas = a.notes && (a.notes[S.lang] || a.notes.en);
  $("p-notes").hidden = !notas;
  $("p-notes-title").textContent = t("notes");
  fill($("p-notes-body"), ...(notas ? md(notas) : []));
  // What the unit asks for beyond its own container, read from the unit itself: seen before the click.
  const perms = a.permissions || [];
  // The install options, read-only once chosen.
  const ops = a.installed ? (a.options || []) : [];
  $("p-options").hidden = !ops.length;
  fill($("p-options"), ...(ops.length ? [h("strong", {}, t("optionsTitle"))] : []),
    ...ops.map((o) => h("div", {}, `${o.question} ${(o.values.find((v) => v.value === o.chosen) || {}).label || o.chosen}`)),
    ...(ops.length && a.options_locked ? [h("div", { class: "muted" }, t("optionLocked"))] : []));
  $("p-perms").hidden = !perms.length;
  fill($("p-perms"), ...(perms.length ? [h("strong", {}, t("permsTitle"))] : []),
    ...perms.map((p) => h("div", { class: `perm perm-${p.kind}` },
      t("perm")[p.kind] + (p.kind === "devices" || p.kind === "capabilities" ? `: ${p.items.join(", ")}` : ""))));
  // Over plain HTTP (the local-only rule or exception) an app that needs HTTPS breaks silently.
  const httpsRisco = a.requires_https && (a.access.exception || S.rule) === "local";
  $("p-notice").hidden = !motivo && !trial && !velho && !httpsRisco;
  if (motivo) $("p-notice").textContent = `${t("deprecatedNote")} ${motivo}${a.installed ? "" : ` ${t("noInstall")}`}`;
  else if (velho) $("p-notice").textContent = velho;
  else if (httpsRisco) $("p-notice").textContent = t("httpsWarn");
  else if (trial) $("p-notice").textContent = trial;
  // The thing most people came for goes first and is the loudest: open the app.
  const abrir = a.installed ? openUrl(a) : null;
  const acoes = a.installed ? [abrir ? h("a", { class: "btn", href: abrir, target: "_blank", rel: "noopener noreferrer" }, t("open")) : null, controls(a)].filter(Boolean) : [];
  if (!a.installed) {
    if (!a.deprecated) {
      const deps = needs(a);
      acoes.push(h("button", { type: "button", onclick: () => instalar(a.id) },
        deps.length ? t("installWith")(deps.map((x) => x.name).join(", ")) : t("install")));
      acoes.push(h("button", { type: "button", class: "ghost", onclick: () => showCustom(a, null, true) },
        S.preCustom[a.id] || S.preUnit[a.id] ? `${t("customize")} ✓` : t("customize")));
    }
  }
  else {
    // One update button, and only when there is something to update: a newer
    // upstream release than what runs (bump the repository if it is behind
    // too, then update — the bump is a no-op when the repository already has
    // it), or a repository that changed since the install (update). Its label
    // says where it goes, and clicking it does it — no plan, no Confirm.
    const novo = behind(a)[0];
    const mudou = a.units.find((u) => u.installed && u.drift);
    if (novo)
      acoes.push(h("button", { type: "button", onclick: () => updateNow("upgrade") },
        t("upgradeTo")(S.upd[novo.unit].there)));
    else if (mudou) {
      const alvo = !mudou.templated && tagOf(mudou.image) !== tagOf(mudou.installed_image) ? tagOf(mudou.image) : null;
      acoes.push(h("button", { type: "button", onclick: () => updateNow("update") },
        alvo ? t("upgradeTo")(alvo) : t("update")));
    }
    if (a.trial)
      acoes.push(h("button", { type: "button", onclick: () => keepTrial() }, t("trialKeep")));
    if (a.has_data && (novo || mudou))
      acoes.push(h("label", { class: "check" },
        h("input", { id: "backup-first", type: "checkbox", checked: S.backupFirst,
                     onchange: (ev) => { S.backupFirst = ev.target.checked; localStorage.setItem("qh-backup-first", S.backupFirst ? "1" : ""); } }),
        " " + t("backupFirst")));
  }
  // A not-installed app has no history and no second copy to make: those are in the tabs of an installed one.
  renderPanelTabs(a);
  fill($("p-actions"), ...acoes, a.installed && a.web.length ? accessPicker(a) : null,
    ...(a.installed ? [] : [(S.factsEl = h("div", { class: "facts" }))]));
  if (a.installed) S.factsEl = null;
  renderFacts();
}

// One plain line says how it is going; the raw output is there for whoever wants it, one click away.
function setStatus(kind, texto) {
  const el = $("p-status");
  el.hidden = !kind;
  el.className = kind ? `status-line ${kind}` : "status-line";
  el.textContent = texto || "";
}

function out(text, append = false) {
  const pre = $("p-out");
  pre.hidden = false;
  $("p-log").hidden = false;
  pre.textContent = append ? pre.textContent + text : text;
  pre.scrollTop = pre.scrollHeight;
}

function busy(on) {
  for (const b of $("panel").querySelectorAll("button:not(#p-close)")) b.disabled = on;
}

// "Install" installs: no second confirmation. Only what cannot be guessed (a secret to paste, a variable, a choice the
// developer offers) or a reason not to (discontinued, Podman too old) brings the panel up first.
async function instalar(id) {
  const aberto = $("panel").open && S.current === id;
  if (!aberto) openPanel(id, false);
  const a = current();
  if (!a.deprecated && !a.podman_too_old) await plan("install");
  const falta = ["secret", "var", "option"].some((k) => $("p-form").querySelector(`[data-${k}]`));
  if (!a.deprecated && !a.podman_too_old && !$("p-form").hidden && !falta) { await run("install"); return; }
  if (!$("panel").open) $("panel").showModal();
}

async function plan(action, file = "") {
  const a = current();
  busy(true);
  if (!["restore", "backup"].includes(action)) $("p-section").hidden = true;
  try {
    const p = await api(`/api/plan?app=${encodeURIComponent(a.id)}&action=${action}` +
                        `&file=${encodeURIComponent(file)}&lang=${S.lang}`);
    $("p-log-title").textContent = t("planTitle");
    out(`# ${t("plan")}\n\n${p.output}`);
    if (p.nothing) {
      // No Confirm for a plan with no steps: it would run and change nothing.
      $("p-form").hidden = true;
      out(`\n${t("nothingToDo")}\n`, true);
    } else buildForm(a, action, file);
  } catch (e) { out(String(e.message)); }
  finally { busy(false); }
}

// -- sections: what's new, login, backups ------------------------------------

const behind = (a) => a.units.filter((u) => u.installed && S.upd[u.unit] && S.upd[u.unit].bucket === "BEHIND");

function section(...kids) {
  fill($("p-section"), ...kids);
  $("p-section").hidden = false;
}

async function showNotes(a) {
  section(h("p", { class: "muted" }, t("checking")));
  const blocos = [h("h3", {}, t("notesFrom"))];
  for (const u of behind(a)) {
    try {
      const n = await api(`/api/notes?unit=${encodeURIComponent(u.unit)}`);
      if (behind(a).length > 1) blocos.push(h("h4", {}, u.unit));
      if (!n.releases.length) blocos.push(h("p", { class: "muted" }, n.reason || t("noNotes")));
      n.releases.forEach((r, i) => blocos.push(
        h("details", { open: i === 0 },
          h("summary", {}, `${r.tag}${r.name && r.name !== r.tag ? ` — ${r.name}` : ""}  ·  ${r.date}`),
          h("div", { class: "md" }, r.body ? md(r.body) : "—"),
          r.url && h("a", { href: r.url, target: "_blank", rel: "noopener noreferrer" }, `${t("onGithub")} ↗`))));
    } catch (e) { blocos.push(h("p", { class: "note" }, String(e.message))); }
  }
  section(...blocos);
}

// -- history: what was done, when, and how it ended, kept on disk -----------------

async function openHistory(appId = null) {
  S.histApp = appId;
  $("history").showModal();
  await renderHistory();
}

const appName = (id) => id === "_host" ? t("resources") : (S.apps.find((a) => a.id === id) || { name: id }).name;

async function renderHistory() {
  $("h-out").hidden = true;
  $("h-title").textContent = S.histApp ? `${t("history")} — ${appName(S.histApp)}` : t("history");
  try {
    const { entries } = await api(`/api/history?limit=200${S.histApp ? `&app=${encodeURIComponent(S.histApp)}` : ""}`);
    const quando = (s) => new Date(s * 1000).toLocaleString(S.lang === "pt" ? "pt-BR" : "en");
    const linha = (e) => {
      const tr = h("tr", { tabindex: "0", class: "run" },
        h("td", {}, quando(e.start)),
        !S.histApp && h("td", {}, appName(e.app)),
        h("td", {}, t("act")[e.action] || e.action, e.unit && e.unit !== e.app ? ` (${e.unit})` : ""),
        h("td", { class: e.rc === 0 ? "ok" : "bad" }, e.rc === 0 ? "✓" : `✗ ${e.rc ?? "?"}${e.rolled_back ? ` ↩ ${t("rolledBack")}` : ""}`),
        h("td", {}, `${Math.max(0, Math.round(e.end - e.start))}s`));
      tr.onclick = () => showRun(e);
      tr.onkeydown = (ev) => { if (ev.key === "Enter") showRun(e); };
      return tr;
    };
    fill($("h-list"), entries.length
      ? h("table", { class: "hist" },
          h("tr", {}, h("th", {}, t("when")), !S.histApp && h("th", {}, "App"), h("th", {}, t("what")),
            h("th", {}, t("result")), h("th", {}, t("took"))),
          ...entries.map(linha))
      : h("p", { class: "muted" }, t("noHistory")));
  } catch (e) { fill($("h-list"), h("p", { class: "note" }, String(e.message))); }
}

async function showRun(e) {
  try {
    const d = await api(`/api/history/${encodeURIComponent(e.id)}`);
    $("h-out").textContent = `${t("act")[d.action] || d.action} · ${appName(d.app)} · ${t("from")} ${d.from || "?"}\n\n${d.output || "—"}`;
    $("h-out").hidden = false;
    $("h-out").scrollTop = 0;
  } catch (err) { $("h-out").textContent = String(err.message); $("h-out").hidden = false; }
}

// -- Customize: a drop-in beside the unit, the way CasaOS lets you edit an app -------------
// The unit stays the repository's. Each group is shown as the unit carries it now (with
// any earlier customization applied); what the person edits is sent whole, and the
// server decides what differs from the unit, checks it, and writes only that.

const campo = (type, value, placeholder, extra = {}) =>
  h("input", { type, value: value ?? "", placeholder, autocomplete: "off", ...extra });
const escolha = (opcoes, atual) => {
  const s = h("select", {}, ...opcoes.map(([v, rotulo]) => h("option", { value: v, selected: v === atual }, rotulo)));
  s.value = atual;
  return s;
};

const linhas = {
  ports(it) {
    if (it && it.opaque) return opaca(it);
    const bind = campo("text", it && it.bind, t("ipOpt")), host = campo("number", it ? it.host : "", t("hostPort"));
    const cont = campo("number", it ? it.container : "", t("contPort"));
    const proto = escolha([["tcp", "TCP"], ["udp", "UDP"]], (it && it.proto) || "tcp");
    return { els: [bind, host, cont, proto], read: () => host.value === "" ? null :
      { bind: bind.value.trim(), host: Number(host.value), container: Number(cont.value), proto: proto.value } };
  },
  volumes(it) {
    if (it && it.opaque) return opaca(it);
    const host = campo("text", it && it.host, t("hostPath")), cont = campo("text", it && it.container, t("contPath"));
    const escolher = dirPicker(host);
    const rotulo = escolha([["Z", t("labelZ")], ["z", t("labelz")], ["", t("labelNone")]], it ? it.label : "Z");
    const ro = h("input", { type: "checkbox", checked: !!(it && it.ro), "aria-label": t("readOnly") });
    return { els: [host, escolher.btn, cont, rotulo, h("label", { class: "check" }, ro, ` ${t("readOnly")}`), escolher.painel],
      read: () => host.value.trim() === "" ? null :
        { host: host.value.trim(), container: cont.value.trim(), label: rotulo.value, ro: ro.checked, extra: (it && it.extra) || [] } };
  },
  env(it) {
    if (it && it.opaque) return opaca(it);
    const k = campo("text", it && it.key, t("envKey")), v = campo("text", it && it.value, t("envValue"));
    return { els: [k, v], read: () => k.value.trim() === "" ? null : { key: k.value.trim(), value: v.value } };
  },
  devices(it) {
    if (it && it.opaque) return opaca(it);
    const d = campo("text", it && it.path, t("devPath"));
    return { els: [d], read: () => d.value.trim() === "" ? null : { path: d.value.trim() } };
  },
};

// The folder picker beside a volume's host path (what CasaOS has): the folders inside the permitted roots,
// by the server's own list, so it cannot lead anywhere the form would refuse. A new sub-folder is typed
// and created when the customization is applied.
function dirPicker(campoHost) {
  const painel = h("div", { class: "picker" });
  painel.hidden = true;
  const NOVA = /^[A-Za-z0-9._@+-]+$/;
  async function ir(caminho) {
    let r;
    try { r = await api(`/api/dirs?path=${encodeURIComponent(caminho || "")}`); }
    catch (e) { return caminho ? ir("") : fill(painel, h("p", { class: "note" }, String(e.message))); }
    const nova = h("input", { type: "text", placeholder: t("newFolder"), "aria-label": t("newFolder"), autocomplete: "off" });
    const usar = () => {
      const nome = nova.value.trim();
      if (nome && !NOVA.test(nome)) return nova.setAttribute("aria-invalid", "true");
      campoHost.value = r.value + (nome ? `/${nome}` : "");
      painel.hidden = true;
    };
    fill(painel,
      h("div", { class: "picker-bar" },
        r.path ? h("button", { type: "button", class: "ghost", title: t("up"), "aria-label": t("up"),
                               onclick: () => ir(r.parent || "") }, "↑") : null,
        h("code", {}, r.shown || t("roots"))),
      r.dirs.length
        ? h("ul", { class: "picker-list" }, ...r.dirs.map((d) =>
            h("li", {}, h("button", { type: "button", class: "ghost", onclick: () => ir(d.path) }, `📁 ${d.name}`))))
        : h("p", { class: "cust-note" }, r.path ? t("noSubfolders") : t("noRoots")),
      r.path ? h("div", { class: "row" }, nova, h("button", { type: "button", onclick: usar }, t("useFolder"))) : null);
  }
  const btn = h("button", { type: "button", class: "ghost", title: t("pickFolder"), "aria-label": t("pickFolder"),
    onclick: () => { painel.hidden = !painel.hidden; if (!painel.hidden) ir(campoHost.value.trim().includes("$") ? "" : campoHost.value.trim()); } }, "📁");
  return { btn, painel };
}

// An entry that is not a plain shape (a ${VAR} in a port, say): shown, kept as it is, removable.
const opaca = (it) => ({ els: [h("code", {}, it.raw), h("span", { class: "cust-note" }, t("fromUnit"))],
                         read: () => ({ raw: it.raw, opaque: true }) });

function grupo(nome, titulo, dica, itens, cab = null) {
  const rows = [], caixa = h("div");
  // Column titles above the rows, as in CasaOS: what each box is, said once instead of in every row.
  const mostrar = () => fill(caixa, ...(rows.length
    ? [cab ? h("div", { class: "cust-head", "data-kind": nome, "aria-hidden": "true" }, ...cab.map((x) => h("span", {}, x))) : null, ...rows.map((r) => r.row)]
    : [h("p", { class: "cust-empty" }, `ⓘ ${t("emptyRows")}`)]));
  const juntar = (it) => {
    const r = linhas[nome](it);
    r.row = h("div", { class: "cust-row", "data-kind": nome }, ...r.els,
      h("button", { type: "button", class: "x", title: t("removeRow"), "aria-label": t("removeRow"),
                    onclick: () => { rows.splice(rows.indexOf(r), 1); mostrar(); } }, "✕"));
    rows.push(r);
  };
  itens.forEach(juntar);
  mostrar();
  return { el: h("div", { class: "cust-group" },
      h("h4", {}, titulo, h("button", { type: "button", class: "ghost", onclick: () => { juntar(null); mostrar(); } }, `+ ${t("add")}`)),
      dica && h("p", { class: "cust-note" }, dica), caixa),
    read: () => rows.map((r) => r.read()).filter(Boolean) };
}

// A slider with the stops written under it, as in CasaOS; the last stop is "no limit". It only changes the
// value once moved, so a limit the unit already has that is not one of the stops is kept as it is.
function limiteDeslizante(paradas, rotulos, atual, aoMudar, ligado) {
  const i0 = atual === "" ? paradas.length - 1 : Math.max(0, paradas.findIndex((p, i) => i < paradas.length - 1 && p.v === atual));
  const r = h("input", { type: "range", min: 0, max: paradas.length - 1, step: 1, value: i0, disabled: !ligado,
                         "aria-label": rotulos.nome });
  r.value = String(i0);
  const lido = h("span", { class: "slider-val" }, atual === "" ? t("noLimit") : atual);
  r.addEventListener("input", () => {
    const p = paradas[Number(r.value)];
    aoMudar(p.v);
    lido.textContent = p.v === "" ? t("noLimit") : p.rotulo;
  });
  return h("div", { class: "slider" }, h("div", { class: "slider-head" }, h("span", {}, rotulos.nome), lido), r,
    h("div", { class: "slider-ticks", "aria-hidden": "true" }, ...paradas.map((p) => h("span", {}, p.v === "" ? "∞" : p.rotulo))));
}
const PARADAS_MEM = [["256m", "256 MB"], ["512m", "512 MB"], ["1g", "1 GB"], ["2g", "2 GB"], ["4g", "4 GB"], ["8g", "8 GB"], ["", ""]]
  .map(([v, rotulo]) => ({ v, rotulo }));
const PARADAS_CPU = [["0.25", "¼"], ["0.5", "½"], ["1", "1"], ["2", "2"], ["4", "4"], ["8", "8"], ["", ""]]
  .map(([v, rotulo]) => ({ v, rotulo }));

// The form of ONE unit (a container). `pre`: before an install — it works on the unit as it will be written
// and the choice is kept in S.preCustom; the install applies it once the unit exists.
async function formDaUnidade(a, u, pre) {
  const unit = u.unit;
  let d = await api(`/api/custom?unit=${encodeURIComponent(unit)}${pre ? "&pre=1" : ""}`);
  const guardada = pre && (S.preCustom[a.id] || {})[unit];
  if (guardada) {          // what was chosen before comes back in the form
    d = { ...d, effective: { ...d.effective, ports: guardada.ports, volumes: guardada.volumes, env: guardada.env,
                             devices: guardada.devices, caps: guardada.caps },
          restart: guardada.restart || d.restart, limit_values: { memory: guardada.limits.memory, cpus: guardada.limits.cpus } };
  }
  const G = {
    ports: grupo("ports", t("cPorts"), t("portsHint"), d.effective.ports, [t("hHost"), t("hContainer"), t("hProto"), t("hIp"), ""]),
    volumes: grupo("volumes", t("cVolumes"), t("volumesHint")(d.roots), d.effective.volumes, [t("hHost"), "", t("hContainer"), t("hLabel"), "", ""]),
    env: grupo("env", t("cEnv"), t("custEnvHint"), d.effective.env, [t("hKey"), t("hValue"), ""]),
    devices: grupo("devices", t("cDevices"), null, d.effective.devices),
  };
  const tem = new Set(d.effective.caps.map((c) => c.name));
  const caps = [...new Set([...d.caps_ok, ...tem])].map((n) =>
    ({ n, box: h("input", { type: "checkbox", id: `cap-${unit}-${n}`, checked: tem.has(n) }) }));
  const reinicio = escolha(d.restarts.map((r) => [r, r]), d.restart || "always");
  // Limits need the controllers delegated to the user; a field the host cannot honour is shown, disabled,
  // with the reason. Its value still goes back as it is, so what the unit already says is never "changed".
  const lv = d.limit_values || { memory: "", cpus: "" };
  let mem = lv.memory, cpus = lv.cpus;
  const config = () => ({ ports: G.ports.read(), volumes: G.volumes.read(), env: G.env.read(), devices: G.devices.read(),
    caps: caps.filter((c) => c.box.checked).map((c) => ({ name: c.n })), restart: reinicio.value,
    limits: { memory: String(mem).trim(), cpus: String(cpus).trim() } });
  const saida = h("div", { class: "cust-out" });
  // The unit as text: what it is, and the person's own version of it. Saved as a whole file the install and every
  // update then use, instead of the repository's; the form above does not apply to a unit rewritten this way.
  const rawSec = rawUnit(a, unit, d, pre);
  const imagem = (u.image || "").replace(/@sha256:.*/, "");
  const repo = imagem.replace(/:[^/:]*$/, "");
  const tag = u.templated ? t("latestPinned") : tagOf(u.image);
  const lerLeitura = (rotulo, valor) => h("label", { class: "field ro" }, rotulo, h("input", { type: "text", value: valor, readonly: true }));
  const el = h("form", { class: "cust", onsubmit: (ev) => ev.preventDefault() },
    h("div", { class: "cust-two" }, lerLeitura(t("dockerImage"), repo), lerLeitura(t("dockerTag"), tag)),
    lerLeitura(t("containerName"), unit),
    d.base_changed ? h("p", { class: "note" }, t("baseChanged")) : null,
    d.override ? h("p", { class: "cust-note" }, `${t("filePath")}: ${d.file}`) : null,
    G.ports.el, G.volumes.el, G.env.el, G.devices.el,
    h("div", { class: "cust-group" }, h("h4", {}, t("cLimits")),
      h("p", { class: "cust-note" }, d.limits.memory && d.limits.cpu ? t("limitsHint") : t("limitsOff")),
      limiteDeslizante(PARADAS_MEM, { nome: t("limMemory") }, lv.memory, (v) => { mem = v; }, d.limits.memory),
      limiteDeslizante(PARADAS_CPU, { nome: t("limCpus") }, lv.cpus, (v) => { cpus = v; }, d.limits.cpu)),
    h("div", { class: "cust-group" }, h("h4", {}, t("cRestart")), reinicio),
    // Advanced: tucked away, with each permission said in words, since the names mean nothing to most people.
    h("details", { class: "cust-group tech adv", open: caps.some((c) => c.box.checked) },
      h("summary", {}, t("cCaps")), h("p", { class: "cust-note" }, t("capsHint")),
      h("div", { class: "caps" }, ...caps.map((c) => h("label", { class: "check cap", for: `cap-${unit}-${c.n}`, title: t("capInfo")[c.n] || c.n },
        c.box, h("span", {}, c.n, t("capInfo")[c.n] ? h("small", {}, t("capInfo")[c.n]) : null))))),
    rawSec.el,
    saida);

  async function previa() {
    try {
      const r = await api("/api/custom/preview", { unit, config: config(), ...(pre ? { pre: true } : {}) });
      fill(saida,
        r.errors.length ? h("ul", { class: "cust-errors" }, ...r.errors.map((e) => h("li", {}, e))) : null,
        r.warnings.length ? h("ul", { class: "cust-warn" }, ...r.warnings.map((w) => h("li", {}, w))) : null,
        r.changed ? h("details", { open: true }, h("summary", {}, t("fileToWrite")), h("pre", {}, r.text))
                  : (r.errors.length ? null : h("p", { class: "cust-note" }, t("nothingChanged"))),
        r.generated ? h("details", {}, h("summary", {}, t("generated")), h("pre", {}, r.generated)) : null);
      return r;
    } catch (e) { fill(saida, h("p", { class: "note" }, String(e.message))); return { errors: [String(e.message)], changed: false }; }
  }
  return { unit, el, d, config, previa, guardada: !!guardada, raw: rawSec };
}

// The `.container` as text, in the Customize screen: read it, change it, check it, keep it as the person's own.
function rawUnit(a, unit, d, pre) {
  d = { unit_source: "", repo_text: "", ...d };
  const salvo = pre && (S.preUnit[a.id] || {})[unit];
  const inicial = salvo !== undefined && salvo !== false ? salvo : d.unit_source;
  const area = h("textarea", { class: "raw", rows: 18, spellcheck: false, "aria-label": `${unit}.container`, id: `raw-${unit}` });
  area.value = inicial;
  const saida = h("div", { class: "cust-out" });
  const ack = h("input", { type: "checkbox", id: `rawack-${unit}` });
  const ackLinha = h("label", { class: "check", hidden: true }, ack, ` ${t("rawAck")}`);
  const estado = h("p", { class: "cust-note" });
  const atual = () => area.value;
  const difere = () => area.value.trim() !== d.repo_text.trim();
  const editado = () => area.value !== d.unit_source;          // against what is saved (installed) now
  const marca = () => { estado.textContent = difere() ? t("rawDiff") : t("rawSame"); };
  area.addEventListener("input", marca);
  marca();
  async function revisar() {
    let r;
    try { r = await api("/api/custom/unit-check", { unit, text: area.value }); }
    catch (e) { fill(saida, h("p", { class: "note" }, String(e.message))); return { errors: [String(e.message)], warnings: [] }; }
    fill(saida,
      r.errors.length ? h("ul", { class: "cust-errors" }, ...r.errors.map((x) => h("li", {}, x))) : null,
      r.warnings.length ? h("ul", { class: "cust-warn" }, ...r.warnings.map((x) => h("li", {}, x))) : null,
      !r.errors.length && !r.warnings.length ? h("p", { class: "cust-note" }, t("rawOk")) : null);
    ackLinha.hidden = !r.warnings.length;
    return r;
  }
  const el = h("details", { class: "cust-group tech raw-sec", open: !!d.custom_unit || (salvo !== undefined && salvo !== false) },
    h("summary", {}, t("rawTitle")),
    h("p", { class: "cust-note" }, d.custom_unit ? t("rawCustom") : t("rawRepo")),
    h("p", { class: "note" }, t("rawWarn")),
    area, estado,
    h("div", { class: "row" },
      h("button", { type: "button", class: "ghost", onclick: revisar }, t("rawCheck")),
      h("button", { type: "button", class: "ghost", onclick: () => { area.value = d.repo_text; marca(); } }, t("rawRestore")),
      h("button", { type: "button", class: "ghost", onclick: async () => {
        try { await navigator.clipboard.writeText(area.value); estado.textContent = t("rawCopied"); } catch (e) { /* no clipboard here */ }
      } }, t("rawCopy"))),
    saida, ackLinha,
    d.installed_text ? h("details", {}, h("summary", {}, t("rawRunning")),
      h("pre", {}, d.installed_text + (d.text ? `\n# ---- ${d.file} ----\n${d.text}` : ""))) : null);
  return { el, value: atual, difere, editado, revisar, ack: () => ack.checked, open: () => { el.open = true; } };
}

// A unit the repository changed after the install counts as an update; this says what changed, before it is applied.
async function showDrift(a, unidades) {
  $("p-drift-title").textContent = t("driftTitle")(unidades.map((u) => u.unit).join(", "));
  $("p-drift-hint").textContent = t("driftHint");
  const partes = [];
  for (const u of unidades) {
    try {
      const d = await api(`/api/drift?unit=${encodeURIComponent(u.unit)}`);
      if (a.id !== S.current) return;                           // the person went elsewhere meanwhile
      if (unidades.length > 1) partes.push(h("b", {}, u.unit), "\n");
      for (const linha of (d.diff || t("driftNone")).split("\n"))
        partes.push(h("span", { class: linha.startsWith("+") && !linha.startsWith("+++") ? "add" : linha.startsWith("-") && !linha.startsWith("---") ? "del" : "ctx" }, `${linha}\n`));
    } catch (e) { partes.push(String(e.message), "\n"); }
  }
  fill($("p-drift-diff"), ...partes);
}

// What the person sees: a sheet over the page, a tab per container, the fields of the chosen one, and the
// one thing to do at the bottom — Install (before the install) or Save and apply.
async function showCustom(a, unit, pre = false) {
  const todas = pre ? a.units : a.units.filter((u) => u.installed);
  const principal = a.units.find((u) => u.unit === a.main_unit) || mainUnit(a);
  // The app itself first, then its helpers (database, cache, workers) in their own tabs.
  const unidades = [...todas].sort((x, y) => (y === principal) - (x === principal));
  unit = unit || (principal && unidades.includes(principal) ? principal : unidades[0]).unit;
  const formas = [];
  try { for (const u of unidades) formas.push(await formDaUnidade(a, u, pre)); }
  catch (e) { return section(h("p", { class: "note" }, String(e.message))); }
  let ativa = formas.find((f) => f.unit === unit) || formas[0];
  const corpo = $("c-body"), abas = $("c-tabs");
  $("c-title").textContent = pre ? `${t("install")} ${a.name}` : `${t("customize")} · ${a.name}`;

  const mostrar = (f) => {
    ativa = f;
    fill(abas, ...formas.map((x) => h("button", { type: "button", role: "tab", "aria-selected": String(x === f),
      onclick: () => mostrar(x) }, x.unit.startsWith(`${a.id}-`) ? x.unit.slice(a.id.length + 1) : x.unit)));
    abas.hidden = formas.length < 2;
    fill(corpo, pre ? h("p", { class: "cust-note" }, t("preIntro")) : h("p", { class: "cust-note" }, t("custIntro")), f.el);
  };

  // Every unit with a change is checked first; the first with an error is brought forward and nothing goes on.
  const conferir = async () => {
    for (const f of formas) {
      const r = await f.previa();
      if (r.errors.length) { mostrar(f); return null; }
      f.r = r;
    }
    return formas.filter((f) => f.r.changed);
  };
  const instalar = async () => {
    const mudadas = await conferir();
    if (!mudadas) return;
    if (mudadas.length && formas.some((f) => f.raw.difere() && mudadas.includes(f))) {   // both at once: the code wins
      const f = formas.find((x) => x.raw.difere() && mudadas.includes(x));
      mostrar(f); f.raw.open();
      fill(f.el.querySelector(".raw-sec .cust-out") || f.el, h("p", { class: "note" }, t("rawFormOff")));
    }
    // A unit rewritten whole is reviewed first; its form is not applied (the code is the change).
    const proprias = {};
    let precisaAck = false;
    for (const f of formas) {
      if (!f.raw.difere()) continue;
      const rv = await f.raw.revisar();
      if (rv.errors.length) { mostrar(f); f.raw.open(); return; }
      if (rv.warnings.length && !f.raw.ack()) { precisaAck = true; mostrar(f); f.raw.open(); }
      proprias[f.unit] = f.raw.value();
    }
    if (precisaAck) return;
    S.preCustom[a.id] = {};
    for (const f of mudadas) if (!(f.unit in proprias)) S.preCustom[a.id][f.unit] = f.config();
    if (!Object.keys(S.preCustom[a.id]).length) delete S.preCustom[a.id];
    if (Object.keys(proprias).length) { S.preUnit[a.id] = proprias; S.preUnitAck[a.id] = true; } else { delete S.preUnit[a.id]; delete S.preUnitAck[a.id]; }
    $("custom").close();
    await plan("install");
  };
  const aplicar = async () => {
    // A unit whose code was edited is saved as the person's own first (reviewed, and the warnings acknowledged).
    const editadas = formas.filter((f) => f.raw.editado());
    for (const f of editadas) {
      const rv = await f.raw.revisar();
      if (rv.errors.length || (rv.warnings.length && !f.raw.ack())) { mostrar(f); f.raw.open(); return; }
    }
    const mudadas = editadas.length ? [] : await conferir();
    if (!mudadas) return;
    if (!mudadas.length && !editadas.length) return;
    $("custom").close();
    for (const f of editadas)
      await follow(() => api("/api/custom/unit-save", { unit: f.unit, text: f.raw.value(), ack: f.raw.ack() }));
    for (const f of mudadas) await follow(() => api("/api/custom/apply", { unit: f.unit, config: f.config() }));
  };
  const reverter = async () => {
    $("custom").close();
    await follow(() => api("/api/custom/reset", { unit: ativa.unit }));
  };
  const descartar = () => {
    delete S.preCustom[a.id];
    delete S.preUnit[a.id];
    delete S.preUnitAck[a.id];
    $("custom").close();
    showCustom(a, ativa.unit, true);
  };

  fill($("c-foot"),
    h("button", { type: "button", class: "ghost", onclick: () => ativa.previa() }, t("previewBtn")),
    pre && (S.preCustom[a.id] || S.preUnit[a.id]) ? h("button", { type: "button", class: "danger", onclick: descartar }, t("preDiscard")) : null,
    !pre && formas.some((f) => f.d.override) ? h("button", { type: "button", class: "danger", onclick: reverter }, t("revertBtn")) : null,
    !pre && formas.some((f) => f.d.custom_unit) ? h("button", { type: "button", class: "danger", title: t("rawUnitReset"), onclick: async () => {
      const f = formas.find((x) => x.d.custom_unit && x.unit === ativa.unit) || formas.find((x) => x.d.custom_unit);
      $("custom").close();
      await follow(() => api("/api/custom/unit-reset", { unit: f.unit }));
    } }, t("rawRestore")) : null,
    h("span", { class: "grow" }),
    h("button", { type: "button", class: "ghost", onclick: () => $("custom").close() }, t("cancel")),
    pre ? h("button", { type: "button", onclick: instalar }, t("install")) : h("button", { type: "button", onclick: aplicar }, t("saveApply")));
  mostrar(ativa);
  if (!$("custom").open) $("custom").showModal();
}

// The settings of a service: its .env, as the .example files lay it out. An
// optional setting ships commented out; ticking it turns it on, unticking an
// active one comments it out again. Only what changed is sent.
// The box for one setting, by the type its .env.example declares (`# type: number`): the right input
// for the browser to validate, and `read()` for what goes back. A value the type would not hold
// (the file says `4G` for a number) stays a text box, so opening the form never blanks it.
const unquote = (v) => String(v).trim().replace(/^["']|["']$/g, "");
function envInput(e, id) {
  const tipo = e.type || "text";
  if (tipo === "bool" && e.bool) {
    const [on, off] = e.bool;
    const el = h("input", { id, type: "checkbox", checked: unquote(e.value).toLowerCase() === on.toLowerCase(), disabled: !e.active });
    return { el, read: () => (el.checked ? on : off) };
  }
  const v = unquote(e.value);
  const servePara = { number: v === "" || (v.trim() !== "" && !Number.isNaN(Number(v))),
                      email: true, url: true, ip: true, password: true }[tipo];
  const html = !servePara ? (e.sensitive ? "password" : "text")
    : { password: "password", number: "number", email: "email", url: "url" }[tipo] || (e.sensitive ? "password" : "text");
  const el = h("input", { id, type: html, value: e.value, autocomplete: "off", disabled: !e.active,
                          step: html === "number" ? "any" : null,
                          pattern: tipo === "ip" && servePara ? "[0-9A-Fa-f:.]+" : null,
                          title: tipo === "ip" ? "IPv4 / IPv6" : null });
  return { el, read: () => el.value };
}

async function showEnv(a) {
  try {
    const { files } = await api(`/api/env?app=${encodeURIComponent(a.id)}`);
    if (!files.length) return section(h("p", { class: "muted" }, t("noEnv")));
    const linhas = [];
    for (const f of files) {
      const campos = f.entries.map((e, i) => {
        const id = `e-${f.file}-${i}`;
        const caixa = h("input", { type: "checkbox", id: `${id}-on`, checked: e.active, "aria-label": t("active") });
        const { el: valor, read } = envInput(e, id);
        caixa.onchange = () => { valor.disabled = !caixa.checked; };
        return { e, caixa, valor, read, linha: h("div", { class: "env-row" },
          caixa, h("label", { for: id }, e.key), valor,
          e.type && e.type !== "text" ? h("span", { class: "muted env-type" }, t("envType")[e.type] || e.type) : null,
          e.help && h("p", { class: "help" }, plain(e.help))) };
      });
      linhas.push(h("h4", {}, f.file), ...campos.map((c) => c.linha));
      f.campos = campos;
    }
    const form = h("form", { class: "env" }, h("h3", {}, t("configure")),
      h("p", { class: "help" }, `${t("envHint")} ${t("envNote")}`), ...linhas,
      h("div", { class: "row" }, h("button", { type: "submit" }, t("envSave"))));
    form.onsubmit = async (ev) => {
      ev.preventDefault();
      for (const f of files) {
        const mudar = {}, off = [];
        for (const { e, caixa, read } of f.campos) {
          const novo = read();
          if (caixa.checked && (!e.active || (e.type === "bool" ? novo.toLowerCase() !== unquote(e.value).toLowerCase() : novo !== e.value))) mudar[e.key] = novo;
          else if (!caixa.checked && e.active) off.push(e.key);
        }
        if (!Object.keys(mudar).length && !off.length) continue;
        $("p-section").hidden = true;
        await follow(() => api("/api/env/save", { app: a.id, file: f.file, set: mudar, off }));
      }
    };
    section(form);
  } catch (e) { section(h("p", { class: "note" }, String(e.message))); }
}

async function showLogin(a) {
  try {
    const l = await api(`/api/login?app=${encodeURIComponent(a.id)}`);
    if (!l.available) return section(h("p", { class: "muted" }, t("noLogin")));
    const senha = h("input", { type: "password", readonly: true, value: l.password });
    const copiar = (valor, botao) => navigator.clipboard.writeText(valor)
      .then(() => { botao.textContent = t("copied"); });
    const linhas = [h("h3", {}, t("login"))];
    if (l.user) {
      const b = h("button", { type: "button", class: "ghost" }, t("copy"));
      b.onclick = () => copiar(l.user, b);
      linhas.push(h("div", { class: "cred" }, h("label", {}, t("user")),
                    h("input", { type: "text", readonly: true, value: l.user }), b));
    }
    const ver = h("button", { type: "button", class: "ghost" }, t("show"));
    ver.onclick = () => {
      const oculto = senha.type === "password";
      senha.type = oculto ? "text" : "password";
      ver.textContent = oculto ? t("hide") : t("show");
    };
    const cp = h("button", { type: "button", class: "ghost" }, t("copy"));
    cp.onclick = () => copiar(l.password, cp);
    linhas.push(h("div", { class: "cred" }, h("label", {}, t("password")), senha, ver, cp));
    section(...linhas);
  } catch (e) { section(h("p", { class: "note" }, String(e.message))); }
}

const mib = (n) => n >= 1 << 30 ? `${(n / (1 << 30)).toFixed(1)} GB` : `${Math.round(n / (1 << 20))} MB`;

// CPU and memory of an app: the sum over its units that are running.
function resources(a) {
  const us = a.units.filter((u) => u.installed && S.stats[u.unit]).map((u) => S.stats[u.unit]);
  if (!us.length) return null;
  return { cpu: us.reduce((s, x) => s + x.cpu, 0), mem: us.reduce((s, x) => s + x.mem, 0) };
}

const resText = (a) => { const r = resources(a); return r ? `${r.cpu.toFixed(1)}% · ${mib(r.mem)}` : ""; };

// In place, not a re-render: it runs every few seconds and must not reset hover or focus.
function updateResources() {
  for (const a of S.apps) {
    const el = document.querySelector(`[data-res="${a.id}"]`);
    if (el) el.textContent = resText(a);
  }
  if (S.current && $("panel").open) renderInfo();
}

async function pollStats() {
  if (document.hidden || !S.apps.some((a) => a.installed)) return;
  try {
    S.stats = (await api("/api/stats")).stats;
    for (const a of S.apps) {                       // a short history per app, for the sparklines in its panel
      const r = a.installed && resources(a);
      if (!r) continue;
      const h2 = (S.rhist[a.id] = S.rhist[a.id] || { cpu: [], mem: [] });
      h2.cpu.push(r.cpu); h2.mem.push(r.mem);
      if (h2.cpu.length > 30) { h2.cpu.shift(); h2.mem.shift(); }
    }
    updateResources();
  } catch (e) { /* next turn */ }
}

const tamanho = (n) => n > 1 << 30 ? `${(n / (1 << 30)).toFixed(1)} GB`
  : n > 1 << 20 ? `${(n / (1 << 20)).toFixed(1)} MB` : `${Math.ceil(n / 1024)} KB`;

async function showBackups(a) {
  try {
    const b = await api(`/api/backups?app=${encodeURIComponent(a.id)}`);
    const arquivo = h("input", { type: "file", accept: ".gz,.tar.gz,application/gzip" });
    const enviar = h("button", { type: "button", class: "ghost" }, t("upload"));
    enviar.onclick = () => upload(a, arquivo);
    section(
      h("h3", {}, t("backups")),
      h("p", { class: "muted" }, `${t("backupDir")}: ${b.dir}`),
      b.backups.length
        ? h("table", { class: "backups" }, ...b.backups.map((x) => h("tr", {},
            h("td", {}, x.file),
            h("td", {}, new Date(x.date * 1000).toLocaleString(S.lang === "pt" ? "pt-BR" : "en")),
            h("td", {}, tamanho(x.size)),
            h("td", {},
              h("a", { href: `/api/backup/file?app=${encodeURIComponent(a.id)}&file=${encodeURIComponent(x.file)}`,
                       download: x.file }, t("download")), " ",
              h("button", { type: "button", class: "ghost", onclick: () => plan("restore", x.file) },
                t("restoreAction"))))))
        : h("p", { class: "muted" }, t("noBackups")),
      h("div", { class: "row" },
        h("button", { type: "button", onclick: () => plan("backup") }, t("backupNow")), arquivo, enviar));
  } catch (e) { section(h("p", { class: "note" }, String(e.message))); }
}

async function upload(a, input) {
  const f = input.files[0];
  if (!f) return;
  busy(true);
  out(`${t("working")}\n`);
  try {
    const r = await fetch(`/api/backup/upload?app=${encodeURIComponent(a.id)}`, {
      method: "POST", body: f,
      headers: { "X-QH-Store": "1", "Content-Type": "application/octet-stream" },
    });
    const d = await r.json();
    out(r.ok ? `${d.file}\n${t("done")}\n` : `${d.error}\n`, true);
  } catch (e) { out(String(e.message), true); }
  finally { busy(false); showBackups(a); }
}

// What the terminal would have asked: `manual` secrets and unset [vars].
function buildForm(a, action, file = "") {
  const form = $("p-form");
  const campos = [];
  if (action === "backup") campos.push(h("p", { class: "help" }, t("backupNote")));
  if (action === "restore") {
    // The same guard as the terminal: the name, typed. qh checks it again.
    campos.push(h("p", { class: "note" }, t("restoreNote")));
    campos.push(h("label", { for: "confirm" }, `${t("typeToConfirm")} ${a.id}`));
    campos.push(h("input", { id: "confirm", type: "text", "data-confirm": "1", autocomplete: "off" }));
  }
  if (action === "install") {
    // The services it needs come first, and so do their questions.
    const deps = needs(a);
    campos.push(h("p", { class: "lead" }, t("readyToInstall")(a.name)));
    if (deps.length) campos.push(h("p", { class: "note" }, t("requiresNote")(deps.map((x) => x.name).join(", "))));
    for (const x of [...deps, a]) campos.push(...asksFields(x));
  }
  if (action === "install") {
    // What the developer offers at the first install (a database, say): chosen here, read-only afterwards.
    for (const o of a.options || []) {
      const sel = h("select", { "data-option": o.key, "aria-label": o.question },
        ...o.values.map((v) => h("option", { value: v.value, selected: v.value === o.chosen }, v.label)));
      sel.value = o.chosen;
      campos.push(h("label", {}, `${o.question} `, sel));
    }
  }
  if (action === "install") {
    // Trying an app for a while is for people who know they want it: tucked away, not in the way of the install.
    campos.push(h("details", { class: "tech adv" }, h("summary", {}, t("advanced")),
      h("label", { for: "trial" }, t("trialLabel")),
      h("select", { id: "trial", "data-trial": "1" },
        ...[["", t("trialNone")], ["1h", "1 h"], ["6h", "6 h"], ["1d", "1 d"], ["7d", "7 d"], ["reboot", t("trialReboot")]]
          .map(([v, r]) => h("option", { value: v }, r))),
      h("label", { class: "check" }, h("input", { id: "trial-purge", type: "checkbox" }), " " + t("trialPurge")),
      h("p", { class: "help" }, t("trialHint"))));
  }
  if (action === "install" && (S.preCustom[a.id] || S.preUnit[a.id]))
    campos.push(h("p", { class: "note" }, t("preRides")([...Object.keys(S.preCustom[a.id] || {}), ...Object.keys(S.preUnit[a.id] || {})].join(", "))));
  if (action === "remove") {
    campos.push(h("p", { class: "note" }, t("removeNote")));
    // Deleting the data is its own, typed, step — the same guard a restore has.
    const confirma = h("input", { id: "purge-confirm", type: "text", "data-confirm": "1", autocomplete: "off" });
    const bloco = h("div", { class: "purge" }, h("p", { class: "note bad" }, t("purgeWarn")),
      h("label", { for: "purge-confirm" }, `${t("typeToConfirm")} ${a.id}`), confirma);
    bloco.hidden = true;
    const caixa = h("input", { id: "purge", "data-purge": "1", type: "checkbox", onchange: (ev) => { bloco.hidden = !ev.target.checked; } });
    campos.push(h("label", { class: "check" }, caixa, ` ${t("purgeData")}`), bloco);
  }
  campos.push(h("div", {},
    h("button", { type: "submit", class: ["remove", "restore"].includes(action) ? "danger" : null },
      action === "install" ? t("installNow") : t("confirm")), " ",
    h("button", { type: "button", class: "ghost", onclick: () => { form.hidden = true; } }, t("cancel"))));
  fill(form, ...campos);
  form.onsubmit = (ev) => { ev.preventDefault(); run(action, file); };
  form.hidden = false;
}

async function keepTrial() {
  const a = current();
  await follow(() => api("/api/run", { app: a.id, action: "trial-keep" }));
}

async function run(action, file = "") {
  const a = current();
  const secrets = {}, vars = {};
  const confirm = ($("p-form").querySelector("[data-confirm]") || {}).value || "";
  for (const i of $("p-form").querySelectorAll("[data-secret]")) if (i.value) secrets[i.dataset.secret] = i.value;
  for (const i of $("p-form").querySelectorAll("[data-var]")) if (i.value) vars[i.dataset.var] = i.value;
  const options = {};
  if (action === "install") for (const i of $("p-form").querySelectorAll("[data-option]")) options[i.dataset.option] = i.value;
  const trial = action === "install" ? ($("trial") || {}).value || "" : "";
  const trial_purge = !!trial && !!($("trial-purge") || {}).checked;
  $("p-form").hidden = true;
  const custom = action === "install" && S.preCustom[a.id] ? S.preCustom[a.id] : null;
  const unidades = action === "install" && S.preUnit[a.id] ? S.preUnit[a.id] : null;
  const purge = action === "remove" && !!($("p-form").querySelector("[data-purge]") || {}).checked;
  const iniciar = () => api("/api/run", { app: a.id, action, secrets, vars, file, confirm,
                                       ...(trial ? { trial, trial_purge } : {}), ...(custom ? { custom } : {}),
                                       ...(unidades ? { custom_units: unidades, ack: !!S.preUnitAck[a.id] } : {}),
                                       ...(purge ? { purge: true } : {}), ...(Object.keys(options).length ? { options } : {}) });
  await (action === "install" ? installFlow(a, iniciar) : follow(iniciar));
  if (custom) delete S.preCustom[a.id];
  if (unidades) { delete S.preUnit[a.id]; delete S.preUnitAck[a.id]; }
  if (action === "backup" || action === "restore") showBackups(a);
}

// Updating is one click: it runs right away, with the release notes of what it
// brings shown above the output while it works.
// The services an install of `a` takes along: the owners of the networks it
// needs that are not installed, theirs first.
function needs(a, vistos = new Set()) {
  const saida = [];
  for (const id of a.requires || []) {
    const dono = S.apps.find((x) => x.id === id);
    if (!dono || vistos.has(id)) continue;
    vistos.add(id);
    saida.push(...needs(dono, vistos), dono);
  }
  return saida;
}

// What the terminal would have asked for one service: `manual` secrets and unset [vars]. The manifest's `ask`
// says how: a label, a hint, the kind of input and its limits (the browser checks them; the server checks again).
const askText = (v) => (v && typeof v === "object" ? (v[S.lang] || v.en || "") : v || "");
function askInput(id, nome, f, base) {
  const tipo = { password: "password", email: "email", number: "number", url: "url" }[f.type] || (base || "text");
  const num = f.type === "number", at = { id, type: tipo, autocomplete: tipo === "password" ? "new-password" : "off" };
  if (f.placeholder) at.placeholder = askText(f.placeholder);
  if (f.required) at.required = true;
  if (f.min !== undefined) at[num ? "min" : "minlength"] = f.min;
  if (f.max !== undefined) at[num ? "max" : "maxlength"] = f.max;
  if (f.regex) { at.pattern = f.regex; at.title = askText(f.pattern_error) || f.regex; }
  return at;
}
function asksFields(x) {
  const campos = [];
  for (const s of x.asks.secrets) {
    const f = s.field || {};
    campos.push(h("label", { for: `s-${s.secret}` }, askText(f.label) || s.secret));
    campos.push(h("input", { ...askInput(`s-${s.secret}`, s.secret, { ...f, required: f.required && !s.exists }, "password"), "data-secret": s.secret }));
    campos.push(h("p", { class: "help" }, askText(f.hint) ? `${askText(f.hint)} ` : null, plain(s.instruction) + " — " +
                  (s.exists ? t("exists") : t("secretHint"))));
  }
  for (const v of x.asks.vars.filter((y) => !y.set)) {
    const f = v.field || {};
    campos.push(h("label", { for: `v-${v.name}` }, askText(f.label) || v.name));
    campos.push(h("input", { ...askInput(`v-${v.name}`, v.name, f), "data-var": v.name, value: v.default }));
    if (askText(f.hint)) campos.push(h("p", { class: "help" }, askText(f.hint)));
  }
  return campos;
}

// How the service is reached. Choosing applies it at once: the exception is
// saved beside the rule, and the update writes it into the unit.
function accessPicker(a) {
  const atual = a.access.exception || "default";
  const sel = h("select", { "aria-label": t("access") },
    h("option", { value: "default", selected: atual === "default" }, t("followRule")(t("modes")[S.rule] || S.rule)),
    ...["local", "tailnet", "both"].map((m) => h("option", { value: m, selected: atual === m },
      t("modes")[m] + (m === "local" && a.requires_https ? ` ⚠ ${t("httpsNeeded")}` : ""))));
  sel.onchange = () => follow(() => api("/api/run", { app: a.id, action: "access", mode: sel.value }));
  return h("label", { class: "access" }, `${t("access")}: `, sel);
}

async function updateNow(action) {
  const a = current();
  $("p-form").hidden = true;
  if (behind(a).length) showNotes(a);
  else $("p-section").hidden = true;
  const antes = !!($("backup-first") || {}).checked && a.has_data;
  await follow(() => api("/api/run", { app: a.id, action, ...(antes ? { backup_first: true } : {}) }));
  await hintClean();
}

// After an update the old image is still on the disk: say how much, and where to clear it.
async function hintClean() {
  try {
    const r = await api("/api/resources");
    const p = $("p-clean");
    p.hidden = !r.images.length;
    if (r.images.length)
      fill(p, t("cleanHint")(r.images.length, sizeOf(r.reclaimable)), " ",
        h("button", { type: "button", class: "ghost", onclick: openResources }, t("cleanOpen")));
  } catch (e) { /* the hint is a courtesy */ }
}

const sizeOf = (b) => b >= 2 ** 30 ? `${(b / 2 ** 30).toFixed(1)} GB` : `${Math.max(1, Math.round(b / 2 ** 20))} MB`;

// A job shown in its own window: what an update of everything, or a rule applied to all, prints. The job
// runs on the server, so closing the window does not stop it: the chip in the top bar brings it back.
async function jobWindow(titulo, start) {
  $("b-title").textContent = titulo;
  $("b-out").textContent = `${t("working")}\n`;
  $("bulk").showModal();
  try { await watchJob(titulo, (await start()).job); }
  catch (e) { $("b-out").textContent += e.status === 409 ? t("busy") : String(e.message); await load(); }
}

async function watchJob(titulo, job) {
  const eu = (S.watch = Symbol("watch"));          // reopening starts a new loop and ends the old one
  $("b-title").textContent = titulo;
  $("b-out").textContent = "";
  if (!$("bulk").open) $("bulk").showModal();
  const prog = jobProgress($("b-progress"), { onmode: () => escondeLog() });
  // In the terminal view the progress already is the output; without a plan there is no progress, and the log stays.
  const escondeLog = () => { $("b-out").hidden = prog.mode() === "terminal" && !$("b-progress").hidden; };
  prog.reset();
  escondeLog();
  try {
    let next = 0, st;
    do {
      st = await api(`/api/job/${job}?from=${next}`);
      next = st.next;
      if (S.watch !== eu) { prog.reset(); return; }
      if (st.output) { $("b-out").textContent += st.output; $("b-out").scrollTop = $("b-out").scrollHeight; prog.feed(st.output); escondeLog(); }
      if (st.rc === null) await new Promise((r) => setTimeout(r, 700));
    } while (st.rc === null);
    prog.finish(st.rc);
    $("b-out").textContent += `\n${st.rc === 0 ? t("done") : `${t("failed")} (${st.rc}).`}\n`;
    $("b-out").scrollTop = $("b-out").scrollHeight;
  } catch (e) { if (S.watch === eu) $("b-out").textContent += String(e.message); }
  await load();
}

// The chip: shown while something runs on the server, whoever started it and whether or not a window is open.
async function pollJobs() {
  let j = null;
  try { j = (await api("/api/jobs/active")).job; } catch (e) { return; }
  const chip = $("job-chip"), antes = S.activeJob;
  S.activeJob = j ? j.id : null;
  chip.hidden = !j;
  if (j) {
    const titulo = j.app === "_host" ? j.action : `${j.action} · ${j.app}`;
    chip.textContent = `⟳ ${titulo}`;
    chip.onclick = () => watchJob(titulo, j.id);
  } else if (antes) await load();
}

async function openSettings() {
  $("settings").showModal();
  await renderSettings();
}

async function renderSettings() {
  $("s-title").textContent = t("settings");
  $("s-out").hidden = true;
  let c;
  try { c = await api("/api/settings"); }
  catch (e) { return fill($("s-body"), h("p", { class: "bad" }, String(e.message))); }
  let escolhido = c.access;
  const radios = c.modes.map((m) => h("label", { class: "check" },
    h("input", { type: "radio", name: "access", value: m, checked: m === c.access, onchange: () => { escolhido = m; } }),
    ` ${t("modes")[m] || m} — ${t("accessDesc")[m]}`));
  const rodar = async (aplicar) => {
    const pre = $("s-out");
    pre.hidden = false;
    pre.textContent = `${t("working")}\n`;
    try {
      const { job } = await api("/api/settings", { access: escolhido, ...(aplicar ? { apply: true } : {}) });
      let next = 0, st;
      do {
        await new Promise((r) => setTimeout(r, 700));
        st = await api(`/api/job/${job}?from=${next}`);
        next = st.next;
        if (st.output) pre.textContent += st.output;
      } while (st.rc === null);
      pre.textContent += `\n${st.rc === 0 ? t("ruleSaved") : `${t("failed")} (${st.rc}).`}\n`;
    } catch (e) { pre.textContent += e.status === 409 ? t("busy") : String(e.message); }
    const texto = pre.textContent;
    await renderSettings();
    $("s-out").hidden = false;
    $("s-out").textContent = texto;
    await load();
  };
  fill($("s-body"),
    h("section", {}, h("h3", {}, t("accessRule")),
      ...radios, c.default ? h("p", { class: "muted" }, t("ruleDefault")) : null,
      c.drift.length ? h("p", { class: "note" }, t("ruleDrift")(c.drift.length, c.drift.slice(0, 6).join(", "))) : null,
      h("div", { class: "row" },
        h("button", { type: "button", onclick: () => rodar(false) }, t("saveRule")),
        h("button", { type: "button", class: "ghost", onclick: () => rodar(true) }, t("applyRule")))),
    await networkSection(),
    await appearanceSection(),
    await alertsSection(),
    podmanSection(),
    await powerSection(),
    h("section", {}, h("p", { class: "muted" }, c.tailnet ? t("tailnetOn") : t("tailnetOff"))));
}

// Restart or shut down the machine: each button asks once more, and a restart waits for the panel to answer again.
function podmanSection() {
  if (!S.podman) return null;
  return h("section", {}, h("h3", {}, t("podmanTitle")), h("p", { class: "muted" }, t("podmanLine")(S.podman)),
    S.podmanOutdated ? h("p", { class: "note" }, t("podmanLate")(S.podman, S.podmanRec)) : h("p", { class: "muted" }, t("podmanOk")(S.podmanRec)));
}

async function powerSection() {
  const msg = h("p", { class: "muted" }), linha = h("div", { class: "row" }), agenda = h("div", { class: "row" }), quando = h("p", { class: "muted" });
  const botoes = () => {
    fill(linha,
      h("button", { type: "button", class: "ghost", onclick: () => pergunta("reboot") }, t("powerReboot")),
      h("button", { type: "button", class: "ghost", onclick: () => pergunta("poweroff") }, t("powerOff")));
  };
  const pergunta = (acao) => fill(linha,
    h("button", { type: "button", class: "danger", onclick: () => fazer(acao) }, `${t("powerSure")}: ${t(acao === "reboot" ? "powerReboot" : "powerOff")}`),
    h("button", { type: "button", class: "ghost", onclick: botoes }, t("powerCancel")));
  const fazer = async (acao) => {
    try { await api("/api/power", { action: acao }); }
    catch (e) { msg.textContent = e.status === 409 ? t("busy") : String(e.message); msg.className = "bad"; return botoes(); }
    fill(linha, agenda);
    msg.className = "muted";
    if (acao === "poweroff") { msg.textContent = t("powerOffDone"); return; }
    msg.textContent = t("powerRebooting");
    let caiu = false;                       // reload once it has gone away and come back
    const olhar = async () => {
      try { await api("/api/host"); if (caiu) return location.reload(); } catch (e) { caiu = true; }
      setTimeout(olhar, 4000);
    };
    setTimeout(olhar, 4000);
  };
  // Scheduled: what, and when (a delay, or the next time of day); one at a time, cancellable.
  const mostra = (ag) => {
    if (!ag) { fill(quando); return; }
    const hora = new Date(ag.at * 1000).toLocaleString(S.lang === "pt" ? "pt-BR" : "en-GB", { weekday: "short", hour: "2-digit", minute: "2-digit" });
    fill(quando, t("powerScheduled")(ag.action, hora), " ",
      h("button", { type: "button", class: "ghost", onclick: async () => { await api("/api/power", { action: "cancel" }); mostra(null); } }, t("powerUnschedule")));
  };
  const oque = h("select", { "aria-label": t("powerAction") },
    h("option", { value: "reboot" }, t("powerReboot")), h("option", { value: "poweroff" }, t("powerOff")));
  const espera = h("select", { "aria-label": t("powerLater") },
    ...["15", "60", "240", "at"].map((k) => h("option", { value: k }, t("powerWhen")[k])));
  const hora = h("input", { type: "time", value: "03:30", "aria-label": t("powerWhen").at });
  hora.hidden = true;
  espera.onchange = () => { hora.hidden = espera.value !== "at"; };
  fill(agenda, oque, espera, hora, h("button", { type: "button", onclick: async () => {
    const corpo = { action: oque.value, ...(espera.value === "at" ? { at: hora.value } : { minutes: Number(espera.value) }) };
    try { mostra((await api("/api/power", corpo)).scheduled); msg.textContent = ""; }
    catch (e) { msg.textContent = String(e.message); msg.className = "bad"; }
  } }, t("powerSchedule")));
  botoes();
  try { mostra((await api("/api/power")).scheduled); } catch (e) { /* no schedule shown */ }
  return h("section", {}, h("h3", {}, t("power")), h("p", { class: "muted" }, t("powerDesc")), linha, agenda, quando, msg);
}

// Alerts to an ntfy topic: opt-in; the token is write-only (the server never sends it back).
async function alertsSection() {
  let r;
  try { r = await api("/api/alerts"); } catch (e) { return null; }
  const c = r.config, msg = h("p", { class: "muted" });
  const caixa = (marcada) => h("input", { type: "checkbox", checked: marcada });
  const entrada = (tipo, valor, extra = {}) => h("input", { type: tipo, value: valor ?? "", autocomplete: "off", ...extra });
  const on = caixa(c.enabled), server = entrada("text", c.server), topic = entrada("text", c.topic);
  const token = entrada("password", "", { placeholder: c.has_token ? t("alertTokenSet") : "" });
  const cool = entrada("number", c.cooldown_hours, { min: 1, max: 168 }), disk = entrada("number", c.disk_percent, { min: 50, max: 99 });
  const kinds = Object.fromEntries(r.kinds.map((k) => [k, caixa(c.kinds[k])]));
  const campo = (rotulo, el) => h("label", { class: "field" }, `${rotulo} `, el);
  const corpo = () => ({
    enabled: on.checked, server: server.value.trim(), topic: topic.value.trim(),
    cooldown_hours: Number(cool.value), disk_percent: Number(disk.value),
    kinds: Object.fromEntries(r.kinds.map((k) => [k, kinds[k].checked])),
    ...(token.value ? { token: token.value } : {}),
  });
  const guardar = async () => {
    try { await api("/api/alerts", corpo()); msg.textContent = t("alertSaved"); msg.className = "muted"; return true; }
    catch (e) { msg.textContent = String(e.message); msg.className = "bad"; return false; }
  };
  const testar = async () => {
    if (!(await guardar())) return;
    try { await api("/api/alerts/test", {}); msg.textContent = t("alertTested"); msg.className = "muted"; }
    catch (e) { msg.textContent = String(e.message); msg.className = "bad"; }
  };
  return h("section", {}, h("h3", {}, t("alerts")), h("p", { class: "muted" }, t("alertsDesc")),
    h("label", { class: "check" }, on, ` ${t("alertsOn")}`),
    campo(t("alertServer"), server), campo(t("alertTopic"), topic), campo(t("alertToken"), token),
    campo(t("alertCooldown"), cool), campo(t("alertDisk"), disk),
    ...r.kinds.map((k) => h("label", { class: "check" }, kinds[k], ` ${t("alertKinds")[k]}`)),
    h("div", { class: "row" }, h("button", { type: "button", onclick: guardar }, t("alertSave")),
      h("button", { type: "button", class: "ghost", onclick: testar }, t("alertTest"))), msg);
}

async function openResources() {
  $("resources").showModal();
  await renderResources();
}

async function renderResources() {
  $("r-title").textContent = t("resources");
  $("r-out").hidden = true;
  fill($("r-body"), h("p", { class: "muted" }, t("resLoading")));
  let r;
  try { r = await api("/api/resources"); }
  catch (e) { fill($("r-body"), h("p", { class: "bad" }, String(e.message))); return; }
  const secao = (kind, titulo, itens, nota, linhas) => {
    let palavra = null, pedido = false;
    const botao = h("button", { type: "button", class: "danger", onclick: () => {
      if (!pedido) {
        pedido = true;
        botao.textContent = t("resSure");
        return;
      }
      pruneRun(kind, palavra ? palavra.value : "");
    } }, t("resRemove"));
    if (kind === "volumes" && itens.length)
      palavra = h("input", { type: "text", autocomplete: "off", "aria-label": "volumes" });
    return h("section", {},
      h("h3", {}, `${titulo} (${itens.length})`),
      itens.length ? h("div", {},
        nota ? h("p", { class: "muted" }, nota) : null,
        h("table", { class: "hist" }, ...linhas),
        kind === "volumes" ? h("p", { class: "note" }, t("resVolumesWarn"), " ", palavra) : null,
        botao) : h("p", { class: "muted" }, t("resNone")));
  };
  const img = r.images.slice(0, 20).map((i) => h("tr", {}, h("td", {}, i.name), h("td", {}, sizeOf(i.size))));
  if (r.images.length > 20) img.push(h("tr", {}, h("td", { colspan: "2", class: "muted" }, `+${r.images.length - 20}`)));
  fill($("r-body"),
    secao("images", t("resImages"), r.images, t("resImagesNote")(r.images.length, sizeOf(r.reclaimable)), img),
    secao("networks", t("resNetworks"), r.networks, null, r.networks.map((n) => h("tr", {}, h("td", {}, n.name)))),
    secao("volumes", t("resVolumes"), r.volumes, null, r.volumes.map((v) => h("tr", {}, h("td", {}, v.name)))),
    usageSection(), imagesSection());
}

// Every image on the disk (not only the unused ones): who uses it, when it was built, what it says about itself.
function imagesSection() {
  const corpo = h("div", {}, h("p", { class: "muted" }, t("resUsageLoading")));
  const nomeApp = (id) => (S.apps.find((a) => a.id === id) || {}).name || id;
  const abrir = new Set();
  const carregar = async () => {
    let r;
    try { r = await api("/api/images"); } catch (e) { fill(corpo, h("p", { class: "bad" }, String(e.message))); return; }
    const detalhe = async (im, cel) => {
      const rot = im.labels || {};
      const linhas = Object.entries(rot).map(([k, v]) => h("tr", {}, h("th", {}, k), h("td", {}, v)));
      fill(cel, h("table", { class: "hist kv" }, h("tr", {}, h("th", {}, "id"), h("td", {}, im.id)), ...linhas), h("p", { class: "muted" }, t("resUsageLoading")));
      try {
        const hs = await api(`/api/images/history?id=${im.id}`);
        fill(cel, h("table", { class: "hist kv" }, h("tr", {}, h("th", {}, "id"), h("td", {}, im.id)), ...linhas),
          h("h4", {}, t("imgHistory")), h("table", { class: "hist" }, ...hs.layers.map((c) => h("tr", {}, h("td", { class: "muted" }, fsTime(c.created)), h("td", {}, h("code", {}, c.by || "—")), h("td", { class: "num" }, c.size ? bytes(c.size) : "")))));
      } catch (e) { fill(cel, h("p", { class: "bad" }, String(e.message))); }
    };
    const linhas = r.images.flatMap((im) => {
      const cel = h("td", { colspan: "6" });
      const detalhes = h("tr", { hidden: !abrir.has(im.id) }, cel);
      let pediu = false;
      const apagar = im.removable ? h("button", { type: "button", class: "ghost force", onclick: async () => {
        if (!pediu) { pediu = true; apagar.textContent = t("imgSure"); return; }
        apagar.textContent = t("imgRemoving");
        await jobWindow(t("imgRemove"), () => api("/api/images/rm", { id: im.id }));
        carregar();
      } }, t("imgRemove")) : null;
      const estado = im.removable ? t("imgFree") : im.in_use ? t("imgInUse") : t("imgWanted");
      const quem = [...new Set(im.used_by.map((u) => (u.app ? nomeApp(u.app) : u.container)))];
      return [h("tr", {},
        h("td", {}, im.names.map((n) => h("div", {}, n))), h("td", { class: "num" }, bytes(im.size)),
        h("td", {}, quem.length ? quem.join(", ") : h("span", { class: "muted" }, `${t("imgNoUse")} · ${estado}`)),
        h("td", { class: "num" }, (im.created || "").slice(0, 10)), h("td", {}, [im.labels.version, im.labels.revision && im.labels.revision.slice(0, 8)].filter(Boolean).join(" · ")),
        h("td", {}, h("button", { type: "button", class: "ghost", onclick: () => { detalhes.hidden = !detalhes.hidden; if (!detalhes.hidden) { abrir.add(im.id); detalhe(im, cel); } else abrir.delete(im.id); } }, t("imgDetails")), apagar)),
        detalhes];
    });
    fill(corpo, r.images.length ? h("table", { class: "hist imgs" }, h("tr", {}, h("th", {}, t("imgName")), h("th", { class: "num" }, t("fColSize")), h("th", {}, t("imgUsedBy")),
      h("th", { class: "num" }, t("imgBuilt")), h("th", {}, t("imgVersion")), h("th", {})), ...linhas) : h("p", { class: "muted" }, t("imgNone")));
  };
  carregar();
  return h("section", {}, h("h3", {}, t("imgTitle")), h("p", { class: "muted" }, t("imgNote")), corpo);
}

// What each app's data takes on disk: asked after the rest of the page (walking a library is slow).
function usageSection() {
  const corpo = h("div", {}, h("p", { class: "muted" }, t("resUsageLoading")));
  const carregar = async (refresh) => {
    fill(corpo, h("p", { class: "muted" }, t("resUsageLoading")));
    let u;
    try { u = await api(`/api/usage${refresh ? "?refresh=1" : ""}`); }
    catch (e) { fill(corpo, h("p", { class: "bad" }, String(e.message))); return; }
    const nome = (id) => (S.apps.find((a) => a.id === id) || {}).name || id;
    const total = u.apps.reduce((n, x) => n + x.bytes, 0);
    fill(corpo, u.apps.length ? h("table", { class: "hist" },
      ...u.apps.map((x) => h("tr", {}, h("td", {}, nome(x.app)), h("td", {}, bytes(x.bytes)))),
      h("tr", {}, h("td", {}, h("b", {}, t("resUsageTotal"))), h("td", {}, h("b", {}, bytes(total))))) : h("p", { class: "muted" }, t("resUsageNone")));
  };
  carregar(false);
  return h("section", {}, h("h3", {}, t("resUsage")), h("p", { class: "muted" }, t("resUsageNote")), corpo,
    h("button", { type: "button", class: "ghost", onclick: () => carregar(true) }, t("resUsageRefresh")));
}

async function pruneRun(kind, confirm) {
  const pre = $("r-out");
  pre.hidden = false;
  pre.textContent = `${t("resWorking")}\n`;
  try {
    const { job } = await api("/api/prune", { kind, confirm });
    let next = 0, st;
    do {
      await new Promise((r) => setTimeout(r, 700));
      st = await api(`/api/job/${job}?from=${next}`);
      next = st.next;
      if (st.output) pre.textContent += st.output;
    } while (st.rc === null);
    pre.textContent += `\n${st.rc === 0 ? t("done") : `${t("failed")} (${st.rc}).`}\n`;
  } catch (e) { pre.textContent += e.status === 409 ? t("busy") : String(e.message); }
  const texto = pre.textContent;
  await renderResources();
  pre.hidden = false;
  pre.textContent = texto;
  $("p-clean").hidden = true;
}

// Kill the container at once, then stop or restart the unit: asked twice, since what was not written is lost.
function forceButton(unit, verbo, rotulo) {
  let pediu = false;
  const b = h("button", { type: "button", class: "ghost force", title: t("forceHint"), onclick: () => {
    if (!pediu) { pediu = true; b.textContent = t("forceSure"); return; }
    unitVerb(unit, verbo);
  } }, t(rotulo));
  return b;
}

const fsTime = (iso) => (iso ? new Date(iso).toLocaleString(S.lang === "pt" ? "pt-BR" : "en-GB") : "—");

// Health: the status, the probe's own settings and what the last runs printed (the answer to "why is it unhealthy").
async function showHealth(unit, resultado = null) {
  if (!resultado) section(h("p", { class: "muted" }, t("checking")));
  let d;
  try { d = await api(`/api/health?unit=${encodeURIComponent(unit)}`); }
  catch (e) { return section(h("p", { class: "bad" }, String(e.message))); }
  const msg = h("p", { class: "muted" }, resultado ? resultado.texto : "");
  if (resultado) msg.className = resultado.rc === 0 ? "ok" : "bad";
  const cfg = d.config || {};
  const rodar = h("button", { type: "button", disabled: !d.running, onclick: async () => {
    rodar.textContent = t("hRunning");
    try {
      const r = await api("/api/health/run", { unit });
      return showHealth(unit, { rc: r.rc, texto: `${t("hResult")(r.rc)} ${r.output || ""}`.trim() });
    } catch (e) { msg.textContent = String(e.message); msg.className = "bad"; rodar.textContent = t("hRun"); }
  } }, t("hRun"));
  const linhas = (d.runs || []).map((r) => h("tr", {}, h("td", {}, fsTime(r.start)), h("td", { class: r.exit === 0 ? "ok" : "bad" }, String(r.exit)), h("td", {}, h("pre", { class: "mini" }, r.output || "—"))));
  const ok = d.status === "healthy" ? "ok" : d.status === "unhealthy" ? "bad" : "muted";
  section(h("h3", {}, `${unit} · ${t("hTab")}`),
    h("p", {}, h("span", { class: `badge ${ok}` }, t("hStatus")[d.status] || d.status), d.streak ? ` ${t("hStreak")(d.streak)}` : "", !d.running ? ` · ${t("hNotRunning")}` : ""),
    cfg.test ? h("p", { class: "muted" }, `${t("hEvery")} ${cfg.interval}s · ${t("hTimeout")} ${cfg.timeout}s · ${cfg.retries} ${t("hRetries")} · ${t("hStartPeriod")} ${cfg.start_period || 0}s`) : null,
    cfg.test ? h("p", {}, h("b", {}, `${t("hCommand")}: `), h("code", {}, cfg.test)) : null,
    cfg.test ? h("p", { class: "muted" }, `${t("hOnFail")}: ${cfg.on_failure || t("hOnFailNone")}`) : null,
    cfg.test ? h("div", { class: "row" }, rodar) : null, msg,
    linhas.length ? h("div", {}, h("h4", {}, t("hRuns")), h("table", { class: "hist" }, h("tr", {}, h("th", {}, t("hStartedAt")), h("th", {}, t("hExit")), h("th", {}, t("hOutput"))), ...linhas))
      : h("p", { class: "muted" }, t("hNoRuns")));
}

// What really runs: the container as Podman has it, variables masked until asked for.
async function showRuntime(unit, reveal = false) {
  section(h("p", { class: "muted" }, t("checking")));
  let d;
  try { d = await api(`/api/runtime?unit=${encodeURIComponent(unit)}${reveal ? "&reveal=1" : ""}`); }
  catch (e) { return section(h("p", { class: "bad" }, e.status === 404 ? t("hNotRunning") : String(e.message))); }
  const linha = (rotulo, v) => (v === null || v === undefined || v === "" ? null : h("tr", {}, h("th", {}, rotulo), h("td", {}, String(v))));
  const L = d.limits || {};
  section(h("h3", {}, `${unit} · ${t("rtTab")}`), h("p", { class: "muted" }, t("rtIntro")),
    h("table", { class: "hist kv" },
      linha(t("rtImage"), d.image), linha(t("rtDigest"), d.digest), linha(t("rtCommand"), d.command), linha(t("rtUser"), d.user), linha(t("rtWorkdir"), d.workdir),
      linha(t("rtCreated"), fsTime(d.created)), linha(t("rtStarted"), fsTime(d.started)), linha(t("rtRestarts"), d.restarts)),
    h("h4", {}, t("rtNetworks")),
    d.networks.length ? h("table", { class: "hist" }, ...d.networks.map((n) => h("tr", {}, h("td", {}, n.name), h("td", {}, n.ip || "—"), h("td", { class: "muted" }, (n.aliases || []).join(", ")))))
      : h("p", { class: "muted" }, "—"),
    h("h4", {}, t("rtPorts")),
    d.ports.length ? h("table", { class: "hist" }, ...d.ports.map((p) => h("tr", {}, h("td", {}, `${p.host_ip}:${p.host}`), h("td", {}, `→ ${p.container}/${p.proto}`)))) : h("p", { class: "muted" }, t("rtNoPorts")),
    h("h4", {}, t("rtMounts")),
    d.mounts.length ? h("table", { class: "hist" }, ...d.mounts.map((m) => h("tr", {}, h("td", {}, m.source || "—"), h("td", {}, `→ ${m.dest}`), h("td", { class: m.rw ? "" : "muted" }, m.rw ? t("rtRW") : t("rtRO"))))) : h("p", { class: "muted" }, "—"),
    h("h4", {}, t("rtLimits")),
    h("table", { class: "hist kv" },
      linha(t("rtReadOnly"), L.read_only ? "✓" : null), linha(t("rtPids"), L.pids), linha(t("rtMemory"), L.memory ? bytes(L.memory) : null),
      linha(t("rtCapsDrop"), (L.cap_drop || []).join(", ")), linha(t("rtCapsAdd"), (L.cap_add || []).join(", ")), linha(t("rtSecurity"), (L.security || []).join(", "))),
    h("h4", {}, t("rtEnv")), h("p", { class: "muted" }, t("rtRevealNote")),
    d.env.length ? h("table", { class: "hist" }, ...d.env.map((e) => h("tr", {}, h("td", {}, e.key), h("td", { class: "muted" }, e.value), h("td", {}, e.secret ? h("span", { class: "badge warn" }, t("rtSecret")) : null)))) : h("p", { class: "muted" }, "—"),
    h("button", { type: "button", class: "ghost", onclick: () => showRuntime(unit, !d.revealed) }, d.revealed ? t("rtHide") : t("rtShow")));
}

async function unitVerb(unit, verb) {
  $("p-form").hidden = true;
  await follow(() => api("/api/unit", { unit, verb }));
}

function showInstance(a) {
  const nome = h("input", { type: "text", placeholder: t("instanceName"), autocomplete: "off", "aria-label": t("instanceName") });
  const criar = async () => {
    const v = nome.value.trim();
    if (!v) return;
    await follow(() => api("/api/run", { app: a.id, action: "install", instance: v }));
  };
  section(h("h3", {}, t("newInstance")), h("div", { class: "row" }, nome,
    h("button", { type: "button", onclick: criar }, t("instanceCreate"))));
}

// -- the progress of a job: the plan, which step is under way and for how long ---------------------------------
// qh prints its plan (`  -> step`), then `[n/N] step` just before it runs each one. This reads that as it arrives and draws the
// steps (done, under way with a clock, waiting, failed) and a bar, so an install or an update is not a spinner and a log.
const STEP_RE = /^\[(\d+)\/(\d+)\] (.+)$/, PLAN_RE = /^ {2}-> (.+)$/;

function stepLabel(desc) {
  const casa = (x) => x.replace(/^.*\/\.config\/containers\//, "~/.config/containers/");
  let m;
  if (/^mkdir -p .*\/volumes\//.test(desc)) return t("stMkdirData");
  if (/^mkdir -p .*\/containers\/systemd/.test(desc)) return t("stMkdirUnits");
  if (/^mkdir -p /.test(desc)) return t("stMkdir");
  if (/^cp .*\.container /.test(desc)) return t("stCopyUnit");
  if (/^cp .*(\.env|\.example)/.test(desc)) return t("stCopyEnv");
  if (/^podman secret create/.test(desc)) return t("stSecret");
  if (/^podman unshare chown/.test(desc)) return t("stChown");
  if (/^systemctl --user daemon-reload/.test(desc)) return t("stReload");
  if ((m = /^systemctl --user restart (\S+)/.exec(desc))) return t("stRestart")(m[1]);
  if ((m = /^systemctl --user start (\S+)/.exec(desc))) return t("stStart")(m[1]);
  if ((m = /^systemctl --user (?:stop|mask --now) (\S+)/.exec(desc))) return t("stStop")(m[1]);
  if ((m = /^wait until it is healthy \(up to (\d+)s\)/.exec(desc))) return t("stHealthy")(m[1]);
  if (/^keep the current units/.test(desc)) return t("stKeep");
  if (/^podman pull/.test(desc)) return t("stPull");
  if (/^rm .*\.container/.test(desc)) return t("stRemoveUnit");
  if (/^tar .*(czf|cf)/.test(desc)) return t("stBackup");
  if (/^tar .*x/.test(desc)) return t("stRestore");
  return casa(desc);
}

// Two ways to show it, kept in this browser: the steps with a bar (default), or the terminal, which is the output as it comes.
function jobProgress(host, opcoes = {}) {
  let plano = [], atual = 0, total = 0, falhou = false, fim = null, buf = "", rodando = false, relogio = null, bruto = "", termSujo = false, mostrando = null;
  let modo = !opcoes.janela && localStorage.getItem("qh-progress") === "terminal" ? "terminal" : "steps";   // the install window shows steps and console together
  const inicio = Date.now();
  let passoInicio = inicio, tFim = null;
  const seg = (ms) => { const n = Math.max(0, Math.round(ms / 1000)); return n >= 60 ? `${Math.floor(n / 60)}min ${n % 60}s` : `${n}s`; };
  const tempoEl = h("span", { class: "muted" }), termEl = h("pre", { class: "live-term", tabindex: "0", "aria-label": t("prTerminal") });
  const botao = (m, rotulo) => h("button", { type: "button", class: "seg-btn", "aria-pressed": String(modo === m), onclick: () => muda(m) }, rotulo);
  const corLinha = (l) => (STEP_RE.test(l) ? "step" : /^(FALHOU em:|FAILED at:|!! )/.test(l) ? "fail" : /^ {2}!  /.test(l) ? "warn" : /^ {2}-> |^ {7}[(…]/.test(l) ? "dim" : "");
  const termDesenha = () => {
    const linhas = bruto.replace(/\n$/, "").split("\n");
    fill(termEl, ...linhas.map((l) => h("span", { class: corLinha(l) }, `${l}\n`)), fim === null ? h("span", { class: "cursor" }, "▌") : null);
    termEl.scrollTop = termEl.scrollHeight;
    termSujo = false;
  };
  const muda = (m) => {
    modo = m;
    localStorage.setItem("qh-progress", m);
    if (opcoes.onmode) opcoes.onmode(m);
    desenha(true);
  };
  const cabeca = (estado) => opcoes.janela ? h("div", { class: "pr-head" }, h("b", {}, estado), tempoEl) : h("div", { class: "pr-head" }, h("b", {}, estado),
    h("div", { class: "pr-right" }, tempoEl, h("div", { class: "seg", role: "group", "aria-label": t("prView") }, botao("steps", t("prSteps")), botao("terminal", t("prTerminal")))));
  const desenha = (forcar = false) => {
    host.hidden = !plano.length;
    if (!plano.length) return;
    const feitos = fim === 0 ? total : Math.max(0, atual - 1);
    const pct = total ? Math.round((feitos / total) * 100) : 0;
    const estado = fim === 0 ? t("prDone") : falhou || (fim !== null && fim !== 0) ? t("prFailed") : t("prStep")(Math.min(atual || 1, total), total);
    tempoEl.textContent = `${t("prElapsed")} ${seg((tFim === null ? Date.now() : tFim) - inicio)}`;
    if (modo === "terminal") {
      if (forcar || termSujo || mostrando !== "terminal") {     // not every second: that would undo a scroll up
        fill(host, cabeca(estado), termEl);
        termDesenha();
        mostrando = "terminal";
      }
      return;
    }
    mostrando = "steps";
    const cheio = h("i", {});
    const barra = h("div", { class: "bar" }, cheio);
    cheio.style.width = `${pct}%`;                // through the CSSOM: the CSP forbids a style attribute
    const pctEl = opcoes.janela ? h("span", { class: "pr-pct" }, `${pct}%`) : null;
    fill(host, cabeca(estado), opcoes.janela ? h("div", { class: "bar-row" }, barra, pctEl) : barra,
      h("ol", { class: "pr-steps" }, ...plano.map((d, i) => {
        const n = i + 1;
        const ruim = (falhou || (fim !== null && fim !== 0)) && n === atual;
        const feito = fim === 0 || n < atual;
        const agora = !feito && !ruim && n === atual && fim === null;
        return h("li", { class: `pr-step ${ruim ? "bad" : feito ? "done" : agora ? "now" : "wait"}`, title: d },
          h("span", { class: "pr-ico", "aria-hidden": "true" }, ruim ? "✗" : feito ? "✓" : agora ? "▶" : "○"),
          h("span", { class: "pr-txt" }, stepLabel(d)), agora ? h("span", { class: "muted pr-time" }, ` ${seg(Date.now() - passoInicio)}`) : null);
      })));
  };
  const linha = (l) => {
    let m;
    if ((m = PLAN_RE.exec(l))) {
      if (rodando) { plano = []; atual = 0; total = 0; falhou = false; rodando = false; }   // a second plan: another app of the same job
      plano.push(m[1]);
    } else if ((m = STEP_RE.exec(l))) {
      rodando = true;
      atual = Number(m[1]); total = Number(m[2]); passoInicio = Date.now();
      if (plano.length !== total) plano = Array.from({ length: total }, (_, i) => plano[i] || (i + 1 === atual ? m[3] : `#${i + 1}`));
      else plano[atual - 1] = plano[atual - 1] || m[3];
    } else if (/^(FALHOU em:|FAILED at:)/.test(l)) falhou = true;
    total = Math.max(total, plano.length);
  };
  return {
    feed(texto) {
      bruto = (bruto + texto).slice(-200000); termSujo = true;
      buf += texto;
      const partes = buf.split(/\r?\n/);
      buf = partes.pop();
      partes.forEach(linha);
      if (!relogio && plano.length && fim === null) relogio = setInterval(desenha, 1000);
      desenha();
    },
    finish(rc) {
      if (buf) { linha(buf); buf = ""; }
      fim = rc; tFim = Date.now(); termSujo = true;
      if (rc !== 0 && atual === 0) atual = 1;
      if (relogio) { clearInterval(relogio); relogio = null; }
      desenha(true);
    },
    reset() { plano = []; atual = 0; total = 0; falhou = false; fim = null; tFim = null; buf = ""; bruto = ""; termSujo = false; mostrando = null; rodando = false; if (relogio) { clearInterval(relogio); relogio = null; } host.hidden = true; fill(host); },
    mode: () => modo,
  };
}

// Installing, in a window of its own: the whole bar with its percentage, every step, and the console under them.
// Closing it ("Continue in the background") does not stop the job: it runs on the server, and the chip in the top bar
// brings the progress back.
async function installFlow(a, start) {
  const pronto = $("i-bg");
  $("i-title").textContent = t("installing")(a.name);
  $("i-out").textContent = "";
  $("i-result").textContent = "";
  $("i-open").hidden = true;
  $("i-spin").hidden = false;
  pronto.textContent = t("inBackground");
  const prog = jobProgress($("i-progress"), { janela: true });
  prog.reset();
  $("panel").close();
  $("install").showModal();
  const fim = (rc, msg) => {
    $("i-spin").hidden = true;
    $("i-result").textContent = msg;
    $("i-result").className = rc === 0 ? "ok" : "bad";
    pronto.textContent = t("closeLabel");
  };
  try {
    const { job } = await start();
    let next = 0, st;
    do {
      await new Promise((r) => setTimeout(r, 700));
      st = await api(`/api/job/${job}?from=${next}`);
      next = st.next;
      if (st.output) {
        $("i-out").textContent += st.output; $("i-out").scrollTop = $("i-out").scrollHeight;
        prog.feed(st.output);
        $("i-spin").hidden = !$("i-progress").hidden;
      }
    } while (st.rc === null);
    prog.finish(st.rc);
    fim(st.rc, st.rc === 0 ? t("done") : `${t("failed")} (${st.rc})`);
    await load();
    const b = S.apps.find((x) => x.id === a.id), url = st.rc === 0 && b ? openUrl(b) : null;
    if (url) { $("i-open").href = url; $("i-open").hidden = false; }
  } catch (e) {
    prog.finish(1);
    const msg = e.status === 409 ? t("busy") : String(e.message);
    $("i-out").textContent += msg;
    fim(1, msg);
  }
}

async function follow(start) {
  busy(true);
  setStatus("busy", t("working"));
  $("p-log-title").textContent = t("logTitle");
  out(`${t("working")}\n`);
  const prog = jobProgress($("p-progress"), { onmode: (m) => { $("p-log").open = m !== "terminal"; } });
  prog.reset();
  const dono = S.current;                    // the panel may be closed or reopened on another app meanwhile
  const aqui = () => S.current === dono;
  try {
    const { job } = await start();
    $("p-log").open = prog.mode() !== "terminal";   // the log is open while it runs, unless the terminal view already shows it
    let next = 0, st;
    do {
      await new Promise((r) => setTimeout(r, 700));
      st = await api(`/api/job/${job}?from=${next}`);
      next = st.next;
      if (st.output && aqui()) { out(st.output, true); prog.feed(st.output); }
    } while (st.rc === null);
    if (!aqui()) return;
    prog.finish(st.rc);
    out(`\n${st.rc === 0 ? t("done") : `${t("failed")} (${st.rc}).`}\n`, true);
    setStatus(st.rc === 0 ? "ok" : "bad", st.rc === 0 ? t("done") : `${t("failed")} (${st.rc})`);
    if (st.rc !== 0) $("p-log").open = true;
  } catch (e) {
    if (!aqui()) return;
    prog.finish(1);
    out(e.status === 409 ? t("busy") : String(e.message), true);
    setStatus("bad", e.status === 409 ? t("busy") : String(e.message));
  } finally {
    busy(false);
    await load();
  }
}

// Live logs: the unit's last 200 lines, then `journalctl -f` as Server-Sent Events. The filter is
// applied here, to what has arrived (5000 lines kept), so changing it needs no new request.
const LOG_MAX = 5000;
function closeLogs() {
  if (S.logSource) { S.logSource.close(); S.logSource = null; }
  clearTimeout(S.logTimer);
  S.logTimer = null;          // a cleared timer left set would stop every later repaint
  closeConsole();
}

function showLogs(unit) {
  closeLogs();
  const linhas = [];
  const filtro = h("input", { type: "search", placeholder: t("logFilter"), "aria-label": t("logFilter") });
  const seguir = h("input", { type: "checkbox", checked: true });
  const estado = h("span", { class: "muted" }, t("logConnecting"));
  const area = h("pre", { class: "logs" });
  const pintar = () => {
    const f = filtro.value.trim().toLowerCase();
    const vistas = f ? linhas.filter((l) => l.toLowerCase().includes(f)) : linhas;
    area.textContent = vistas.length ? vistas.join("\n") : (linhas.length ? t("logNoMatch") : "");
    if (seguir.checked) area.scrollTop = area.scrollHeight;
  };
  const agendar = () => { if (!S.logTimer) S.logTimer = setTimeout(() => { S.logTimer = null; pintar(); }, 150); };
  filtro.addEventListener("input", pintar);
  seguir.addEventListener("change", pintar);
  section(h("h3", {}, `${t("logs")} — ${unit}`),
    h("div", { class: "row" }, filtro, h("label", { class: "check" }, seguir, ` ${t("logFollow")}`), estado), area);
  const es = new EventSource(`/api/logs/stream?unit=${encodeURIComponent(unit)}`);
  S.logSource = es;
  es.onopen = () => { estado.textContent = t("logLive"); };
  es.onmessage = (ev) => {
    linhas.push(ev.data);
    if (linhas.length > LOG_MAX) linhas.splice(0, linhas.length - LOG_MAX);
    agendar();
  };
  es.onerror = () => {         // the server ended it (journalctl stopped) or the connection dropped
    estado.textContent = t("logEnded");
    es.close();
    if (S.logSource === es) S.logSource = null;
  };
}

// -- console ------------------------------------------------------------------
// A terminal over a WebSocket, with no library: the pty on the server does the line editing, and
// this keeps the screen. It understands what a shell with TERM=dumb sends — \r, \n, backspace, tab
// — and drops the colour and cursor sequences. Full-screen programs (vim, top) are out of reach.

const ANSI = /\x1b\[[0-9;?]*[ -\/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]/g;
const TERM_LINES = 2000;

function termNew() { return { lines: [""], row: 0, col: 0, pend: "" }; }

function termFeed(term, chunk) {
  let s = term.pend + chunk;
  term.pend = "";
  // An escape sequence cut by the end of a chunk waits for the next one.
  const i = s.lastIndexOf("\x1b");
  if (i >= 0 && i > s.length - 16 && !/^(\x1b\[[0-9;?]*[ -\/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[@-Z\\-_])/.test(s.slice(i))) {
    term.pend = s.slice(i);
    s = s.slice(0, i);
  }
  s = s.replace(ANSI, "");
  const put = (ch) => {
    const l = term.lines[term.row];
    term.lines[term.row] = l.slice(0, term.col).padEnd(term.col, " ") + ch + l.slice(term.col + 1);
    term.col++;
  };
  for (const ch of s) {
    if (ch === "\n") {
      term.row++;
      if (term.row >= term.lines.length) term.lines.push("");
    } else if (ch === "\r") term.col = 0;
    else if (ch === "\b") term.col = Math.max(0, term.col - 1);
    else if (ch === "\t") { do put(" "); while (term.col % 8); }
    else if (ch >= " " && ch !== "\x7f") put(ch);
  }
  if (term.lines.length > TERM_LINES) {
    const cortar = term.lines.length - TERM_LINES;
    term.lines.splice(0, cortar);
    term.row = Math.max(0, term.row - cortar);
  }
  return term;
}

// What a key sends to a terminal, or null when it is not ours (a shortcut of the browser's).
function termKey(ev) {
  const k = ev.key;
  if (ev.ctrlKey && !ev.altKey && !ev.metaKey && k.length === 1 && /[a-z]/i.test(k)) {
    if (k.toLowerCase() === "c" && typeof getSelection === "function" && String(getSelection()).length) return null;   // a copy
    if (k.toLowerCase() === "v") return null;                                                            // a paste
    return String.fromCharCode(k.toUpperCase().charCodeAt(0) - 64);
  }
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return null;
  return { Enter: "\r", Backspace: "\x7f", Tab: "\t", Escape: "\x1b", ArrowUp: "\x1b[A", ArrowDown: "\x1b[B",
           ArrowRight: "\x1b[C", ArrowLeft: "\x1b[D", Home: "\x1b[H", End: "\x1b[F", Delete: "\x1b[3~" }[k]
    ?? (k.length === 1 ? k : null);
}

function closeConsole() {
  if (S.termWs) { try { S.termWs.close(); } catch (e) { /* already gone */ } S.termWs = null; }
  clearTimeout(S.termTimer);
}

function showConsole(unit) {
  closeLogs();
  const term = termNew();
  const tela = h("pre", { class: "term", tabindex: "0", "aria-label": t("console") });
  const estado = h("span", { class: "muted" }, t("logConnecting"));
  const enviar = (d) => { if (S.termWs && S.termWs.readyState === 1) S.termWs.send(JSON.stringify({ t: "in", d })); };
  const pintar = () => {
    S.termTimer = null;
    tela.textContent = term.lines.join("\n");
    tela.scrollTop = tela.scrollHeight;
  };
  tela.addEventListener("keydown", (ev) => {
    const d = termKey(ev);
    if (d === null || d === undefined) return;
    ev.preventDefault();
    enviar(d);
  });
  tela.addEventListener("paste", (ev) => {
    ev.preventDefault();
    enviar(((ev.clipboardData || {}).getData || (() => ""))("text").replace(/\r?\n/g, "\r"));
  });
  const atalho = (rotulo, d) => h("button", { type: "button", class: "ghost", onclick: () => { enviar(d); tela.focus(); } }, rotulo);
  section(h("h3", {}, `${t("console")} — ${unit}`),
    h("div", { class: "row" }, atalho("Ctrl-C", "\x03"), atalho("Ctrl-D", "\x04"), atalho("Tab", "\t"), estado),
    h("p", { class: "help" }, t("consoleHint")), tela);
  const proto = (typeof location !== "undefined" && location.protocol === "https:") ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${(typeof location !== "undefined" && location.host) || ""}/api/shell?unit=${encodeURIComponent(unit)}`);
  S.termWs = ws;
  ws.onopen = () => {
    estado.textContent = t("logLive");
    ws.send(JSON.stringify({ t: "size", c: 100, r: 28 }));
    tela.focus();
  };
  ws.onmessage = (ev) => { termFeed(term, String(ev.data)); if (!S.termTimer) S.termTimer = setTimeout(pintar, 30); };
  ws.onclose = () => { estado.textContent = t("logEnded"); if (S.termWs === ws) S.termWs = null; pintar(); };
  ws.onerror = () => { estado.textContent = t("consoleFailed"); };
}

// -- wiring -----------------------------------------------------------------

$("search").addEventListener("input", (e) => { S.search = e.target.value; renderGrid(); });
$("tab-apps").addEventListener("click", () => setView("apps"));
$("tab-store").addEventListener("click", () => setView("store"));
$("lang").addEventListener("click", () => {
  S.lang = S.lang === "pt" ? "en" : "pt";
  localStorage.setItem("qh-lang", S.lang);
  S.group = null;
  renderChrome();
  load();
});
$("p-close").addEventListener("click", () => $("panel").close());
$("c-close").addEventListener("click", () => $("custom").close());
$("panel").addEventListener("close", closeLogs);
$("history-btn").addEventListener("click", () => openHistory(null));
$("h-close").addEventListener("click", () => $("history").close());
$("resources-btn").addEventListener("click", openResources);
$("files-btn").addEventListener("click", () => openFiles(""));
$("f-close").addEventListener("click", () => $("files").close());
$("files").addEventListener("dragover", (ev) => { ev.preventDefault(); $("files").classList.add("drop"); });
$("files").addEventListener("dragleave", () => $("files").classList.remove("drop"));
$("files").addEventListener("drop", (ev) => {
  ev.preventDefault();
  $("files").classList.remove("drop");
  uploadFiles([...((ev.dataTransfer || {}).files || [])]);
});
$("settings-btn").addEventListener("click", openSettings);
$("s-close").addEventListener("click", () => $("settings").close());
$("b-close").addEventListener("click", () => $("bulk").close());
$("i-close").addEventListener("click", () => $("install").close());
$("i-bg").addEventListener("click", () => $("install").close());
$("r-close").addEventListener("click", () => $("resources").close());
$("recheck").addEventListener("click", () => loadUpdates(true));
renderChrome();
load();
setInterval(pollStats, 10000);

// The host in one line, at the top: load over the CPUs, memory used, hottest sensor, uptime.
// A few file reads on the server; a field the host does not report is simply left out.
const duracao = (seg) => (seg >= 86400 ? `${Math.floor(seg / 86400)} d` : seg >= 3600 ? `${Math.floor(seg / 3600)} h` : `${Math.max(1, Math.floor(seg / 60))} min`);
function hostLine(h) {
  const gb = (b) => (b / 2 ** 30).toFixed(1);
  const up = h.uptime === null ? null : duracao(h.uptime);
  const partes = [
    h.load === null ? null : `${t("hostCpu")} ${Math.round((h.load / h.cpus) * 100)}%`,
    h.mem ? `${t("hostMem")} ${gb(h.mem.used)}/${gb(h.mem.total)} GB` : null,
    h.temp === null ? null : `${h.temp} °C`,
    up ? `${t("hostUp")} ${up}` : null,
  ].filter(Boolean);
  return partes.join(" · ");
}

// -- service widgets -------------------------------------------------------------------------
// Numbers from inside an app (photos in Immich, blocked queries in AdGuard...), read by the server with a
// key typed here and kept there. The tile shows the first two; the panel shows them all.
const compacto = (n) => (n === null || n === undefined ? "—" : Math.abs(n) >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : Math.abs(n) >= 1e4 ? `${Math.round(n / 1e3)}k`
  : Math.abs(n) >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : String(n));
const valorSvc = (x) => (x.kind === "bytes" ? bytes(x.value || 0) : x.kind === "ms" ? `${x.value} ms` : x.kind === "pct" ? `${x.value}%` : compacto(x.value));

function svcLine(a) {
  const ws = (S.svc || {})[a.id] || [];
  const com = ws.find((w) => w.fields && w.fields.length);
  const erro = ws.find((w) => w.error);
  if (!com) return erro ? h("p", { class: "svc-line muted", title: erro.error }, "⚠") : null;
  return h("p", { class: "svc-line" }, ...com.fields.slice(0, 2).flatMap((x, i) => [i ? " · " : null,
    h("span", { class: x.level ? `lv-${x.level}` : null }, h("strong", {}, valorSvc(x)), ` ${t("svcField")[x.key] || x.key}`)]).filter(Boolean));
}

function renderSvc(a) {
  const ws = (S.svc || {})[a.id] || [];
  $("p-svc").hidden = !a.installed || !ws.length;
  fill($("p-svc"), ws.length ? h("h3", {}, t("svcTitle")) : null, ...ws.map((w) => h("div", { class: "svc-block" },
    h("div", { class: "svc-head" }, h("strong", {}, t("svcNames")[w.type] || w.type),
      h("button", { type: "button", class: "ghost", onclick: () => svcForm(a, w) }, t("svcSetup"))),
    w.fields ? h("div", { class: "svc-stats" }, ...w.fields.map((x) => h("div", { class: `svc-stat${x.level ? ` lv-${x.level}` : ""}` },
      h("span", { class: "svc-val" }, valorSvc(x)), h("span", { class: "svc-lbl" }, t("svcField")[x.key] || x.key))))
      : w.error ? h("p", { class: "note" }, w.error)
      : h("p", { class: "muted" }, w.url ? t("svcConnect") : t("svcNoUrl")))));
}

function svcForm(a, w) {
  const rotulo = { key: t("svcKey"), user: t("svcUser"), password: t("svcPassword"), slug: t("svcSlug") };
  const campos = w.auth.map((k) => [k, h("input", { type: k === "key" || k === "password" ? "password" : "text", autocomplete: "off",
    placeholder: w.configured && (k === "key" || k === "password") ? t("svcKeyKept") : "", "aria-label": rotulo[k] })]);
  const url = h("input", { type: "text", autocomplete: "off", placeholder: "https://…", "aria-label": t("svcUrl") });
  const aviso = h("p", { class: "muted" });
  const enviar = async (valores) => {
    try { S.svc = (await api("/api/svc/config", { app: a.id, slot: w.slot, values: valores })).apps; renderSvc(a); renderGrid(); $("p-section").hidden = true; }
    catch (e) { aviso.textContent = String(e.message); }
  };
  section(h("h3", {}, `${t("svcSetup")} · ${t("svcNames")[w.type] || w.type}`),
    h("p", { class: "help" }, t("svcHelp")[w.type] || ""),
    ...campos.map(([k, el]) => h("label", { class: "field" }, rotulo[k], el)),
    h("label", { class: "field" }, t("svcUrl"), url),
    h("p", { class: "help" }, t("svcSecure")),
    h("div", { class: "row" },
      h("button", { type: "button", onclick: () => enviar({ ...Object.fromEntries(campos.map(([k, el]) => [k, el.value])), ...(url.value.trim() ? { url: url.value } : {}) }) }, t("svcSave")),
      w.configured ? h("button", { type: "button", class: "danger", onclick: () => enviar({ clear: true }) }, t("svcForget")) : null),
    aviso);
}

async function pollSvc() {
  if (document.hidden || !S.apps.some((a) => a.installed)) return;
  try {
    S.svc = (await api("/api/svc")).apps;
    if (S.view === "apps") renderGrid();
    const a = S.current && current();
    if (a && $("panel").open) renderSvc(a);
  } catch (e) { /* next turn */ }
}

// -- network: Tailscale, Headscale or none ---------------------------------------------------
// The tailnet is part of the project: one choice here, and `qh --network` does the rest (the host's client,
// the Headscale server, tsdproxy). What needs root on the host is only shown, as commands to copy.
async function networkSection() {
  let n;
  try { n = await api("/api/network"); } catch (e) { return null; }
  let modo = n.mode;
  const aviso = h("p", { class: "muted" });
  const nome = h("input", { type: "text", value: n.tailnet || "", placeholder: "casa", autocomplete: "off", "aria-label": t("netTailnet") });
  const url = h("input", { type: "text", value: n.server_url || "", placeholder: "http://192.168.1.10:8093", autocomplete: "off", "aria-label": t("netServer") });
  const detalhe = h("div", { class: "net-detail" });
  const estado = (ok, txt) => h("li", {}, h("span", { class: `dot ${ok === true ? "ok" : ok === false ? "off" : "warn"}` }), txt);
  const ts = n.tailscale, hs = n.headscale, tsd = n.tsdproxy;
  const lista = h("ul", { class: "net-state" },
    estado(ts.installed && ts.active && ts.backend === "Running", `${t("netTs")}: ${!ts.installed ? t("netNotInstalled") : !ts.active ? t("netNotRunning") : [ts.backend, ts.ip, ts.domain].filter(Boolean).join(" · ")}`),
    estado(hs.active, `${t("netHs")}: ${hs.active ? t("netRunning") : hs.installed ? t("netInstalledOnly") : t("netNotInstalled")}`),
    estado(tsd.active, `${t("netTsd")}: ${tsd.active ? t("netRunning") : tsd.installed ? t("netInstalledOnly") : t("netNotInstalled")}${tsd.authkey || !tsd.installed ? "" : ` · ${t("netNoKey")}`}`));
  const desenha = () => {
    const faltaHost = modo !== "local" && (!ts.installed || !ts.active || !ts.operator);
    const cmds = !ts.installed ? n.commands.install : !ts.active ? n.commands.service : n.commands.operator;
    fill(detalhe, h("p", { class: "muted" }, t("netDesc")[modo]),
      modo === "headscale" ? h("label", { class: "field" }, `${t("netServer")}`, url, h("small", { class: "muted" }, t("netServerHint"))) : null,
      modo !== "local" ? h("label", { class: "field" }, t("netTailnet"), nome, h("small", { class: "muted" }, t("netTailnetHint"))) : null,
      faltaHost ? h("div", { class: "note" }, h("strong", {}, t("netNeed")), h("pre", {}, cmds.join("\n"))) : null);
  };
  const botoes = ["local", "tailscale", "headscale"].map((m) => {
    const b = h("button", { type: "button", "aria-pressed": String(modo === m), onclick: () => {
      modo = m; for (const x of botoes) x.setAttribute("aria-pressed", String(x === b)); desenha(); } }, t("netModes")[m]);
    return b;
  });
  const aplicar = async () => {
    const pre = $("s-out");
    pre.hidden = false; pre.textContent = `${t("working")}\n`;
    if (modo !== "local") pre.textContent += `${t("netNowTs")}\n`;
    try {
      const { job } = await api("/api/network", { mode: modo, tailnet: nome.value.trim(), server_url: url.value.trim() });
      let next = 0, st;
      do {
        await new Promise((r) => setTimeout(r, 900));
        st = await api(`/api/job/${job}?from=${next}`);
        next = st.next;
        if (st.output) pre.textContent += st.output;
      } while (st.rc === null);
      pre.textContent += `\n${st.rc === 0 ? t("netDone") : `${t("failed")} (${st.rc}).`}\n`;
    } catch (e) { pre.textContent += e.status === 409 ? t("busy") : String(e.message); }
    const texto = pre.textContent;
    await renderSettings(); $("s-out").hidden = false; $("s-out").textContent = texto;
    await load();
  };
  desenha();
  return h("section", {}, h("h3", {}, t("netTitle")), h("div", { class: "seg", role: "group", "aria-label": t("netTitle") }, ...botoes),
    detalhe, h("p", { class: "lead-sm" }, t("netState")), lista,
    h("div", { class: "row" }, h("button", { type: "button", onclick: aplicar }, t("netApply"))), aviso);
}

// -- appearance -----------------------------------------------------------------------------
// Theme, accent, card style, density and a background image: kept on the server (/api/ui), applied as
// data attributes on <html> and CSS variables, so the stylesheet does all the drawing.
const ACCENT_SWATCH = { blue: "#2b59ff", orange: "#c2410c", green: "#15803d", teal: "#0f766e", purple: "#7e22ce", pink: "#be185d", red: "#b91c1c", slate: "#334155" };

function applyUi(u) {
  S.ui = u;
  const raiz = document.documentElement;
  raiz.setAttribute("data-theme", u.theme);
  raiz.setAttribute("data-accent", u.accent);
  raiz.setAttribute("data-card", u.card);
  raiz.setAttribute("data-density", u.density);
  raiz.setAttribute("data-isize", u.icon_size || "medium");
  raiz.setAttribute("data-depth", u.depth || "flat");
  document.body.classList.toggle("has-bg", !!u.background);
  const st = document.body.style;
  if (st.setProperty) {
    if (u.background) st.setProperty("--bg-img", `url("/ui/background?v=${u.bg_version}")`);
    st.setProperty("--bg-blur", `${u.bg_blur}px`);
    st.setProperty("--bg-dim", String(u.bg_dim / 100));
  }
}

async function loadUi() {
  try { applyUi(await api("/api/ui")); } catch (e) { /* the defaults in the stylesheet */ }
}

async function saveUi(mudanca, aviso) {
  applyUi({ ...S.ui, ...mudanca });                   // at once: what you pick is what you see
  try { applyUi(await api("/api/ui", mudanca)); if (aviso) aviso.textContent = t("apSaved"); }
  catch (e) { if (aviso) aviso.textContent = String(e.message); }
}

async function appearanceSection() {
  if (!S.ui) await loadUi();
  if (!S.ui) return null;
  const u = S.ui, aviso = h("p", { class: "muted" });
  const segmento = (chave, rotulos) => {
    const botoesSeg = Object.keys(rotulos).map((v) => {
      const b = h("button", { type: "button", "aria-pressed": String(u[chave] === v),
        onclick: async () => { for (const x of botoesSeg) x.setAttribute("aria-pressed", String(x === b)); await saveUi({ [chave]: v }, aviso); } }, rotulos[v]);
      return b;
    });
    return h("div", { class: "seg", role: "group" }, ...botoesSeg);
  };
  const cores = Object.keys(ACCENT_SWATCH).map((k) => {
    const b = h("button", { type: "button", class: "swatch", title: t("apAccents")[k], "aria-label": t("apAccents")[k], "aria-pressed": String(u.accent === k),
      onclick: async () => { for (const x of cores) x.setAttribute("aria-pressed", String(x === b)); await saveUi({ accent: k }, aviso); } });
    b.style.background = ACCENT_SWATCH[k];
    return b;
  });
  const arquivo = h("input", { type: "file", accept: "image/png,image/jpeg,image/webp", "aria-label": t("apBgPick") });
  arquivo.addEventListener("change", async () => {
    const f = arquivo.files && arquivo.files[0];
    if (!f) return;
    try {
      const r = await fetch("/api/ui/background", { method: "POST", body: f, headers: { "X-QH-Store": "1", "Content-Type": "application/octet-stream" } });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      applyUi(d); aviso.textContent = t("apSaved"); renderSettings();
    } catch (e) { aviso.textContent = String(e.message); }
  });
  const deslize = (chave, max) => {
    const el = h("input", { type: "range", min: 0, max, step: 1, value: u[chave] });
    el.value = String(u[chave]);
    el.addEventListener("input", () => applyUi({ ...S.ui, [chave]: Number(el.value) }));
    el.addEventListener("change", () => saveUi({ [chave]: Number(el.value) }, aviso));
    return el;
  };
  return h("section", {}, h("h3", {}, t("appearance")),
    h("div", { class: "ap-grid" },
      h("label", {}, t("apTheme"), segmento("theme", t("apThemes"))),
      h("label", {}, t("apCard"), segmento("card", t("apCards"))),
      h("label", {}, t("apDensity"), segmento("density", t("apDensities"))),
      h("label", {}, t("apIconSize"), segmento("icon_size", t("apIconSizes"))),
      h("label", {}, t("apDepth"), segmento("depth", t("apDepths")))),
    h("p", { class: "lead-sm" }, t("apAccent")), h("div", { class: "swatches" }, ...cores),
    h("p", { class: "lead-sm" }, t("apBg")),
    h("div", { class: "row" }, arquivo,
      u.background ? h("button", { type: "button", class: "ghost", onclick: async () => {
        const r = await fetch("/api/ui/background", { method: "POST", body: "", headers: { "X-QH-Store": "1" } });
        applyUi(await r.json()); renderSettings(); } }, t("apBgRemove")) : null),
    h("p", { class: "help" }, t("apBgHint")),
    u.background ? h("div", { class: "ap-grid" }, h("label", {}, t("apBgBlur"), deslize("bg_blur", 20)), h("label", {}, t("apBgDim"), deslize("bg_dim", 80))) : null,
    aviso);
}

// -- Files: a file manager for the folders of the apps --------------------------------------------
// The path is "app/volume/sub/dir" (or "@NAME" for a folder of the person's own). The server lists, previews, streams
// downloads and uploads, and makes the changes; it refuses anything outside those folders and any link. Selection,
// copy/cut/paste, rename, new folder and delete (asked twice) happen here; a drop of files uploads them.
S.fsel = new Set();
S.fclip = null;          // {mode: "copy"|"move", paths: [...]}
const fsJoin = (a, b) => (a ? `${a}/${b}` : b);
const fsPost = (body) => api("/api/files/op", body);

S.fview = localStorage.getItem("qh-fview") === "grid" ? "grid" : "list";

async function openFiles(path = "") {
  if (!$("files").open) $("files").showModal();
  S.fsel = new Set();
  try { S.floc = (await api("/api/files?path=")).entries; } catch (e) { S.floc = []; }     // the places on the left
  await renderFiles(path);
}

// The icon of an entry: an app's own logo at the top, a folder, or a file by what it is.
function fsIcon(e, noTopo) {
  if (noTopo) {
    const a = S.apps.find((x) => x.id === e.name);
    if (a && a.icon) return iconPlate(a, "sm");
  }
  const tipo = e.type === "dir" ? "dir" : e.type === "link" ? "link" : FS_IMAGES.test(e.name) ? "img" : FS_TEXT.test(e.name) ? "txt" : "file";
  return h("span", { class: `fi ${tipo}`, "aria-hidden": "true" });
}

function fsSide(partes) {
  const atual = partes[0] || "";
  const nomeApp = fsName;
  fill($("f-side"), h("h4", {}, t("fPlaces")),
    h("button", { type: "button", "aria-current": String(!atual), onclick: () => openFiles("") }, h("span", { class: "fi dir", "aria-hidden": "true" }), t("filesRoot")),
    ...(S.floc || []).map((e) => h("button", { type: "button", "aria-current": String(atual === e.name), onclick: () => openFiles(e.name) },
      fsIcon(e, true), nomeApp(e.name))));
}

// Writable below the volume level: "app/volume/..." or "@NAME/...", not in the list of apps or of one app's volumes.
const FS_RO = ["@systemd", "@env"];                      // the units and the .env files: to look at, not to change
const fsCanWrite = (partes) => !FS_RO.includes(partes[0]) && (partes.length >= 2 || (partes.length === 1 && partes[0].startsWith("@")));
const fsName = (id) => (id === "@systemd" ? t("filesUnits") : id === "@env" ? t("filesEnv") : (S.apps.find((a) => a.id === id) || {}).name || id);

async function renderFiles(path, msg = "") {
  S.fpath = path;
  $("f-title").textContent = t("files");
  $("f-view").hidden = true;
  const partes = path.split("/").filter(Boolean);
  const nomeApp = fsName;
  fill($("f-crumb"), h("button", { type: "button", onclick: () => openFiles("") }, t("filesRoot")),
    ...partes.flatMap((p, i) => [h("span", { class: "sep" }, "/"),
      h("button", { type: "button", onclick: () => openFiles(partes.slice(0, i + 1).join("/")) }, i === 0 && (!p.startsWith("@") || FS_RO.includes(p)) ? nomeApp(p) : p)]));
  let r;
  try { r = await api(`/api/files?path=${encodeURIComponent(path)}`); }
  catch (e) { fill($("f-body"), h("p", { class: "bad" }, e.status === 403 ? t("filesDenied") : String(e.message))); fill($("f-bar")); return; }
  const gravavel = fsCanWrite(partes);
  const quais = r.entries.filter((e) => S.fsel.has(e.name));
  const nSel = quais.length;
  const caminhoDe = (e) => fsJoin(path, e.name);
  const refresca = (m = "") => renderFiles(path, m);
  const erro = (e) => refresca(e.status === 409 ? t("fExists") : String(e.message));

  // The bar: what can be done here and with the selection.
  const barra = [];
  const campo = (rotulo, inicial, feito) => {            // an inline question that replaces the bar
    const entrada = h("input", { type: "text", value: inicial, "aria-label": rotulo, autocomplete: "off" });
    const ok = async () => { const v = entrada.value.trim(); if (v) { try { await feito(v); } catch (e) { return erro(e); } } refresca(); };
    entrada.addEventListener("keydown", (ev) => { if (ev.key === "Enter") { ev.preventDefault(); ok(); } else if (ev.key === "Escape") refresca(); });
    fill($("f-bar"), h("label", {}, `${rotulo} `, entrada), h("button", { type: "button", onclick: ok }, t("fOk")),
      h("button", { type: "button", class: "ghost", onclick: () => refresca() }, t("fCancel")));
    return entrada;
  };
  if (gravavel) {
    const escolher = h("input", { type: "file", multiple: true, hidden: true, id: "f-pick" });
    escolher.addEventListener("change", () => uploadFiles([...(escolher.files || [])]));
    barra.push(escolher, h("button", { type: "button", onclick: () => escolher.click() }, t("fUpload")),
      h("button", { type: "button", class: "ghost", onclick: () => campo(t("fName"), "", (v) => fsPost({ op: "mkdir", path, name: v })) }, t("fNewFolder")));
    if (S.fclip)
      barra.push(h("button", { type: "button", class: "ghost", onclick: async () => {
        try { for (const p of S.fclip.paths) await fsPost({ op: S.fclip.mode, path: p, to: path }); if (S.fclip.mode === "move") S.fclip = null; }
        catch (e) { return erro(e); }
        refresca();
      } }, `${t("fPaste")} (${S.fclip.paths.length})`));
  }
  if (nSel) {
    barra.push(h("span", { class: "muted" }, t("fSel")(nSel)));
    if (gravavel) {
      barra.push(h("button", { type: "button", class: "ghost", onclick: () => { S.fclip = { mode: "copy", paths: quais.map(caminhoDe) }; refresca(); } }, t("fCopy")),
        h("button", { type: "button", class: "ghost", onclick: () => { S.fclip = { mode: "move", paths: quais.map(caminhoDe) }; refresca(); } }, t("fCut")));
      if (nSel === 1) barra.push(h("button", { type: "button", class: "ghost", onclick: () => campo(t("fName"), quais[0].name, (v) => fsPost({ op: "rename", path: caminhoDe(quais[0]), name: v })) }, t("fRename")));
      let pediu = false;
      const apagar = h("button", { type: "button", class: "danger", onclick: () => {
        if (!pediu) { pediu = true; apagar.textContent = t("fSure")(nSel); return; }
        (async () => { try { for (const e of quais) await fsPost({ op: "delete", path: caminhoDe(e) }); } catch (e) { return erro(e); } S.fsel = new Set(); refresca(); })();
      } }, t("fDelete"));
      barra.push(apagar);
    }
  }
  if (S.fclip && !gravavel) barra.push(h("span", { class: "muted" }, t("fClip")(S.fclip.paths.length, S.fclip.mode)));
  barra.push(h("button", { type: "button", class: "ghost push", onclick: () => { S.fview = S.fview === "grid" ? "list" : "grid"; localStorage.setItem("qh-fview", S.fview); refresca(); } },
    S.fview === "grid" ? t("fList") : t("fGrid")),
    h("button", { type: "button", class: "ghost", onclick: () => refresca() }, t("fRefresh")));
  fill($("f-bar"), ...barra);

  const todos = h("input", { type: "checkbox", "aria-label": t("fSelectAll"), checked: r.entries.length > 0 && nSel === r.entries.length });
  todos.addEventListener("change", () => { S.fsel = todos.checked ? new Set(r.entries.map((e) => e.name)) : new Set(); refresca(); });
  const topo = !partes.length;
  const caixa = (e) => {
    const c = h("input", { type: "checkbox", "aria-label": e.name, checked: S.fsel.has(e.name) });
    c.addEventListener("change", () => { c.checked ? S.fsel.add(e.name) : S.fsel.delete(e.name); refresca(); });
    return c;
  };
  const nome = (e) => (topo && (!e.name.startsWith("@") || FS_RO.includes(e.name)) ? nomeApp(e.name) : e.name);
  const abrir = (e) => e.type === "dir"
    ? h("button", { type: "button", class: "fname dir", onclick: () => openFiles(fsJoin(path, e.name)) }, fsIcon(e, topo), h("span", { class: "nm" }, nome(e)))
    : e.type === "link"
      ? h("button", { type: "button", class: "fname", disabled: true, title: t("filesLink") }, fsIcon(e), h("span", { class: "nm" }, e.name))
      : h("button", { type: "button", class: "fname", onclick: () => showFile(fsJoin(path, e.name), e, gravavel) }, fsIcon(e), h("span", { class: "nm" }, e.name));
  const dataDe = (e) => (e.mtime ? new Date(e.mtime * 1000).toLocaleDateString(S.lang === "pt" ? "pt-BR" : "en-GB") : "");
  const lista = S.fview === "grid"
    ? h("div", { class: "fgrid" }, ...r.entries.map((e) => h("div", { class: `fcard${S.fsel.has(e.name) ? " sel" : ""}` },
        gravavel ? h("span", { class: "chk" }, caixa(e)) : null, abrir(e))))
    : h("table", { class: "hist" },
        h("tr", {}, gravavel ? h("th", { class: "chk" }, todos) : null, h("th", {}, t("fColName")), h("th", { class: "num" }, t("fColSize")), h("th", { class: "num" }, t("fColDate"))),
        ...r.entries.map((e) => h("tr", {}, gravavel ? h("td", { class: "chk" }, caixa(e)) : null, h("td", {}, abrir(e)),
          h("td", { class: "num" }, e.size === null || e.size === undefined ? "" : bytes(e.size)), h("td", { class: "num" }, dataDe(e)))));
  fsSide(partes);
  fill($("f-body"),
    h("p", { class: "muted" }, gravavel ? t("filesNote") : FS_RO.includes(partes[0]) ? t("filesRO") : t("fReadHere")),
    msg ? h("p", { class: "note" }, msg) : null,
    r.entries.length ? lista : h("p", { class: "muted" }, partes.length ? t("filesEmpty") : t("filesNone")),
    r.truncated ? h("p", { class: "note" }, t("filesMore")) : null);
}

// Files sent one after the other into the folder on screen; a name already there is kept, the new one gets (1).
async function uploadFiles(arquivos, path = S.fpath) {
  const partes = (path || "").split("/").filter(Boolean);
  if (!arquivos.length || !fsCanWrite(partes)) return;
  let feitos = 0;
  for (const [i, f] of arquivos.entries()) {
    $("f-state").textContent = t("fSending")(i + 1, arquivos.length, f.name);
    try {
      const r = await fetch(`/api/files/upload?path=${encodeURIComponent(path)}&name=${encodeURIComponent(f.name)}`,
        { method: "POST", headers: { "X-QH-Store": "1" }, body: f });
      if (!r.ok) throw new Error(((await r.json().catch(() => ({}))).error) || r.status);
      feitos += 1;
    } catch (e) { $("f-state").textContent = `${f.name}: ${e.message}`; return renderFiles(path, `${f.name}: ${e.message}`); }
  }
  $("f-state").textContent = "";
  await renderFiles(path, t("fSent")(feitos));
}

const FS_IMAGES = /\.(png|jpe?g|gif|webp|bmp)$/i;
const FS_TEXT = /\.(txt|md|json|ya?ml|toml|ini|conf|cfg|env|log|csv|xml|html?|css|js|py|sh|sql|container|network|service)$/i;
async function showFile(path, e, gravavel) {
  const pasta = path.split("/").slice(0, -1).join("/");
  const url = `/api/files/download?path=${encodeURIComponent(path)}`;
  const baixar = h("a", { class: "btn", href: url, download: e.name }, t("filesDownload"));
  const voltar = h("button", { type: "button", class: "ghost", onclick: () => renderFiles(pasta) }, t("filesBack"));
  fill($("f-bar"));
  fsSide(path.split("/").filter(Boolean));
  const corpo = [h("h3", {}, e.name), h("div", { id: "f-actions" }, baixar, voltar), h("p", { class: "muted" }, bytes(e.size || 0))];
  fill($("f-body"), ...corpo);
  const pre = $("f-view");
  if (FS_IMAGES.test(e.name)) {
    pre.hidden = true;
    $("f-body").append(h("img", { class: "fimg", src: `${url}&inline=1`, alt: e.name }));
    return;
  }
  pre.hidden = false;
  pre.textContent = "";
  try {
    const v = await api(`/api/files/preview?path=${encodeURIComponent(path)}`);
    pre.textContent = v.text;
    if (v.truncated) $("f-body").append(h("p", { class: "note" }, t("filesCut")(bytes(v.text.length))));
    else if (gravavel) {                                      // a whole text file can be edited here and saved over itself
      const area = h("textarea", { id: "f-edit", rows: 16, "aria-label": e.name, spellcheck: false });
      area.value = v.text;
      const salvar = h("button", { type: "button", onclick: async () => {
        const r = await fetch(`/api/files/upload?path=${encodeURIComponent(pasta)}&name=${encodeURIComponent(e.name)}&overwrite=1`,
          { method: "POST", headers: { "X-QH-Store": "1" }, body: area.value });
        $("f-state").textContent = r.ok ? t("fSaved") : String(r.status);
      } }, t("fSave"));
      pre.hidden = true;
      $("f-body").append(area, h("div", { id: "f-actions" }, salvar));
    }
  } catch (err) {
    pre.hidden = true;
    $("f-body").append(h("p", { class: "muted" }, err.status === 415 ? t("filesBinary") : err.status === 403 ? t("filesDenied") : String(err.message)));
  }
}

// -- Quick Launch ---------------------------------------------------------------------------
// Start typing anywhere and a search opens over the page: the installed apps first, then the store's.
// Enter takes the highlighted one (open the app, or its page when it is not installed); the last line
// searches the web. No shortcut to learn: any letter starts it, and "/" opens it empty.
const QL = { sel: 0, itens: [] };

function qlResults(q) {
  const termo = q.trim().toLowerCase();
  if (!termo) return [];
  const casa = (a) => `${a.name} ${a.id}`.toLowerCase();
  const nota = (a) => (casa(a).startsWith(termo) ? 0 : casa(a).includes(termo) ? 1 : 2);
  const achados = S.apps.filter((a) => matches(a, termo))
    .sort((x, y) => (y.installed - x.installed) || (nota(x) - nota(y)) || x.name.localeCompare(y.name));
  return achados.slice(0, 8).map((a) => {
    const url = a.installed ? openUrl(a) : null;
    return { app: a, rotulo: a.installed ? (url ? t("qlOpen") : t("qlManage")) : t("qlStore"),
      ir: () => { if (url) window.open(url, "_blank", "noopener"); else { if (!a.installed) setView("store"); openPanel(a.id); } } };
  }).concat([{ web: true, rotulo: t("qlWeb")(q.trim()),
    ir: () => window.open(`https://duckduckgo.com/?q=${encodeURIComponent(q.trim())}`, "_blank", "noopener") }]);
}

function qlRender() {
  const campo = $("ql-input");
  QL.itens = qlResults(campo.value);
  QL.sel = Math.min(QL.sel, Math.max(0, QL.itens.length - 1));
  const lista = QL.itens.map((it, i) => h("li", { role: "option", "aria-selected": String(i === QL.sel), class: it.web ? "ql-web" : null,
    onclick: () => { $("ql").close(); if (it.app) touchRecent(it.app.id); it.ir(); } },
    it.web ? h("span", { class: "ico sm ql-g", "aria-hidden": "true" }, "↗")
      : iconPlate(it.app, "xs"),
    h("span", { class: "ql-name" }, it.web ? it.rotulo : it.app.name,
      it.web ? null : h("small", {}, plain(it.app.description[S.lang] || it.app.description.en))),
    it.web ? null : h("span", { class: "ql-act" }, it.rotulo)));
  fill($("ql-list"), ...(QL.itens.length > 1 || !campo.value.trim() ? lista : [h("li", { class: "ql-none" }, t("qlNone")), ...lista]));
}

function quickLaunch(inicial = "") {
  const campo = $("ql-input");
  campo.placeholder = t("qlPlaceholder");
  campo.value = inicial;
  QL.sel = 0;
  qlRender();
  if (!$("ql").open) $("ql").showModal();
  campo.focus();
}

$("ql-input").addEventListener("input", () => { QL.sel = 0; qlRender(); });
$("ql-input").addEventListener("keydown", (ev) => {
  if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
    ev.preventDefault();
    QL.sel = (QL.sel + (ev.key === "ArrowDown" ? 1 : -1) + QL.itens.length) % Math.max(1, QL.itens.length);
    qlRender();
  } else if (ev.key === "Enter") {
    ev.preventDefault();
    const it = QL.itens[QL.sel];
    if (it) { $("ql").close(); it.ir(); }
  }
});
document.addEventListener("keydown", (ev) => {
  if (ev.ctrlKey || ev.metaKey || ev.altKey || ev.defaultPrevented) return;
  const alvo = ev.target || {};
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(alvo.tagName || "") || alvo.isContentEditable) return;
  if ([...document.querySelectorAll("dialog")].some((d) => d.open)) return;
  if (ev.key === "/") { ev.preventDefault(); quickLaunch(""); }
  else if (ev.key.length === 1 && /\S/.test(ev.key)) { ev.preventDefault(); quickLaunch(ev.key); }
});

const bytes = (n) => n >= 2 ** 40 ? `${(n / 2 ** 40).toFixed(1)} TB` : n >= 2 ** 30 ? `${(n / 2 ** 30).toFixed(1)} GB`
  : n >= 2 ** 20 ? `${(n / 2 ** 20).toFixed(1)} MB` : `${Math.max(0, Math.round(n / 1024))} KB`;

// Server numbers for the home tiles; the rates need two readings, so the second comes soon after the first.
async function pollPerf() {
  if (document.hidden || S.view !== "apps") return;
  try {
    S.hostData = await api("/api/host");
    pushHist(S.hostData);
    renderHome();
  } catch (e) { /* next turn */ }
}

// The navigation starts open and folds to icons; the choice is kept.
document.body.dataset.nav = localStorage.getItem("qh-nav") === "collapsed" ? "collapsed" : "open";
$("nav-toggle").addEventListener("click", () => {
  document.body.dataset.nav = document.body.dataset.nav === "collapsed" ? "open" : "collapsed";
  localStorage.setItem("qh-nav", document.body.dataset.nav);
  renderChrome();
});
loadUi();
setTimeout(pollMonitor, 3000);
setTimeout(pollSvc, 2000);
setInterval(pollSvc, 60000);
setInterval(pollMonitor, 60000);
pollJobs();
setInterval(pollJobs, 3000);
pollPerf().then(() => setTimeout(pollPerf, 1200));
setInterval(pollPerf, 5000);

async function pollHost() {
  try { $("host").textContent = hostLine(await api("/api/host")); } catch (e) { /* the line just stays */ }
}
pollHost();
setInterval(pollHost, 30000);

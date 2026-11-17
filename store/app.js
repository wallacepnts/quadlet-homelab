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
    customize: "Personalizar", customizedBadge: "personalizado", cPorts: "Portas", cVolumes: "Volumes",
    cEnv: "Variáveis de ambiente", cDevices: "Dispositivos", cCaps: "Capabilities extras",
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
    capsHint: "Só as da lista. Para outra, edite a unit à mão.",
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
           customize: "Personalizar", revert: "Reverter", prune: "Limpar" },
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
    customize: "Customize", customizedBadge: "customized", cPorts: "Ports", cVolumes: "Volumes",
    cEnv: "Environment variables", cDevices: "Devices", cCaps: "Extra capabilities",
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
    capsHint: "Only the ones on the list. For another, edit the unit by hand.",
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
           customize: "Customize", revert: "Revert", prune: "Clean up" },
    link: { repo: "Project", docs: "Documentation", issues: "Issues", releases: "Releases", image: "Image", recipe: "Recipe in this repository" },
    shots: "Screenshots",
    lang: "Português",
  },
};

const S = {
  lang: localStorage.getItem("qh-lang") || (navigator.language.startsWith("pt") ? "pt" : "en"),
  backupFirst: localStorage.getItem("qh-backup-first") === "1",   // the box next to Update, remembered
  rule: "tailnet",          // the host's access rule (qh --set-access)
  apps: [], group: null, filter: null, search: "", current: null, preCustom: {},
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
  $("lang").textContent = t("lang");
  $("recheck").textContent = t("recheck");
  $("history-btn").textContent = t("history");
  $("resources-btn").textContent = t("resources");
  $("settings-btn").textContent = t("settings");
  renderTabs();
}

const installed = () => S.apps.filter((a) => a.installed);

// Two screens, as CasaOS has them: what is installed (a launcher) and the catalog
// (somewhere to find and install). The choice lives in the URL hash, so a reload
// or a bookmark lands on the same one.
function renderTabs() {
  const aba = (id, key, view, n) => {
    fill($(id), t(key), h("span", { class: "count" }, String(n)));
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

function tile(a) {
  const st = health(a), url = openUrl(a);
  const corpo = [
    h("img", { src: a.icon, alt: "", loading: "lazy", referrerpolicy: "no-referrer" }),
    h("h3", {}, a.name),
    st && h("span", { class: `badge ${st[0]}`, title: st[2] || null }, st[1]),
    h("p", { class: "version", "data-res": a.id }, resText(a)),
  ];
  return h("div", { class: "card tile" },
    url
      ? h("a", { class: "tile-open", href: url, target: "_blank", rel: "noopener noreferrer",
                 "aria-label": `${t("open")} ${a.name}` }, ...corpo)
      : h("button", { class: "tile-open", type: "button", onclick: () => openPanel(a.id) }, ...corpo),
    url && h("button", { class: "gear", type: "button", title: t("manage"),
                         "aria-label": `${t("manage")} ${a.name}`, onclick: () => openPanel(a.id) }, "⚙"),
    controls(a));
}

function storeCard(a) {
  return h("button", { class: "card", type: "button", onclick: () => openPanel(a.id) },
    h("div", { class: "top" },
      h("img", { src: a.icon, alt: "", loading: "lazy", referrerpolicy: "no-referrer" }),
      h("div", {}, h("h3", {}, a.name),
        h("p", { class: "version" }, a.installed ? tagOf((mainUnit(a) || {}).installed_image) : ""))),
    h("p", { class: "desc" }, plain(a.description[S.lang] || a.description.en)),
    a.deprecated
      ? h("span", { class: "badge warn" }, a.installed ? `${t("deprecatedBadge")} · ${t("installedBadge")}` : t("deprecatedBadge"))
      : a.installed && h("span", { class: "badge plain" }, t("installedBadge")));
}

function renderGrid() {
  const q = S.search.trim().toLowerCase();
  const meus = S.view === "apps";
  const pool = meus ? installed().filter(FILTERS[S.filter] || (() => true))
                    : S.apps.filter((a) => !S.group || groupOf(a) === S.group);
  const shown = pool.filter((a) => matches(a, q));
  $("grid").className = meus ? "apps" : "";
  fill($("grid"), ...shown.map(meus ? tile : storeCard));
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

function openPanel(id) {
  closeLogs();
  S.current = id;
  S.info = { disk: null, arch: null };       // asked per app, when its panel opens
  renderPanel();
  loadInfo(id);
  $("p-form").hidden = true;
  $("p-out").hidden = true;
  $("p-clean").hidden = true;
  $("p-section").hidden = true;
  $("panel").showModal();
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

function renderInfo() {
  const a = current(), info = S.info || {};
  if (!a) return;
  const partes = [];
  const r = a.installed && resources(a);
  if (r) partes.push(`${t("cpu")} ${r.cpu.toFixed(1)}%`, `${t("mem")} ${mib(r.mem)}`);
  if (a.installed) partes.push(`${t("disk")} ${info.disk ? (info.disk.bytes === null ? "—" : mib(info.disk.bytes)) : t("counting")}`);
  if (a.units.some((u) => u.installed && u.override)) partes.push(t("customizedBadge"));
  const arq = info.arch;
  if (arq && arq.runs && arq.runs.length) partes.push(`${t("runsOn")} ${arq.runs.join(", ")}`);
  const sem = arq ? arq.units.filter((u) => u.ok === false).map((u) => u.unit) : [];
  fill($("p-info"), 
    partes.join(" · "),
    sem.length ? h("span", { class: "note" }, " ", t("noArm")(arq.host, sem.join(", "))) : null);
}

function stateClass(v) {
  if (v === "paused") return "warn";
  if (["active", "healthy", "up"].includes(v)) return "ok";
  if (["failed", "unhealthy", "down", "inactive"].includes(v)) return "bad";
  if (v === "changed" || v === "duplicated") return "warn";
  return null;
}

function renderPanel() {
  const a = current();
  $("p-icon").src = a.icon || "";
  $("p-name").textContent = a.name;
  $("p-meta").textContent = (a.group && a.group[S.lang]) || "";
  const sobre = a.about && (a.about[S.lang] || a.about.en);
  $("p-desc").textContent = plain(sobre || a.description[S.lang] || a.description.en)
    + (a.author ? ` — ${a.author}` : "") + (a.architectures ? ` (${a.architectures.join(", ")})` : "");

  // Images the project hosts (app.json, screenshots); each opens full size in a new tab.
  fill($("p-shots"), ...(a.screenshots || []).map((u) =>
    h("a", { href: u, target: "_blank", rel: "noopener noreferrer", "aria-label": t("shots") },
      h("img", { src: u, alt: "", loading: "lazy", referrerpolicy: "no-referrer" }))));
  $("p-shots").hidden = !(a.screenshots || []).length;

  const instaladas = new Set(a.units.filter((u) => u.installed).map((u) => u.unit));
  fill($("p-links"), ...a.web
    .filter((w) => instaladas.has(w.unit) && (w.tailnet || w.local))
    .map((w) => h("a", { href: w.tailnet || w.local, target: "_blank", rel: "noopener noreferrer" },
      `${t("open")} ${a.web.length > 1 ? w.unit : ""}`.trim() + " ↗")));

  const linhas = a.units.filter((u) => u.installed);
  $("p-units").hidden = !linhas.length;
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
          ? h("button", { type: "button", class: "ghost", onclick: () => showConsole(u.unit) }, t("console")) : null))));

  // The reason, where it is read; and a service that is discontinued is not offered for install.
  const motivo = depReason(a);
  const trial = a.installed && a.trial ? t("trialEnds")(trialWhen(a.trial), a.trial.purge) : null;
  const caidas = a.units.filter((u) => u.installed && u.failure && !u.stopped);
  $("p-fail").hidden = !caidas.length;
  fill($("p-fail"), ...caidas.map((u) => h("p", {}, failText(u))));
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
  const acoes = a.installed ? [controls(a)] : [];
  if (!a.installed) {
    if (!a.deprecated) {
      const deps = needs(a);
      acoes.push(h("button", { type: "button", onclick: () => plan("install") },
        deps.length ? t("installWith")(deps.map((x) => x.name).join(", ")) : t("install")));
      acoes.push(h("button", { type: "button", class: "ghost", onclick: () => showCustom(a, null, true) },
        S.preCustom[a.id] ? `${t("customize")} ✓` : t("customize")));
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
    acoes.push(h("button", { type: "button", class: "ghost", onclick: () => showCustom(a) }, t("customize")));
    if (a.has_env)
      acoes.push(h("button", { type: "button", class: "ghost", onclick: () => showEnv(a) }, t("configure")));
    if (a.has_login)
      acoes.push(h("button", { type: "button", class: "ghost", onclick: () => showLogin(a) }, t("login")));
    acoes.push(h("button", { type: "button", class: "ghost", onclick: () => showBackups(a) }, t("backups")));
    acoes.push(h("button", { type: "button", class: "danger", onclick: () => plan("remove") }, t("remove")));
  }
  // After the others: an app that was removed, or never came up, still has a past worth reading.
  acoes.push(h("button", { type: "button", class: "ghost", onclick: () => openHistory(a.id) }, t("history")));
  fill($("p-actions"), ...acoes, a.installed && a.web.length ? accessPicker(a) : null);
}

function out(text, append = false) {
  const pre = $("p-out");
  pre.hidden = false;
  pre.textContent = append ? pre.textContent + text : text;
  pre.scrollTop = pre.scrollHeight;
}

function busy(on) {
  for (const b of $("panel").querySelectorAll("button:not(#p-close)")) b.disabled = on;
}

async function plan(action, file = "") {
  const a = current();
  busy(true);
  if (!["restore", "backup"].includes(action)) $("p-section").hidden = true;
  try {
    const p = await api(`/api/plan?app=${encodeURIComponent(a.id)}&action=${action}` +
                        `&file=${encodeURIComponent(file)}&lang=${S.lang}`);
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
        h("td", { class: e.rc === 0 ? "ok" : "bad" }, e.rc === 0 ? "✓" : `✗ ${e.rc ?? "?"}`),
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

function grupo(nome, titulo, dica, itens) {
  const rows = [], caixa = h("div");
  const mostrar = () => fill(caixa, ...rows.map((r) => r.row));
  const juntar = (it) => {
    const r = linhas[nome](it);
    r.row = h("div", { class: "cust-row" }, ...r.els,
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

// `pre`: the form before an install. It works on the unit as it will be written, keeps what you choose
// in S.preCustom, and the install applies it once the unit exists.
async function showCustom(a, unit, pre = false) {
  const instaladas = pre ? a.units : a.units.filter((u) => u.installed);
  unit = unit || (mainUnit(a) || instaladas[0]).unit;
  let d;
  try { d = await api(`/api/custom?unit=${encodeURIComponent(unit)}${pre ? "&pre=1" : ""}`); }
  catch (e) { return section(h("p", { class: "note" }, String(e.message))); }
  const guardada = pre && (S.preCustom[a.id] || {})[unit];
  if (guardada) {          // what was chosen before comes back in the form
    d = { ...d, effective: { ...d.effective, ports: guardada.ports, volumes: guardada.volumes, env: guardada.env,
                             devices: guardada.devices, caps: guardada.caps },
          restart: guardada.restart || d.restart, limit_values: { memory: guardada.limits.memory, cpus: guardada.limits.cpus } };
  }

  const G = {
    ports: grupo("ports", t("cPorts"), t("portsHint"), d.effective.ports),
    volumes: grupo("volumes", t("cVolumes"), t("volumesHint")(d.roots), d.effective.volumes),
    env: grupo("env", t("cEnv"), t("custEnvHint"), d.effective.env),
    devices: grupo("devices", t("cDevices"), null, d.effective.devices),
  };
  const tem = new Set(d.effective.caps.map((c) => c.name));
  const caps = [...new Set([...d.caps_ok, ...tem])].map((n) =>
    ({ n, box: h("input", { type: "checkbox", id: `cap-${n}`, checked: tem.has(n) }) }));
  const reinicio = escolha(d.restarts.map((r) => [r, r]), d.restart || "always");
  // Limits need the controllers delegated to the user; a field the host cannot honour is shown, disabled,
  // with the reason. Its value still goes back as it is, so what the unit already says is never "changed".
  const lv = d.limit_values || { memory: "", cpus: "" };
  const limMem = h("input", { id: "lim-mem", type: "text", value: lv.memory, placeholder: "512m", autocomplete: "off",
                              disabled: !d.limits.memory, "aria-label": t("limMemory") });
  const limCpu = h("input", { id: "lim-cpu", type: "text", value: lv.cpus, placeholder: "1.5", autocomplete: "off",
                              disabled: !d.limits.cpu, "aria-label": t("limCpus") });
  const saida = h("div", { class: "cust-out" });
  const config = () => ({ ports: G.ports.read(), volumes: G.volumes.read(), env: G.env.read(), devices: G.devices.read(),
    caps: caps.filter((c) => c.box.checked).map((c) => ({ name: c.n })), restart: reinicio.value,
    limits: { memory: limMem.value.trim(), cpus: limCpu.value.trim() } });

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

  const aplicar = async () => {
    const r = await previa();
    if (r.errors.length || !r.changed) return;
    await follow(() => api("/api/custom/apply", { unit, config: config() }));
    showCustom(current(), unit);
  };
  const reverter = async () => {
    await follow(() => api("/api/custom/reset", { unit }));
    showCustom(current(), unit);
  };
  // Before an install nothing is written: the choice is checked, remembered, and sent with the install.
  const guardar = async () => {
    const r = await previa();
    if (r.errors.length) return;
    S.preCustom[a.id] = { ...(S.preCustom[a.id] || {}) };
    if (r.changed) S.preCustom[a.id][unit] = config(); else delete S.preCustom[a.id][unit];
    if (!Object.keys(S.preCustom[a.id]).length) delete S.preCustom[a.id];
    out(r.changed ? t("preSaved") : t("preNone"));
  };
  const descartar = () => {
    if (S.preCustom[a.id]) delete S.preCustom[a.id][unit];
    if (S.preCustom[a.id] && !Object.keys(S.preCustom[a.id]).length) delete S.preCustom[a.id];
    showCustom(a, unit, true);
  };

  section(h("form", { class: "cust", onsubmit: (ev) => ev.preventDefault() },
    h("h3", {}, `${t("customize")} · ${unit}`),
    pre ? h("p", { class: "note" }, t("preIntro")) : null,
    instaladas.length > 1
      ? h("select", { "aria-label": "unit", onchange: (ev) => showCustom(a, ev.target.value, pre) },
          ...instaladas.map((u) => h("option", { value: u.unit, selected: u.unit === unit }, u.unit)))
      : null,
    h("p", { class: "help" }, t("custIntro")),
    d.base_changed ? h("p", { class: "note" }, t("baseChanged")) : null,
    d.override ? h("p", { class: "cust-note" }, `${t("filePath")}: ${d.file}`) : null,
    G.ports.el, G.volumes.el, G.env.el, G.devices.el,
    h("div", { class: "cust-group" }, h("h4", {}, t("cCaps")), h("p", { class: "cust-note" }, t("capsHint")),
      h("div", { class: "caps" }, ...caps.map((c) => h("label", { class: "check", for: `cap-${c.n}` }, c.box, ` ${c.n}`)))),
    h("div", { class: "cust-group" }, h("h4", {}, t("cRestart")), reinicio),
    h("div", { class: "cust-group" }, h("h4", {}, t("cLimits")),
      h("p", { class: "cust-note" }, d.limits.memory && d.limits.cpu ? t("limitsHint") : t("limitsOff")),
      h("div", { class: "row" },
        h("label", { for: "lim-mem" }, t("limMemory")), limMem, h("span", { class: "muted" }, t("limMemoryHint")),
        h("label", { for: "lim-cpu" }, t("limCpus")), limCpu, h("span", { class: "muted" }, t("limCpusHint")))),
    h("div", { class: "row" },
      h("button", { type: "button", class: "ghost", onclick: previa }, t("previewBtn")),
      pre ? h("button", { type: "button", onclick: guardar }, t("preSave")) : h("button", { type: "button", onclick: aplicar }, t("saveApply")),
      pre && guardada ? h("button", { type: "button", class: "danger", onclick: descartar }, t("preDiscard")) : null,
      !pre && d.override ? h("button", { type: "button", class: "danger", onclick: reverter }, t("revertBtn")) : null),
    saida));
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
  try { S.stats = (await api("/api/stats")).stats; updateResources(); } catch (e) { /* next turn */ }
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
    if (deps.length) campos.push(h("p", { class: "note" }, t("requiresNote")(deps.map((x) => x.name).join(", "))));
    for (const x of [...deps, a]) campos.push(...asksFields(x));
    campos.push(h("label", { for: "trial" }, t("trialLabel")));
    campos.push(h("select", { id: "trial", "data-trial": "1" },
      ...[["", t("trialNone")], ["1h", "1 h"], ["6h", "6 h"], ["1d", "1 d"], ["7d", "7 d"], ["reboot", t("trialReboot")]]
        .map(([v, r]) => h("option", { value: v }, r))));
    campos.push(h("label", { class: "check" }, h("input", { id: "trial-purge", type: "checkbox" }), " " + t("trialPurge")));
    campos.push(h("p", { class: "help" }, t("trialHint")));
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
  if (action === "install" && S.preCustom[a.id])
    campos.push(h("p", { class: "note" }, t("preRides")(Object.keys(S.preCustom[a.id]).join(", "))));
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
      t("confirm")), " ",
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
  const purge = action === "remove" && !!($("p-form").querySelector("[data-purge]") || {}).checked;
  await follow(() => api("/api/run", { app: a.id, action, secrets, vars, file, confirm,
                                       ...(trial ? { trial, trial_purge } : {}), ...(custom ? { custom } : {}),
                                       ...(purge ? { purge: true } : {}), ...(Object.keys(options).length ? { options } : {}) }));
  if (custom) delete S.preCustom[a.id];
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

// What the terminal would have asked for one service: `manual` secrets and unset [vars].
function asksFields(x) {
  const campos = [];
  for (const s of x.asks.secrets) {
    campos.push(h("label", { for: `s-${s.secret}` }, s.secret));
    campos.push(h("input", { id: `s-${s.secret}`, type: "password", "data-secret": s.secret,
                             autocomplete: "new-password" }));
    campos.push(h("p", { class: "help" }, plain(s.instruction) + " — " +
                  (s.exists ? t("exists") : t("secretHint"))));
  }
  for (const v of x.asks.vars.filter((y) => !y.set)) {
    campos.push(h("label", { for: `v-${v.name}` }, v.name));
    campos.push(h("input", { id: `v-${v.name}`, type: "text", "data-var": v.name, value: v.default }));
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

// A job shown in its own window: what an update of everything, or a rule applied to all, prints.
async function jobWindow(titulo, start) {
  $("b-title").textContent = titulo;
  $("b-out").textContent = `${t("working")}\n`;
  $("bulk").showModal();
  try {
    const { job } = await start();
    let next = 0, st;
    do {
      await new Promise((r) => setTimeout(r, 900));
      st = await api(`/api/job/${job}?from=${next}`);
      next = st.next;
      if (st.output) $("b-out").textContent += st.output;
    } while (st.rc === null);
    $("b-out").textContent += `\n${st.rc === 0 ? t("done") : `${t("failed")} (${st.rc}).`}\n`;
  } catch (e) { $("b-out").textContent += e.status === 409 ? t("busy") : String(e.message); }
  await load();
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
    await alertsSection(),
    h("section", {}, h("p", { class: "muted" }, c.tailnet ? t("tailnetOn") : t("tailnetOff"))));
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
    secao("volumes", t("resVolumes"), r.volumes, null, r.volumes.map((v) => h("tr", {}, h("td", {}, v.name)))));
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

async function unitVerb(unit, verb) {
  $("p-form").hidden = true;
  await follow(() => api("/api/unit", { unit, verb }));
}

async function follow(start) {
  busy(true);
  out(`${t("working")}\n`);
  try {
    const { job } = await start();
    let next = 0, st;
    do {
      await new Promise((r) => setTimeout(r, 900));
      st = await api(`/api/job/${job}?from=${next}`);
      next = st.next;
      if (st.output) out(st.output, true);
    } while (st.rc === null);
    out(`\n${st.rc === 0 ? t("done") : `${t("failed")} (${st.rc}).`}\n`, true);
  } catch (e) {
    out(e.status === 409 ? t("busy") : String(e.message), true);
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
$("panel").addEventListener("close", closeLogs);
$("history-btn").addEventListener("click", () => openHistory(null));
$("h-close").addEventListener("click", () => $("history").close());
$("resources-btn").addEventListener("click", openResources);
$("settings-btn").addEventListener("click", openSettings);
$("s-close").addEventListener("click", () => $("settings").close());
$("b-close").addEventListener("click", () => $("bulk").close());
$("r-close").addEventListener("click", () => $("resources").close());
$("recheck").addEventListener("click", () => loadUpdates(true));
renderChrome();
load();
setInterval(pollStats, 10000);

// The host in one line, at the top: load over the CPUs, memory used, hottest sensor, uptime.
// A few file reads on the server; a field the host does not report is simply left out.
function hostLine(h) {
  const gb = (b) => (b / 2 ** 30).toFixed(1);
  const up = h.uptime === null ? null : h.uptime >= 86400 ? `${Math.floor(h.uptime / 86400)} d` : `${Math.floor(h.uptime / 3600)} h`;
  const partes = [
    h.load === null ? null : `${t("hostCpu")} ${Math.round((h.load / h.cpus) * 100)}%`,
    h.mem ? `${t("hostMem")} ${gb(h.mem.used)}/${gb(h.mem.total)} GB` : null,
    h.temp === null ? null : `${h.temp} °C`,
    up ? `${t("hostUp")} ${up}` : null,
  ].filter(Boolean);
  return partes.join(" · ");
}
async function pollHost() {
  try { $("host").textContent = hostLine(await api("/api/host")); } catch (e) { /* the line just stays */ }
}
pollHost();
setInterval(pollHost, 30000);

// The store's page. Every string the server sends goes in through textContent:
// descriptions and command output come from files and processes, not from us.
"use strict";

const T = {
  pt: {
    search: "Buscar apps", tabApps: "Meus apps", tabStore: "Loja", all: "Todos", other: "Outros",
    noneInstalled: "Nenhum app instalado ainda.", goStore: "Abrir a Loja", manage: "Gerenciar",
    installedBadge: "instalado", deprecatedBadge: "descontinuado", deprecatedNote: "Descontinuado:",
    noInstall: "Não dá para instalar este app daqui.",
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
    limitsOff: "Limite de memória e CPU: indisponível aqui. O systemd do seu usuário não delega esses " +
      "controladores, e com um limite o container não sobe (veja docs/tools.md).",
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
    removeNote: "Remove as units e para o serviço. Volumes, secrets e .env ficam.",
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
    act: { install: "Instalar", update: "Atualizar", upgrade: "Atualizar versão", remove: "Remover", backup: "Backup",
           restore: "Restaurar", access: "Acesso", env: "Configuração", start: "Iniciar", stop: "Parar", restart: "Reiniciar",
           customize: "Personalizar", revert: "Reverter" },
    link: { repo: "Projeto", docs: "Documentação", issues: "Problemas", releases: "Releases", image: "Imagem", recipe: "Receita neste repositório" },
    shots: "Capturas de tela",
    lang: "English",
  },
  en: {
    search: "Search apps", tabApps: "My apps", tabStore: "Store", all: "All", other: "Other",
    noneInstalled: "No app installed yet.", goStore: "Open the Store", manage: "Manage",
    installedBadge: "installed", deprecatedBadge: "discontinued", deprecatedNote: "Discontinued:",
    noInstall: "It cannot be installed from here.",
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
    limitsOff: "Memory and CPU limits: not available here. Your user's systemd does not delegate those " +
      "controllers, and with a limit the container does not start (see docs/tools.md).",
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
    removeNote: "Removes the units and stops the service. Volumes, secrets and .env stay.",
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
    act: { install: "Install", update: "Update", upgrade: "Update version", remove: "Remove", backup: "Backup",
           restore: "Restore", access: "Access", env: "Settings", start: "Start", stop: "Stop", restart: "Restart",
           customize: "Customize", revert: "Revert" },
    link: { repo: "Project", docs: "Documentation", issues: "Issues", releases: "Releases", image: "Image", recipe: "Recipe in this repository" },
    shots: "Screenshots",
    lang: "Português",
  },
};

const S = {
  lang: localStorage.getItem("qh-lang") || (navigator.language.startsWith("pt") ? "pt" : "en"),
  rule: "tailnet",          // the host's access rule (qh --set-access)
  apps: [], group: null, search: "", current: null,
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
function health(app) {
  const inst = app.units.filter((u) => u.installed);
  if (!inst.length) return null;
  if (inst.some((u) => u.service !== "active" || ["unhealthy", "down"].includes(u.container)))
    return ["bad", t("attention")];
  const rows = inst.map((u) => S.upd[u.unit]).filter(Boolean);
  if (rows.some((r) => r.bucket === "GONE")) return ["bad", t("gone")];
  if (app.deprecated) return ["warn", t("deprecatedBadge")];
  if (app.trial) return ["warn", t("trialBadge")];
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

// Marked in install.ini [store]: why a service is discontinued, in the page's language.
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
  if (typeof history !== "undefined" && history.replaceState) history.replaceState(null, "", `#${view}`);
  renderTabs();
  renderGroups();
  renderGrid();
}

function renderGroups() {
  // Categories are for browsing the catalog; a handful of installed apps needs none.
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

function tile(a) {
  const st = health(a), url = openUrl(a);
  const corpo = [
    h("img", { src: a.icon, alt: "", loading: "lazy", referrerpolicy: "no-referrer" }),
    h("h3", {}, a.name),
    st && h("span", { class: `badge ${st[0]}` }, st[1]),
    h("p", { class: "version", "data-res": a.id }, resText(a)),
  ];
  return h("div", { class: "card tile" },
    url
      ? h("a", { class: "tile-open", href: url, target: "_blank", rel: "noopener noreferrer",
                 "aria-label": `${t("open")} ${a.name}` }, ...corpo)
      : h("button", { class: "tile-open", type: "button", onclick: () => openPanel(a.id) }, ...corpo),
    url && h("button", { class: "gear", type: "button", title: t("manage"),
                         "aria-label": `${t("manage")} ${a.name}`, onclick: () => openPanel(a.id) }, "⚙"));
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
  const pool = meus ? installed() : S.apps.filter((a) => !S.group || groupOf(a) === S.group);
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
  S.current = id;
  S.info = { disk: null, arch: null };       // asked per app, when its panel opens
  renderPanel();
  loadInfo(id);
  $("p-form").hidden = true;
  $("p-out").hidden = true;
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
    fill($("p-project"), ...links.map((l) =>
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
  $("p-desc").textContent = plain(a.description[S.lang] || a.description.en);

  // Images the project hosts (install.ini [store]); each opens full size in a new tab.
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
      h("td", { class: u.drift ? stateClass(u.drift) : "ok" }, `${tagOf(u.image)} · ${t(u.drift || "synced")}`),
      h("td", {},
        ...(u.service === "active" ? ["restart", "stop"] : ["start"]).map((v) =>
          h("button", { type: "button", class: "ghost", onclick: () => unitVerb(u.unit, v) }, t(v))),
        h("button", { type: "button", class: "ghost", onclick: () => showLogs(u.unit) }, t("logs"))))));

  // The reason, where it is read; and a service that is discontinued is not offered for install.
  const motivo = depReason(a);
  const trial = a.installed && a.trial ? t("trialEnds")(trialWhen(a.trial), a.trial.purge) : null;
  $("p-notice").hidden = !motivo && !trial;
  if (motivo) $("p-notice").textContent = `${t("deprecatedNote")} ${motivo}${a.installed ? "" : ` ${t("noInstall")}`}`;
  else if (trial) $("p-notice").textContent = trial;
  const acoes = [];
  if (!a.installed) {
    if (!a.deprecated) {
      const deps = needs(a);
      acoes.push(h("button", { type: "button", onclick: () => plan("install") },
        deps.length ? t("installWith")(deps.map((x) => x.name).join(", ")) : t("install")));
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
      const alvo = tagOf(mudou.image) !== tagOf(mudou.installed_image) ? tagOf(mudou.image) : null;
      acoes.push(h("button", { type: "button", onclick: () => updateNow("update") },
        alvo ? t("upgradeTo")(alvo) : t("update")));
    }
    if (a.trial)
      acoes.push(h("button", { type: "button", onclick: () => keepTrial() }, t("trialKeep")));
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

const appName = (id) => (S.apps.find((a) => a.id === id) || { name: id }).name;

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
    const rotulo = escolha([["Z", t("labelZ")], ["z", t("labelz")], ["", t("labelNone")]], it ? it.label : "Z");
    const ro = h("input", { type: "checkbox", checked: !!(it && it.ro), "aria-label": t("readOnly") });
    return { els: [host, cont, rotulo, h("label", { class: "check" }, ro, ` ${t("readOnly")}`)],
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

async function showCustom(a, unit) {
  const instaladas = a.units.filter((u) => u.installed);
  unit = unit || (mainUnit(a) || instaladas[0]).unit;
  let d;
  try { d = await api(`/api/custom?unit=${encodeURIComponent(unit)}`); }
  catch (e) { return section(h("p", { class: "note" }, String(e.message))); }

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
  const saida = h("div", { class: "cust-out" });
  const config = () => ({ ports: G.ports.read(), volumes: G.volumes.read(), env: G.env.read(), devices: G.devices.read(),
    caps: caps.filter((c) => c.box.checked).map((c) => ({ name: c.n })), restart: reinicio.value });

  async function previa() {
    try {
      const r = await api("/api/custom/preview", { unit, config: config() });
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

  section(h("form", { class: "cust", onsubmit: (ev) => ev.preventDefault() },
    h("h3", {}, `${t("customize")} · ${unit}`),
    instaladas.length > 1
      ? h("select", { "aria-label": "unit", onchange: (ev) => showCustom(a, ev.target.value) },
          ...instaladas.map((u) => h("option", { value: u.unit, selected: u.unit === unit }, u.unit)))
      : null,
    h("p", { class: "help" }, t("custIntro")),
    d.base_changed ? h("p", { class: "note" }, t("baseChanged")) : null,
    d.override ? h("p", { class: "cust-note" }, `${t("filePath")}: ${d.file}`) : null,
    G.ports.el, G.volumes.el, G.env.el, G.devices.el,
    h("div", { class: "cust-group" }, h("h4", {}, t("cCaps")), h("p", { class: "cust-note" }, t("capsHint")),
      h("div", { class: "caps" }, ...caps.map((c) => h("label", { class: "check", for: `cap-${c.n}` }, c.box, ` ${c.n}`)))),
    h("div", { class: "cust-group" }, h("h4", {}, t("cRestart")), reinicio),
    d.limits.memory && d.limits.cpu ? null : h("p", { class: "cust-note" }, t("limitsOff")),
    h("div", { class: "row" },
      h("button", { type: "button", class: "ghost", onclick: previa }, t("previewBtn")),
      h("button", { type: "button", onclick: aplicar }, t("saveApply")),
      d.override ? h("button", { type: "button", class: "danger", onclick: reverter }, t("revertBtn")) : null),
    saida));
}

// The settings of a service: its .env, as the .example files lay it out. An
// optional setting ships commented out; ticking it turns it on, unticking an
// active one comments it out again. Only what changed is sent.
async function showEnv(a) {
  try {
    const { files } = await api(`/api/env?app=${encodeURIComponent(a.id)}`);
    if (!files.length) return section(h("p", { class: "muted" }, t("noEnv")));
    const linhas = [];
    for (const f of files) {
      const campos = f.entries.map((e, i) => {
        const id = `e-${f.file}-${i}`;
        const caixa = h("input", { type: "checkbox", id: `${id}-on`, checked: e.active, "aria-label": t("active") });
        const valor = h("input", { id, type: e.sensitive ? "password" : "text", value: e.value,
                                   autocomplete: "off", disabled: !e.active });
        caixa.onchange = () => { valor.disabled = !caixa.checked; };
        return { e, caixa, valor, linha: h("div", { class: "env-row" },
          caixa, h("label", { for: id }, e.key), valor,
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
        for (const { e, caixa, valor } of f.campos) {
          if (caixa.checked && (!e.active || valor.value !== e.value)) mudar[e.key] = valor.value;
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
  if (action === "remove") campos.push(h("p", { class: "note" }, t("removeNote")));
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
  const trial = action === "install" ? ($("trial") || {}).value || "" : "";
  const trial_purge = !!trial && !!($("trial-purge") || {}).checked;
  $("p-form").hidden = true;
  await follow(() => api("/api/run", { app: a.id, action, secrets, vars, file, confirm, ...(trial ? { trial, trial_purge } : {}) }));
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
    ...["local", "tailnet", "both"].map((m) => h("option", { value: m, selected: atual === m }, t("modes")[m])));
  sel.onchange = () => follow(() => api("/api/run", { app: a.id, action: "access", mode: sel.value }));
  return h("label", { class: "access" }, `${t("access")}: `, sel);
}

async function updateNow(action) {
  const a = current();
  $("p-form").hidden = true;
  if (behind(a).length) showNotes(a);
  else $("p-section").hidden = true;
  await follow(() => api("/api/run", { app: a.id, action }));
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

async function showLogs(unit) {
  try { out((await api(`/api/logs?unit=${encodeURIComponent(unit)}`)).output || "—"); }
  catch (e) { out(String(e.message)); }
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
$("history-btn").addEventListener("click", () => openHistory(null));
$("h-close").addEventListener("click", () => $("history").close());
$("recheck").addEventListener("click", () => loadUpdates(true));
renderChrome();
load();
setInterval(pollStats, 10000);

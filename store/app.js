// The store's page. Every string the server sends goes in through textContent:
// descriptions and command output come from files and processes, not from us.
"use strict";

const T = {
  pt: {
    search: "Buscar apps", onlyInstalled: "Só instalados", all: "Todos", other: "Outros",
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
    notes: "Novidades", notesFrom: "Releases desde a instalada", noNotes: "Nenhuma release nova para ler.",
    onGithub: "ver no GitHub",
    notInRepo: (pin, novo) => `O repositório ainda fixa ${pin}, a versão instalada. A ${novo} só chega pelo ` +
      `Atualizar depois do bump no repositório (qh-updates --bump --apply, e então commit).`,
    nothingToDo: "Nada a fazer: o instalado já é igual ao que o repositório fixa.",
    lang: "English",
  },
  en: {
    search: "Search apps", onlyInstalled: "Installed only", all: "All", other: "Other",
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
    notes: "What's new", notesFrom: "Releases since the installed one", noNotes: "No new release to read.",
    onGithub: "see on GitHub",
    notInRepo: (pin, novo) => `The repository still pins ${pin}, the installed version. ${novo} only arrives ` +
      `through Update after the repository is bumped (qh-updates --bump --apply, then commit).`,
    nothingToDo: "Nothing to do: what is installed already matches what the repository pins.",
    lang: "Português",
  },
};

const S = {
  lang: localStorage.getItem("qh-lang") || (navigator.language.startsWith("pt") ? "pt" : "en"),
  apps: [], group: null, search: "", onlyInstalled: false, current: null,
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

const groupOf = (app) => (app.group ? app.group[S.lang] : t("other"));

// -- grid -------------------------------------------------------------------

function renderChrome() {
  document.documentElement.lang = S.lang === "pt" ? "pt-BR" : "en";
  $("search").placeholder = t("search");
  $("only-installed-label").textContent = t("onlyInstalled");
  $("lang").textContent = t("lang");
  $("recheck").textContent = t("recheck");
}

function renderGroups() {
  const groups = [...new Set(S.apps.map(groupOf))].sort((a, b) => a.localeCompare(b, S.lang));
  const chip = (g, label) => h("button", {
    type: "button", "aria-pressed": String(S.group === g),
    onclick: () => { S.group = g; renderGroups(); renderGrid(); },
  }, label);
  $("groups").replaceChildren(chip(null, t("all")), ...groups.map((g) => chip(g, g)));
}

function renderGrid() {
  const q = S.search.trim().toLowerCase();
  const shown = S.apps.filter((a) =>
    (!S.group || groupOf(a) === S.group) &&
    (!S.onlyInstalled || a.installed) &&
    (!q || `${a.name} ${a.id} ${a.description.en} ${a.description.pt}`.toLowerCase().includes(q)));
  $("grid").replaceChildren(...shown.map((a) => {
    const st = health(a);
    return h("button", { class: "card", type: "button", onclick: () => openPanel(a.id) },
      h("div", { class: "top" },
        h("img", { src: a.icon, alt: "", loading: "lazy", referrerpolicy: "no-referrer" }),
        h("div", {}, h("h3", {}, a.name),
          h("p", { class: "version" }, a.installed ? tagOf((mainUnit(a) || {}).installed_image) : ""))),
      h("p", { class: "desc" }, plain(a.description[S.lang] || a.description.en)),
      st && h("span", { class: `badge ${st[0]}` }, st[1]));
  }));
  $("empty").hidden = shown.length > 0;
  $("empty").textContent = t("none");
}

async function load() {
  const cat = await api(`/api/catalog?lang=${S.lang}`);
  S.apps = cat.apps;
  renderGroups();
  renderGrid();
  if (S.current && $("panel").open) renderPanel();
  loadUpdates(false);
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
  renderPanel();
  $("p-form").hidden = true;
  $("p-out").hidden = true;
  $("p-section").hidden = true;
  $("panel").showModal();
}

const current = () => S.apps.find((a) => a.id === S.current);

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

  const instaladas = new Set(a.units.filter((u) => u.installed).map((u) => u.unit));
  $("p-links").replaceChildren(...a.web
    .filter((w) => instaladas.has(w.unit) && (w.tailnet || w.local))
    .map((w) => h("a", { href: w.tailnet || w.local, target: "_blank", rel: "noopener noreferrer" },
      `${t("open")} ${a.web.length > 1 ? w.unit : ""}`.trim() + " ↗")));

  const linhas = a.units.filter((u) => u.installed);
  $("p-units").hidden = !linhas.length;
  $("p-units").replaceChildren(
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

  const acoes = [];
  if (!a.installed) acoes.push(h("button", { type: "button", onclick: () => plan("install") }, t("install")));
  else {
    acoes.push(h("button", { type: "button", onclick: () => plan("update") }, t("update")));
    if (behind(a).length)
      acoes.push(h("button", { type: "button", class: "ghost", onclick: () => showNotes(a) }, t("notes")));
    if (a.has_login)
      acoes.push(h("button", { type: "button", class: "ghost", onclick: () => showLogin(a) }, t("login")));
    acoes.push(h("button", { type: "button", class: "ghost", onclick: () => showBackups(a) }, t("backups")));
    acoes.push(h("button", { type: "button", class: "danger", onclick: () => plan("remove") }, t("remove")));
  }
  $("p-actions").replaceChildren(...acoes);
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
  if (action === "update" && behind(a).length) showNotes(a);   // read before you update
  else if (!["restore", "backup"].includes(action)) $("p-section").hidden = true;
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
  $("p-section").replaceChildren(...kids);
  $("p-section").hidden = false;
}

async function showNotes(a) {
  section(h("p", { class: "muted" }, t("checking")));
  const blocos = [h("h3", {}, t("notesFrom"))];
  for (const u of behind(a)) {
    // What Update can bring is what the repository pins, not what upstream released.
    if (tagOf(u.image) === tagOf(u.installed_image))
      blocos.push(h("p", { class: "note" }, t("notInRepo")(tagOf(u.image), S.upd[u.unit].there)));
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
    for (const s of a.asks.secrets) {
      campos.push(h("label", { for: `s-${s.secret}` }, s.secret));
      campos.push(h("input", { id: `s-${s.secret}`, type: "password", "data-secret": s.secret,
                               autocomplete: "new-password" }));
      campos.push(h("p", { class: "help" }, plain(s.instruction) + " — " +
                    (s.exists ? t("exists") : t("secretHint"))));
    }
    for (const v of a.asks.vars.filter((x) => !x.set)) {
      campos.push(h("label", { for: `v-${v.name}` }, v.name));
      campos.push(h("input", { id: `v-${v.name}`, type: "text", "data-var": v.name, value: v.default }));
    }
  }
  if (action === "remove") campos.push(h("p", { class: "note" }, t("removeNote")));
  campos.push(h("div", {},
    h("button", { type: "submit", class: ["remove", "restore"].includes(action) ? "danger" : null },
      t("confirm")), " ",
    h("button", { type: "button", class: "ghost", onclick: () => { form.hidden = true; } }, t("cancel"))));
  form.replaceChildren(...campos);
  form.onsubmit = (ev) => { ev.preventDefault(); run(action, file); };
  form.hidden = false;
}

async function run(action, file = "") {
  const a = current();
  const secrets = {}, vars = {};
  const confirm = ($("p-form").querySelector("[data-confirm]") || {}).value || "";
  for (const i of $("p-form").querySelectorAll("[data-secret]")) if (i.value) secrets[i.dataset.secret] = i.value;
  for (const i of $("p-form").querySelectorAll("[data-var]")) if (i.value) vars[i.dataset.var] = i.value;
  $("p-form").hidden = true;
  await follow(() => api("/api/run", { app: a.id, action, secrets, vars, file, confirm }));
  if (action === "backup" || action === "restore") showBackups(a);
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
$("only-installed").addEventListener("change", (e) => { S.onlyInstalled = e.target.checked; renderGrid(); });
$("lang").addEventListener("click", () => {
  S.lang = S.lang === "pt" ? "en" : "pt";
  localStorage.setItem("qh-lang", S.lang);
  S.group = null;
  renderChrome();
  load();
});
$("p-close").addEventListener("click", () => $("panel").close());
$("recheck").addEventListener("click", () => loadUpdates(true));
renderChrome();
load();

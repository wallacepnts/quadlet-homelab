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
    version: "versão", lang: "English",
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
    version: "version", lang: "Português",
  },
};

const S = {
  lang: localStorage.getItem("qh-lang") || (navigator.language.startsWith("pt") ? "pt" : "en"),
  apps: [], group: null, search: "", onlyInstalled: false, current: null,
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

function health(app) {
  const inst = app.units.filter((u) => u.installed);
  if (!inst.length) return null;
  if (inst.some((u) => u.service !== "active" || ["unhealthy", "down"].includes(u.container)))
    return ["bad", t("attention")];
  if (inst.some((u) => u.drift)) return ["warn", t("changed")];
  return ["ok", t("running")];
}

const groupOf = (app) => (app.group ? app.group[S.lang] : t("other"));

// -- grid -------------------------------------------------------------------

function renderChrome() {
  document.documentElement.lang = S.lang === "pt" ? "pt-BR" : "en";
  $("search").placeholder = t("search");
  $("only-installed-label").textContent = t("onlyInstalled");
  $("lang").textContent = t("lang");
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
        h("div", {}, h("h3", {}, a.name), h("p", { class: "version" }, a.version || ""))),
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
}

// -- panel ------------------------------------------------------------------

function openPanel(id) {
  S.current = id;
  renderPanel();
  $("p-form").hidden = true;
  $("p-out").hidden = true;
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
  $("p-meta").textContent = [a.group && a.group[S.lang], a.version && `${t("version")} ${a.version}`]
    .filter(Boolean).join(" · ");
  $("p-desc").textContent = plain(a.description[S.lang] || a.description.en);

  const instaladas = new Set(a.units.filter((u) => u.installed).map((u) => u.unit));
  $("p-links").replaceChildren(...a.web
    .filter((w) => instaladas.has(w.unit) && (w.tailnet || w.local))
    .map((w) => h("a", { href: w.tailnet || w.local, target: "_blank", rel: "noopener noreferrer" },
      `${t("open")} ${a.web.length > 1 ? w.unit : ""}`.trim() + " ↗")));

  const linhas = a.units.filter((u) => u.installed);
  $("p-units").hidden = !linhas.length;
  $("p-units").replaceChildren(
    h("tr", {}, ...["unit", "service", "container", "repo", ""].map((k) => h("th", {}, k ? t(k) : ""))),
    ...linhas.map((u) => h("tr", {},
      h("td", {}, u.unit),
      h("td", { class: stateClass(u.service) }, u.service || "—"),
      h("td", { class: stateClass(u.container) }, u.container || "—"),
      h("td", { class: u.drift ? stateClass(u.drift) : "ok" }, t(u.drift || "synced")),
      h("td", {},
        ...(u.service === "active" ? ["restart", "stop"] : ["start"]).map((v) =>
          h("button", { type: "button", class: "ghost", onclick: () => unitVerb(u.unit, v) }, t(v))),
        h("button", { type: "button", class: "ghost", onclick: () => showLogs(u.unit) }, t("logs"))))));

  const acoes = [];
  if (!a.installed) acoes.push(h("button", { type: "button", onclick: () => plan("install") }, t("install")));
  else {
    acoes.push(h("button", { type: "button", onclick: () => plan("update") }, t("update")));
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

async function plan(action) {
  const a = current();
  busy(true);
  try {
    const p = await api(`/api/plan?app=${encodeURIComponent(a.id)}&action=${action}&lang=${S.lang}`);
    out(`# ${t("plan")}\n\n${p.output}`);
    buildForm(a, action);
  } catch (e) { out(String(e.message)); }
  finally { busy(false); }
}

// What the terminal would have asked: `manual` secrets and unset [vars].
function buildForm(a, action) {
  const form = $("p-form");
  const campos = [];
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
    h("button", { type: "submit", class: action === "remove" ? "danger" : null }, t("confirm")), " ",
    h("button", { type: "button", class: "ghost", onclick: () => { form.hidden = true; } }, t("cancel"))));
  form.replaceChildren(...campos);
  form.onsubmit = (ev) => { ev.preventDefault(); run(action); };
  form.hidden = false;
}

async function run(action) {
  const a = current();
  const secrets = {}, vars = {};
  for (const i of $("p-form").querySelectorAll("[data-secret]")) if (i.value) secrets[i.dataset.secret] = i.value;
  for (const i of $("p-form").querySelectorAll("[data-var]")) if (i.value) vars[i.dataset.var] = i.value;
  $("p-form").hidden = true;
  await follow(() => api("/api/run", { app: a.id, action, secrets, vars }));
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
renderChrome();
load();

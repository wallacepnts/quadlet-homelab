// Runs store/app.js in Node against a stand-in DOM and a stubbed fetch, and checks what the page does.
//
//     node store/test/ui.js
//
// Not part of the CI (which is Python only). It catches what `node --check` cannot — a wrong name, a
// state that renders "null" — and it made one thing explicit: the stand-in follows the BROWSER,
// where a null or false argument to replaceChildren becomes the word "null" (h() skips them).
// store/test/browser.js is the check against a real Chromium.
const fs = require("fs");
const path = require("path");

class Txt { constructor(s) { this.text = s; } }
class El {
  constructor(tag) { this.tag = tag; this.kids = []; this.attrs = {}; this.listeners = {}; this.dataset = {};
    this.hidden = false; this.open = false; this.disabled = false; this.checked = false; this.value = ""; this.id = ""; this.className = ""; this.style = { setProperty(k, v) { this[k] = v; }, removeProperty(k) { delete this[k]; } };
    const cls = new Set(); this.classList = { toggle: (c, on) => (on ? cls.add(c) : cls.delete(c)), contains: (c) => cls.has(c), add: (c) => cls.add(c), remove: (c) => cls.delete(c) }; this.offsetWidth = 280; this.offsetHeight = 360; }
  setAttribute(k, v) { this.attrs[k] = v; if (k === "id") this.id = v;
    if (k === "value") this.value = v; if (k === "checked") this.checked = true; if (k === "disabled") this.disabled = true;
    if (k.startsWith("data-")) this.dataset[k.slice(5).replace(/-(.)/g, (_, c) => c.toUpperCase())] = v; }
  addEventListener(e, f) { this.listeners[e] = f; }
  removeAttribute(k) { delete this.attrs[k]; if (k === "id") this.id = ""; }
  getAttribute(k) { return this.attrs[k]; }
  // Like the browser: whatever is not a Node becomes text — a null argument is the word "null".
  append(...k) { for (const x of k) this.kids.push(x instanceof El || x instanceof Txt ? x : new Txt(String(x))); }
  replaceChildren(...k) { this.kids = []; this.append(...k); }
  set textContent(v) { this.kids = [new Txt(String(v))]; }
  get textContent() { return this.kids.map((k) => (k instanceof El ? k.textContent : k.text)).join(""); }
  get lastChild() { return this.kids[this.kids.length - 1]; }
  *walk() { yield this; for (const k of this.kids) if (k instanceof El) yield* k.walk(); }
  querySelectorAll(sel) {
    const m = sel.match(/^\[(data-[\w-]+)(?:="([^"]*)")?\]$/);
    if (m) return [...this.walk()].filter((e) => m[1] in e.attrs && (m[2] === undefined || e.attrs[m[1]] === m[2]));
    if (sel.startsWith("button")) return [...this.walk()].filter((e) => e.tag === "button" && e.id !== "p-close");
    return [];
  }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
  focus() {} showModal() { this.open = true; } close() { this.open = false; }
}
const byId = {};
global.document = {
  hidden: false, documentElement: new El("html"), body: new El("body"),
  createElement: (t) => new El(t), createTextNode: (s) => new Txt(s),
  getElementById: (id) => (byId[id] ||= Object.assign(new El("div"), { id })),
  querySelector: (sel) => { for (const e of Object.values(byId)) { const r = e.querySelector(sel); if (r) return r; } return null; },
  querySelectorAll: (sel) => (sel === "dialog" ? Object.values(byId).filter((e) => "open" in e && e.open && ["panel", "custom", "ql", "settings", "history", "resources", "bulk"].includes(e.id)) : []),
};
global.Node = El;
const docOuvintes = {};
document.addEventListener = (e, f) => { docOuvintes[e] = f; };
global.window = { open: (...a) => { (global.abertos ||= []).push(a); } };
const guardado = new Map();
global.localStorage = { getItem: (k) => (k === "qh-lang" ? "pt" : guardado.has(k) ? guardado.get(k) : null), setItem: (k, v) => guardado.set(k, String(v)) };
global.navigator = { language: "pt-BR" };
global.location = {};
global.setInterval = () => 0;
// A stand-in for EventSource: the test pushes lines by hand.
const fontes = [];
const sockets = [];
global.WebSocket = class { constructor(url) { this.url = url; this.readyState = 1; this.sent = []; sockets.push(this); }
  send(d) { this.sent.push(JSON.parse(d)); } close() { this.readyState = 3; this.closed = true; } };
global.EventSource = class { constructor(url) { this.url = url; this.closed = false; fontes.push(this); } close() { this.closed = true; } };

const unidade = (nome, extra = {}) => ({ unit: nome, image: "x:1", installed_image: "x:1", installed: true,
  service: "active", container: "healthy", drift: null, override: false, ...extra });
const base = { screenshots: ["https://img.example/a.png", "https://img.example/b.png"], id: "homebox", name: "Homebox", icon: "i.svg",
  group: { en: "Home", pt: "Casa" }, description: { en: "x", pt: "y" }, main_unit: "homebox", installed: true,
  has_login: false, has_env: true, access: { mode: "tailnet", exception: null }, requires: [], asks: { secrets: [], vars: [] },
  web: [{ unit: "homebox", local: null, tailnet: null }], units: [unidade("homebox")] };
const gitea = { ...base, screenshots: [], id: "gitea", name: "Gitea", group: { en: "Tools", pt: "Ferramentas" }, main_unit: "gitea",
  installed: false, has_env: false, web: [], units: [unidade("gitea", { installed: false, installed_image: null, service: null, container: null })] };
const memos = { ...base, id: "memos", name: "Memos", group: { en: "Productivity", pt: "Produtividade" }, main_unit: "memos",
  screenshots: [], has_env: false, web: [{ unit: "memos", local: null, tailnet: "https://memos.example.ts" }], units: [unidade("memos")] };

const posts = [];
const rotas = {
  "/api/catalog": { access: "tailnet", apps: [base, gitea, memos] },
  "/api/updates": { checked: null, rows: [] },
  "/api/stats": { stats: { homebox: { cpu: 1.5, mem: 150 * 1048576 } } },
  "/api/disk": { bytes: 5 * 1048576, paths: [] },
  "/api/arch": { host: "arm64", runs: ["amd64"], units: [{ unit: "homebox", ok: false }] },
  "/api/links": { links: [{ kind: "repo", url: "https://github.com/o/r" }, { kind: "docs", url: "https://docs.example.org/r" },
    { kind: "issues", url: "https://github.com/o/r/issues" }, { kind: "releases", url: "https://github.com/o/r/releases" },
    { kind: "recipe", url: "https://github.com/me/qh/tree/main/apps/homebox" }] },
  "/api/history": { entries: [
    { id: "a1", app: "homebox", action: "install", unit: "", start: 1700000000, end: 1700000042, rc: 0, from: "127.0.0.1" },
    { id: "a2", app: "homebox", action: "restart", unit: "homebox", start: 1700000100, end: 1700000101, rc: 1, from: "127.0.0.1" },
    { id: "a3", app: "homebox", action: "update", unit: "", start: 1700000200, end: 1700000300, rc: 1, from: "127.0.0.1", rolled_back: true }] },
  "/api/history/a2": { id: "a2", app: "homebox", action: "restart", unit: "homebox", rc: 1, from: "127.0.0.1", output: "Job failed\n" },
  "/api/env": { files: [{ file: "homebox.env", units: ["homebox"], entries: [
    { key: "TZ", value: "UTC", active: true, help: "Time zone", sensitive: false },
    { key: "PORT", value: "8080", active: false, help: "", sensitive: false },
    { key: "API_TOKEN", value: "s3cret", active: true, help: "", sensitive: true }] }] },
  "/api/custom": { unit: "homebox", file: "~/x/homebox.container.d/50-store.conf", override: false, text: null, base_changed: false,
    base: {}, base_restart: "always", restart: "always", restarts: ["always", "on-failure", "no"], roots: ["~/.config/containers/volumes"],
    caps_ok: ["CHOWN", "KILL", "NET_RAW"], quadlet: true, limits: { memory: false, cpu: false },
    effective: { ports: [{ bind: "", host: 8085, container: 3000, proto: "tcp" }, { raw: "${DNS}:53:53/udp", opaque: true }],
      volumes: [{ host: "%h/a", container: "/a", label: "Z", ro: false, extra: [] }, { host: "%h/b", container: "/b", label: "z", ro: true, extra: [] }],
      env: [{ key: "TZ", value: "UTC" }], devices: [], caps: [{ name: "CHOWN" }] } },
  "/api/custom/preview": { errors: [], warnings: ["uma porta publicada abre o app na rede local"], text: "[Container]\nPublishPort=\n", generated: "podman run x", changed: true },
  "/api/custom/apply": { job: "j1" }, "/api/custom/reset": { job: "j1" },
  "/api/job/j1": { rc: 0, next: 0, output: "" },
  "/api/env/save": { job: "j1" },
};
global.fetch = async (url, opts = {}) => {
  let rota = url.split("?")[0];
  if (rota.startsWith("/api/history/") && !(rota in rotas)) rota = "/api/history/a2";
  if (opts.method === "POST") posts.push({ rota, corpo: (() => { try { return JSON.parse(opts.body); } catch (e) { return opts.body; } })(), url });
  if (!(rota in rotas)) return { status: 404, ok: false, json: async () => ({ error: "404 " + rota }) };
  return { status: 200, ok: true, json: async () => rotas[rota] };
};

const codigo = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const api = new Function(codigo + "; return { S, openPanel, showEnv, current, renderGrid, pollStats, pollHost, openSettings, showLogs, showConsole, termNew, termFeed, termKey, openResources, hintClean, openHistory, setView, openFiles, renderFiles, uploadFiles, jobProgress, stepLabel, instalar, pollJobs, pollPerf, iconPlate, renderHome, touchRecent };")();
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
let falhas = 0;
const confere = (cond, msg) => { if (!cond) { falhas++; console.log("FALHOU:", msg); } else console.log("ok   ", msg); };
const $ = (id) => document.getElementById(id);
const botoes = (raiz) => [...raiz.walk()].filter((e) => e.tag === "button");
const porTexto = (raiz, texto) => botoes(raiz).filter((e) => e.textContent === texto);
// An installed app's changes live in the Configure tab: open it, then find the row's button.
const cfgBtn = async (texto) => { porTexto($("p-tabs"), "Configurar")[0].listeners.click(); await esperar(30); return porTexto($("p-section"), texto)[0]; };
// The customize sheet: in the fake DOM the dialog does not contain its parts, so they are read as one.
const folhaC = { *walk() { for (const i of ["c-tabs", "c-body", "c-foot"]) yield* $(i).walk(); },
  get textContent() { return ["c-title", "c-tabs", "c-body", "c-foot"].map((i) => $(i).textContent).join(" "); } };

(async () => {
  await esperar(100);
  const azulejo = [...$("grid").walk()].find((e) => e.attrs && e.attrs.class === "card tile");
  confere(azulejo && !/MB|%/.test(azulejo.textContent) && !document.querySelector('[data-res="homebox"]'), `o azulejo não mostra recursos (${azulejo && azulejo.textContent})`);
  // The tile is the icon and the name: no dot, no arrow, no state words. The state and the update live in the right-click menu.
  const menuCtx = (tileEl) => { tileEl.listeners.contextmenu({ preventDefault() {}, stopPropagation() {}, clientX: 20, clientY: 20 }); return $("ctx"); };
  const tilesDaGrade = () => [...$("grid").walk()].filter((e) => e.attrs && e.attrs.class === "card tile");
  confere(azulejo && ![...azulejo.walk()].some((e) => e.attrs && /(^| )(dot|upd)( |$)/.test(e.attrs.class || "")) && !/rodando|parado|pausado|nova versão/.test(azulejo.textContent),
    `o azulejo não mostra bolinha, seta nem estado (${azulejo && azulejo.textContent})`);
  const doHomebox = () => tilesDaGrade().find((e) => /Homebox|HomeBox/i.test(e.textContent));
  confere(/rodando/.test(menuCtx(doHomebox()).textContent), "o botão direito mostra o estado");

  // the panel of an installed app: resources, disk, architectures, and no stray "null"
  api.openPanel("homebox"); await esperar(100);
  const info = $("p-info").textContent;
  confere(!/CPU|Memória/.test(info) && /Disco 5 MB/.test(info), `painel: só o disco, sem CPU nem memória (${info})`);
  confere(/Roda em amd64/.test(info) && /Sem imagem para arm64: homebox/.test(info), "painel: arquiteturas, com aviso quando o host não é suportado");
  confere(!/null|undefined|false/.test(info), "painel: nenhum 'null' no texto");
  confere(!/null|undefined|false/.test($("p-actions").textContent), "botões: nenhum 'null' solto");

  // the .env form
  await api.showEnv(api.current());
  const form = [...$("p-section").walk()].find((e) => e.tag === "form");
  const campo = (id) => [...$("p-section").walk()].find((e) => e.id === id);
  const [tz, port, tok] = ["e-homebox.env-0", "e-homebox.env-1", "e-homebox.env-2"].map(campo);
  confere(form && tz.attrs.type === "text" && tok.attrs.type === "password", "formulário do .env: chave sensível vira campo de senha");
  confere(port.disabled && !tz.disabled, "opção comentada começa desligada");
  const caixaPort = campo("e-homebox.env-1-on"), caixaTz = campo("e-homebox.env-0-on");
  caixaPort.checked = true; caixaPort.onchange(); port.value = "9090"; caixaTz.checked = false;
  await form.onsubmit({ preventDefault() {} });
  const envio = posts.find((p) => p.rota === "/api/env/save");
  confere(envio && JSON.stringify(envio.corpo.set) === '{"PORT":"9090"}' && JSON.stringify(envio.corpo.off) === '["TZ"]',
    "só o que mudou é enviado");
  confere(!JSON.stringify(envio.corpo).includes("s3cret"), "o valor que não mudou não vai junto");

  // typed settings: the right box for each, and what goes back follows the file's own style
  const envAntes = rotas["/api/env"];
  rotas["/api/env"] = { files: [{ file: "t.env", units: ["homebox"], entries: [
    { key: "CORES", value: "2", active: true, help: "", sensitive: false, type: "number" },
    { key: "RAM", value: "4G", active: true, help: "", sensitive: false, type: "number" },
    { key: "GPU", value: "Y", active: true, help: "", sensitive: false, type: "bool", bool: ["Y", "N"] },
    { key: "MAIL", value: "a@b.co", active: true, help: "", sensitive: false, type: "email" },
    { key: "HOME_URL", value: "http://x:1", active: true, help: "", sensitive: false, type: "url" },
    { key: "ADDR", value: "10.0.0.1", active: true, help: "", sensitive: false, type: "ip" },
    { key: "PW", value: "x", active: true, help: "", sensitive: true, type: "password" }] }] };
  await api.showEnv(api.current());
  const tf = [...$("p-section").walk()].find((e) => e.tag === "form");
  const tc = (id) => [...$("p-section").walk()].find((e) => e.id === id);
  const tipos = [0, 1, 2, 3, 4, 5, 6].map((i) => tc(`e-t.env-${i}`).attrs.type).join(",");
  confere(tipos === "number,text,checkbox,email,url,text,password", `formulário tipado: a caixa de cada tipo (${tipos})`);
  confere(tc("e-t.env-2").attrs.checked !== undefined, "bool: Y vem marcado");
  confere(/número/.test(tf.textContent) && /sim\/não/.test(tf.textContent), "o tipo aparece ao lado do campo");
  tc("e-t.env-2").checked = false;
  tc("e-t.env-0").value = "4";
  await tf.onsubmit({ preventDefault() {} });
  const tipado = posts.filter((x) => x.rota === "/api/env/save").pop().corpo;
  confere(JSON.stringify(tipado.set) === '{"CORES":"4","GPU":"N"}', `o bool volta no estilo do arquivo (Y/N), só o que mudou (${JSON.stringify(tipado.set)})`);
  rotas["/api/env"] = envAntes;
  $("p-section").hidden = true;

  // the manager's tabs: Summary is the default; Backups opens in place; the danger zone holds Remove
  confere(!$("p-tabs").hidden && botoes($("p-tabs")).map((b) => b.textContent).join("|").startsWith("Resumo|Configurar"), "gerenciar: abas Resumo, Configurar…");
  confere(botoes($("p-actions")).every((b) => !["Remover", "Personalizar", "Backups", "Configurar"].includes(b.textContent)), "gerenciar: o topo só tem o uso diário");
  porTexto($("p-tabs"), "Backups")[0].listeners.click(); await esperar(50);
  confere(!$("p-section").hidden, "a aba Backups abre no próprio painel");
  porTexto($("p-tabs"), "Resumo")[0].listeners.click(); await esperar(20);
  confere($("p-section").hidden, "a aba Resumo volta ao resumo");

  // the links at the end of the store page, each named
  { const hb = api.S.apps.find((x) => x.id === "homebox"); const antes = { ...hb };
    Object.assign(hb, { installed: false, website: "https://site.example/", source: "https://github.com/o/r", docs: "https://docs.example/d", demo: "https://demo.example/", video: "https://youtube.com/watch?v=x" });
    api.openPanel("homebox"); await esperar(60);
    const txt = $("p-project").textContent;
    confere(/Site/.test(txt) && /Repositório no GitHub/.test(txt) && /Documentação/.test(txt) && /Demonstração/.test(txt) && /Vídeo/.test(txt) && /github\.com\/o\/r/.test(txt), `loja: links nomeados no fim (${txt})`);
    for (const k of ["website", "source", "docs", "demo", "video"]) delete hb[k];
    hb.installed = antes.installed; api.openPanel("homebox"); await esperar(30); }

  // Cancel: shown while the install runs, asks the server to stop, and the window says it was cancelled
  { const hb = api.S.apps.find((x) => x.id === "homebox"); hb.installed = false; hb.asks = { secrets: [], vars: [] }; hb.options = [];
    const runAntes = rotas["/api/run"], planoAntes = rotas["/api/plan"];
    rotas["/api/plan"] = { rc: 0, output: "x", nothing: false };
    rotas["/api/run"] = { job: "jc" }; rotas["/api/job/jc"] = { rc: null, next: 1, output: "homebox: instalação, 2 passos\n  -> mkdir -p /h\n  -> podman pull x\n[1/2] mkdir -p /h\n", cancelled: false };
    const fim = api.instalar("homebox"); await esperar(1000);
    confere(!$("i-cancel").hidden && $("i-cancel").textContent === "Cancelar", "instalando: o botão Cancelar aparece");
    rotas["/api/job/jc/cancel"] = { cancelled: true };
    const antesC = posts.length;
    $("i-cancel").onclick(); await esperar(30);
    confere(posts.slice(antesC).some((x) => x.rota === "/api/job/jc/cancel") && $("i-cancel").disabled, "Cancelar pede ao servidor para parar");
    rotas["/api/job/jc"] = { rc: 130, next: 2, output: "\nCancelado.\n", cancelled: true };
    await fim; await esperar(30);
    confere($("i-result").textContent === "Instalação cancelada" && $("i-cancel").hidden, "ao terminar cancelado: 'Instalação cancelada' e sem o botão");
    $("install").open = false;
    if (runAntes === undefined) delete rotas["/api/run"]; else rotas["/api/run"] = runAntes;
    if (planoAntes === undefined) delete rotas["/api/plan"]; else rotas["/api/plan"] = planoAntes;
    delete rotas["/api/job/jc"]; delete rotas["/api/job/jc/cancel"]; hb.installed = true; }

  // removal with the data: Confirm stays off until the name is typed
  { const hb = api.S.apps.find((x) => x.id === "homebox"); hb.installed = true;
    api.openPanel("homebox"); await esperar(30);
    const planoR = rotas["/api/plan"]; rotas["/api/plan"] = { rc: 0, output: "x", nothing: false };
    porTexto($("p-danger"), "Remover")[0].listeners.click(); await esperar(80);
    const ok = porTexto($("p-form"), "Confirmar")[0];
    const marca = [...$("p-form").walk()].find((e) => e.attrs["data-purge"]);
    const nome = [...$("p-form").walk()].find((e) => e.attrs["data-confirm"]);
    confere(ok && !ok.disabled, "remover sem apagar os dados: Confirmar liberado");
    marca.checked = true; marca.listeners.change({ target: marca });
    confere(ok.disabled === true, "apagar os dados: Confirmar fica desligado até digitar o nome");
    nome.value = "homebox"; nome.listeners.input();
    confere(ok.disabled === false, "com o nome digitado, Confirmar libera");
    nome.value = "outro"; nome.listeners.input();
    confere(ok.disabled === true, "nome errado: continua desligado");
    if (planoR === undefined) delete rotas["/api/plan"]; else rotas["/api/plan"] = planoR;
    $("p-form").hidden = true; }

  // "Install" installs at once when nothing has to be asked
  { const hb = api.S.apps.find((x) => x.id === "homebox"); hb.installed = false; hb.asks = { secrets: [], vars: [] }; hb.options = [];
    const planoAntes = rotas["/api/plan"]; rotas["/api/plan"] = { rc: 0, output: "x", nothing: false };
    const antesI = posts.length;
    await api.instalar("homebox"); await esperar(100);
    const r = posts.slice(antesI).find((x) => x.rota === "/api/run");
    confere(r && r.corpo.action === "install" && r.corpo.app === "homebox", `Instalar instala de uma vez, sem segunda confirmação (${posts.slice(antesI).map((x) => x.rota)} | form ${$("p-form").hidden} | ${$("p-form").kids.length})`);
    if (planoAntes === undefined) delete rotas["/api/plan"]; else rotas["/api/plan"] = planoAntes;
    hb.installed = true; }

  // gallery, project links, history
  const shots = $("p-shots");
  // the arrow inside the Install pill: opens a menu with one entry, the custom install
  api.S.apps.find((x) => x.id === "homebox").installed = false;
  api.openPanel("homebox"); await esperar(30);
  const menuI = [...$("p-actions").walk()].find((e) => e.attrs.class === "split-menu");
  const setaI = [...$("p-actions").walk()].find((e) => e.attrs.class === "split-arrow");
  confere(menuI.hidden === true, "o menu da setinha começa fechado");
  setaI.listeners.click({ stopPropagation() {} });
  confere(menuI.hidden === false && setaI.attrs["aria-expanded"] === "true", "a setinha abre o menu");
  confere(botoes(menuI).map((b) => b.textContent).join("|") === "Instalação personalizada…", "o menu só tem a instalação personalizada (tudo está nela)");
  api.S.apps.find((x) => x.id === "homebox").installed = true;
  // the lightbox
  api.S.apps.find((x) => x.id === "homebox").installed = false;
  api.openPanel("homebox"); await esperar(30);
  const primeira = [...$("p-shots").walk()].find((e) => e.tag === "a");
  let prevenido = false;
  primeira.listeners.click({ preventDefault() { prevenido = true; } }); await esperar(10);
  confere($("lightbox").open && prevenido && $("lb-img").src === "https://img.example/a.png" && $("lb-count").textContent === "1 / 2", "clicar numa captura abre o lightbox na imagem certa");
  $("lb-next").listeners.click(); await esperar(5);
  confere($("lb-img").src === "https://img.example/b.png" && $("lb-count").textContent === "2 / 2", "seta para a direita: próxima captura");
  $("lb-next").listeners.click(); await esperar(5);
  confere($("lb-img").src === "https://img.example/a.png", "depois da última volta à primeira");
  $("lightbox").listeners.keydown({ key: "ArrowLeft", preventDefault() {} }); await esperar(5);
  confere($("lb-img").src === "https://img.example/b.png", "tecla ←: captura anterior");
  $("lb-close").listeners.click(); confere(!$("lightbox").open, "o ✕ fecha o lightbox");
  confere([...$("p-shots").walk()].filter((e) => e.tag === "button").length === 2, "a galeria tem uma seta de cada lado");
  api.S.apps.find((x) => x.id === "homebox").installed = true;
  api.openPanel("homebox"); await esperar(30);
  confere(shots.hidden, "gerenciar (instalado): sem capturas de tela");
  const homebox = api.S.apps.find((x) => x.id === "homebox");
  homebox.installed = false; homebox.about = { en: "long about", pt: "sobre longo" };
  api.openPanel("homebox"); await esperar(30);
  confere(!shots.hidden && [...shots.walk()].filter((e) => e.tag === "img").length === 2, "loja (não instalado): galeria com duas capturas");
  confere([...shots.walk()].filter((e) => e.tag === "a").every((a) => a.attrs.target === "_blank" && /noopener/.test(a.attrs.rel)), "galeria: outra aba, com noopener");
  confere(/sobre longo/.test($("p-desc").textContent), "loja: mostra a descrição longa");
  homebox.installed = true;
  api.openPanel("homebox"); await esperar(30);
  confere(!/sobre longo/.test($("p-desc").textContent) && $("p-desc").textContent === "y", "gerenciar: só a descrição curta");
  delete homebox.about;
  confere(/Projeto ↗/.test($("p-project").textContent) && /Releases ↗/.test($("p-project").textContent), "links do projeto");
  const ancorasProjeto = [...$("p-project").walk()].filter((e) => e.tag === "a");
  confere(ancorasProjeto.map((a) => a.textContent).slice(0, 3).join("|") === "Projeto ↗|Documentação ↗|Problemas ↗",
    `links: Projeto, Documentação e Problemas, nessa ordem (${ancorasProjeto.map((a) => a.textContent).join("|")})`);
  confere(ancorasProjeto.find((a) => /Problemas/.test(a.textContent)).attrs.href === "https://github.com/o/r/issues"
    && ancorasProjeto.every((a) => a.attrs.target === "_blank" && /noopener/.test(a.attrs.rel)), "Problemas leva às issues, e todos abrem em outra aba com noopener");
  await api.openHistory("homebox"); await esperar(50);
  const linhasHist = [...$("h-list").walk()].filter((e) => e.tag === "tr" && e.attrs.class === "run");
  confere($("history").open && linhasHist.length === 3 && /✓/.test(linhasHist[0].textContent) && /✗ 1/.test(linhasHist[1].textContent) && /voltou à versão anterior/.test(linhasHist[2].textContent) && !/voltou/.test(linhasHist[1].textContent), "histórico: linhas com o resultado, e a que voltou à versão anterior");
  await linhasHist[1].onclick();
  confere(/Job failed/.test($("h-out").textContent) && /de 127\.0\.0\.1/.test($("h-out").textContent), "histórico: a saída e de onde veio");
  $("history").open = false;

  // an app that is not installed, and a host the image supports
  rotas["/api/host"] = { cpus: 4, load: 1, mem: { total: 8 * 2 ** 30, used: 2 * 2 ** 30 }, temp: 50, uptime: 90000,
    cpu: { pct: 12.4, cpus: 4, load: 1 }, disk: { total: 100 * 2 ** 30, used: 91 * 2 ** 30 }, net: { rx: 5 * 2 ** 30, tx: 2 ** 30, rx_rate: 1572864, tx_rate: 2048 } };
  // a job running on the server shows as a chip; clicking it reopens the window with everything printed so far
  rotas["/api/jobs/active"] = { job: { id: "j9", app: "_host", action: "update-all" } };
  rotas["/api/job/j9"] = { app: "_host", action: "update-all", rc: 0, next: 2, output: "=== [1/2] memos ===\nok\n" };
  await api.pollJobs(); await esperar(20);
  confere(!$("job-chip").hidden && /update-all/.test($("job-chip").textContent), `chip do job em andamento (${$("job-chip").textContent})`);
  $("job-chip").onclick(); await esperar(60);
  confere($("bulk").open && /=== \[1\/2\] memos ===/.test($("b-out").textContent), "reabrir a janela mostra o log desde o começo");
  $("bulk").open = false;
  rotas["/api/jobs/active"] = { job: null }; await api.pollJobs();
  confere($("job-chip").hidden, "sem job, sem chip");

  // the server numbers live on the home: one reading fills the tiles
  await api.pollPerf(); await esperar(20);
  confere(/12%/.test($("home").textContent) && /25%/.test($("home").textContent) && /91%/.test($("home").textContent), `início: processador, memória e disco (${$("home").textContent.slice(0, 120)})`);
  confere(/↓ 1\.5 MB\/s/.test($("home").textContent), "início: taxa de rede");

  rotas["/api/arch"] = { host: "amd64", runs: ["amd64", "arm64"], download: 38617327, version: "1.20.26", units: [{ unit: "homebox", ok: true }] };
  api.openPanel("gitea"); await esperar(100);
  confere(botoes($("p-actions")).map((b) => b.textContent).join("") === "InstalarInstalação personalizada…" && $("p-tech").hidden && /Categoria/.test($("p-actions").textContent), `app não instalado: só Instalar e Personalizar (sem histórico, instância nem detalhes técnicos), e o cartão com a categoria (${$("p-actions").textContent})`);
  confere(!/null|undefined/.test($("p-info").textContent + $("p-actions").textContent) && /Arquitetura\s*amd64, arm64/.test($("p-actions").textContent) && /Download\s*37 MB/.test($("p-actions").textContent) && /Versão\s*1\.20\.26/.test($("p-actions").textContent) && !/Roda em/.test($("p-info").textContent), "app não instalado: tamanho e arquitetura vão no cartão, e nada de 'null'");
  $("panel").open = false;

  // discontinued: the badge, the reason in the page's language, and no install for what is not installed
  const marca = { en: "Archived upstream.", pt: "Arquivado no upstream." };
  api.S.apps.find((x) => x.id === "gitea").deprecated = marca;
  api.S.apps.find((x) => x.id === "memos").deprecated = marca;
  api.setView("store");
  const cartaoGitea = $("grid").kids.find((k) => /Gitea/.test(k.textContent));
  confere(/descontinuado/.test(cartaoGitea.textContent) && !/instalado/.test(cartaoGitea.textContent.replace("descontinuado", "")),
    "Loja: o cartão de um app descontinuado leva o selo");
  api.openPanel("gitea"); await esperar(50);
  confere(!$("p-notice").hidden && /Descontinuado: Arquivado no upstream\./.test($("p-notice").textContent) && /Não dá para instalar/.test($("p-notice").textContent),
    "painel: o motivo, em português, e o aviso de que não instala");
  confere(botoes($("p-actions")).length === 0, `painel: sem botão de instalar (${$("p-actions").textContent})`);
  $("panel").open = false;
  api.setView("apps");
  const azulejoMemos = $("grid").kids.find((k) => /Memos/.test(k.textContent));
  confere(/descontinuado/.test(azulejoMemos.textContent), "Meus apps: o azulejo de um instalado também leva o selo");
  api.openPanel("memos"); await esperar(50);
  confere(/Descontinuado: Arquivado no upstream\./.test($("p-notice").textContent) && !/Não dá para instalar/.test($("p-notice").textContent),
    "instalado: mostra o motivo, sem dizer que não instala");
  confere(botoes($("p-danger")).some((b) => b.textContent === "Remover"), "instalado: continua dando para gerenciar e remover");
  $("panel").open = false;
  api.openPanel("homebox"); await esperar(50);
  confere($("p-notice").hidden === true, "um app sem marca não mostra aviso");
  $("panel").open = false;
  api.S.apps.find((x) => x.id === "gitea").deprecated = null;
  api.S.apps.find((x) => x.id === "memos").deprecated = null;

  // host summary: one line at the top
  await api.pollHost();
  confere($("host").textContent === "carga 25% · RAM 2.0/8.0 GB · 50 °C · ligado há 1 d", `topo: resumo do servidor (${$("host").textContent})`);

  // files: a manager. Apps first, then volumes and folders; select, create, copy/cut/paste, rename, delete (asked twice), upload, edit
  rotas["/api/files"] = { path: "", entries: [{ name: "memos", type: "dir", size: null, mtime: null }], truncated: false };
  await api.openFiles(""); await esperar(30);
  confere($("files").open && /Memos/.test($("f-body").textContent) && /Escolha uma pasta/.test($("f-body").textContent) && porTexto($("f-bar"), "Enviar").length === 0, "Arquivos: começa pelos apps, sem poder alterar ali");
  rotas["/api/files"] = { path: "memos/memos/data", entries: [{ name: "sub", type: "dir", size: null, mtime: 1 }, { name: "a.txt", type: "file", size: 6, mtime: 1 },
    { name: "p.png", type: "file", size: 9, mtime: 1 }, { name: "b.bin", type: "file", size: 2, mtime: 1 }, { name: "pw", type: "link", size: null, mtime: 1 }], truncated: false };
  await api.openFiles("memos/memos/data"); await esperar(30);
  const trocas = [...$("f-crumb").walk()].filter((e) => e.tag === "button").map((e) => e.textContent);
  confere(trocas.join("|") === "Apps|Memos|memos|data", `Arquivos: o caminho vira migalhas (${trocas})`);
  confere(porTexto($("f-bar"), "Enviar").length === 1 && porTexto($("f-bar"), "Nova pasta").length === 1 && porTexto($("f-bar"), "Apagar").length === 0 && /Mexer nos arquivos de um app que está rodando/.test($("f-body").textContent), "numa pasta de app: enviar e nova pasta; apagar só com seleção; o aviso sobre app rodando");
  const caixa = (n) => [...$("f-body").walk()].find((e) => e.tag === "input" && e.attrs.type === "checkbox" && e.attrs["aria-label"] === n);
  const linhaF = (n) => [...$("f-body").walk()].find((e) => e.tag === "button" && e.attrs.class && /fname/.test(e.attrs.class) && e.textContent.includes(n));
  confere(linhaF("pw").attrs.disabled !== undefined, "um atalho (link) não se abre");
  const marcar = async (n, v = true) => { const c = caixa(n); c.checked = v; c.listeners.change(); await esperar(30); };
  await marcar("a.txt");
  confere(/1 selecionado/.test($("f-bar").textContent) && ["Copiar", "Recortar", "Renomear", "Apagar"].every((x) => porTexto($("f-bar"), x).length === 1), "marcar um arquivo: copiar, recortar, renomear e apagar");
  await marcar("sub");
  confere(/2 selecionados/.test($("f-bar").textContent) && porTexto($("f-bar"), "Renomear").length === 0, "com dois marcados, não se renomeia");
  // new folder: asks the name, then posts
  rotas["/api/files/op"] = { name: "docs" };
  const antes1 = posts.length;
  porTexto($("f-bar"), "Nova pasta")[0].listeners.click();
  const nomeIn = [...$("f-bar").walk()].find((e) => e.tag === "input");
  nomeIn.value = "docs"; porTexto($("f-bar"), "OK")[0].listeners.click(); await esperar(40);
  const mk = posts.slice(antes1).find((x) => x.rota === "/api/files/op");
  confere(mk && mk.corpo.op === "mkdir" && mk.corpo.path === "memos/memos/data" && mk.corpo.name === "docs", "nova pasta: pergunta o nome e envia mkdir");
  // copy and paste into another folder
  api.S.fsel = new Set(["a.txt"]); await api.renderFiles("memos/memos/data");
  porTexto($("f-bar"), "Copiar")[0].listeners.click(); await esperar(30);
  confere(api.S.fclip && api.S.fclip.mode === "copy" && api.S.fclip.paths[0] === "memos/memos/data/a.txt" && porTexto($("f-bar"), "Colar (1)").length === 1, "copiar guarda na área e oferece Colar");
  const antes2 = posts.length;
  porTexto($("f-bar"), "Colar (1)")[0].listeners.click(); await esperar(40);
  const cp = posts.slice(antes2).find((x) => x.rota === "/api/files/op");
  confere(cp && cp.corpo.op === "copy" && cp.corpo.path === "memos/memos/data/a.txt" && cp.corpo.to === "memos/memos/data" && api.S.fclip, "colar: envia copy para a pasta aberta e guarda a área (copiar)");
  // rename one
  api.S.fsel = new Set(["a.txt"]); api.S.fclip = null; await api.renderFiles("memos/memos/data");
  const antes3 = posts.length;
  porTexto($("f-bar"), "Renomear")[0].listeners.click();
  const novoIn = [...$("f-bar").walk()].find((e) => e.tag === "input");
  confere(novoIn.value === "a.txt", "renomear: já vem com o nome atual");
  novoIn.value = "b.txt"; porTexto($("f-bar"), "OK")[0].listeners.click(); await esperar(40);
  const rn = posts.slice(antes3).find((x) => x.rota === "/api/files/op");
  confere(rn && rn.corpo.op === "rename" && rn.corpo.path === "memos/memos/data/a.txt" && rn.corpo.name === "b.txt", "renomear envia rename");
  // delete: the first click only asks, the second deletes each one selected
  api.S.fsel = new Set(["a.txt", "sub"]); await api.renderFiles("memos/memos/data");
  const antes4 = posts.length;
  porTexto($("f-bar"), "Apagar")[0].listeners.click();
  confere(posts.length === antes4 && porTexto($("f-bar"), "Confirmar: apagar 2 itens").length === 1, "apagar: o primeiro clique só pede confirmação");
  porTexto($("f-bar"), "Confirmar: apagar 2 itens")[0].listeners.click(); await esperar(60);
  const dels = posts.slice(antes4).filter((x) => x.rota === "/api/files/op" && x.corpo.op === "delete").map((x) => x.corpo.path);
  confere(dels.join(",") === "memos/memos/data/sub,memos/memos/data/a.txt", `apagar: o segundo clique apaga cada selecionado (${dels})`);
  // upload: one request per file, with the name and the folder
  rotas["/api/files/upload"] = { name: "n.txt" };
  const antes5 = posts.length;
  await api.uploadFiles([{ name: "n.txt", size: 3 }, { name: "ç é.bin", size: 1 }], "memos/memos/data"); await esperar(40);
  const ups = posts.slice(antes5).filter((x) => x.rota === "/api/files/upload").map((x) => decodeURIComponent(x.url));
  confere(ups.length === 2 && ups[0].includes("path=memos/memos/data&name=n.txt") && ups[1].includes("name=ç é.bin") && /Enviados?|2 enviados/.test($("f-body").textContent), `enviar: um pedido por arquivo (${ups})`);
  const antes6 = posts.length;
  await api.uploadFiles([{ name: "x" }], "memos"); await api.uploadFiles([{ name: "x" }], "");
  confere(posts.length === antes6, "não se envia onde não é pasta de app");
  // preview and edit a text file; an image shows inline; a binary only downloads
  rotas["/api/files/preview"] = { text: "olá\n", size: 6, truncated: false };
  api.S.fsel = new Set(); await api.renderFiles("memos/memos/data");
  linhaF("a.txt").listeners.click(); await esperar(40);
  const area = [...$("f-body").walk()].find((e) => e.tag === "textarea");
  confere(area && area.value === "olá\n" && [...$("f-body").walk()].some((e) => e.tag === "a" && /files\/download\?path=memos%2Fmemos%2Fdata%2Fa\.txt/.test(e.attrs.href)), "texto: editor e link de download");
  area.value = "novo\n";
  const antes7 = posts.length;
  porTexto($("f-body"), "Salvar")[0].listeners.click(); await esperar(40);
  const sv = posts.slice(antes7).find((x) => x.rota === "/api/files/upload");
  confere(sv && sv.corpo === "novo\n" && /overwrite=1/.test(sv.url) && /name=a\.txt/.test(sv.url) && /Salvo/.test($("f-state").textContent), "salvar: envia por cima do mesmo arquivo");
  await api.renderFiles("memos/memos/data");
  linhaF("p.png").listeners.click(); await esperar(30);
  const img = [...$("f-body").walk()].find((e) => e.tag === "img");
  confere(img && /files\/download\?path=memos%2Fmemos%2Fdata%2Fp\.png&inline=1/.test(img.attrs.src), "imagem: aparece no painel");
  await api.renderFiles("memos/memos/data");
  linhaF("b.bin").listeners.click(); await esperar(30);
  confere($("f-view").hidden, "sem prévia, a área do texto some");
  // the units and the .env files: to look at, not to change
  rotas["/api/files"] = { path: "@env", entries: [{ name: "memos.env", type: "file", size: 12, mtime: 1 }], truncated: false };
  api.S.fsel = new Set(); await api.renderFiles("@env");
  confere(porTexto($("f-bar"), "Enviar").length === 0 && porTexto($("f-bar"), "Nova pasta").length === 0 && /Somente leitura/.test($("f-body").textContent)
    && ![...$("f-body").walk()].some((e) => e.tag === "input" && e.attrs.type === "checkbox"), "@env: sem enviar, sem criar, sem seleção; diz que é só leitura");
  const antesRo = posts.length;
  await api.uploadFiles([{ name: "x" }], "@env");
  confere(posts.length === antesRo && [...$("f-crumb").walk()].some((e) => e.tag === "button" && e.textContent === "Variáveis (.env)"), "@env: não se envia, e tem nome legível");
  // an app level (its volumes) is only a list
  rotas["/api/files"] = { path: "memos", entries: [{ name: "memos", type: "dir", size: null, mtime: null }], truncated: false };
  await api.renderFiles("memos");
  confere(porTexto($("f-bar"), "Enviar").length === 0, "na lista de volumes de um app, nada se altera");
  $("files").open = false;

  // resources: the dialog lists what is unused and prunes in two clicks; volumes want the word
  rotas["/api/resources"] = { reclaimable: 3 * 2 ** 30, networks: [{ name: "stray" }], volumes: [{ name: "vf" }],
    images: [{ id: "i2", name: "docker.io/o/old:1", size: 3 * 2 ** 30, created: 0 }] };
  rotas["/api/prune"] = { job: "j9" };
  rotas["/api/job/j9"] = { output: "removed x\n", next: 1, rc: 0 };
  rotas["/api/usage"] = { at: 1, apps: [{ app: "memos", bytes: 3 * 2 ** 30 }, { app: "homebox", bytes: 4096 }] };
  await api.openResources(); await esperar(30);
  const corpoRec = $("r-body").textContent;
  confere(/Imagens sem uso \(1\)/.test(corpoRec) && /docker\.io\/o\/old:1/.test(corpoRec) && /3\.0 GB/.test(corpoRec) && /Redes sem uso \(1\)/.test(corpoRec) && /Volumes sem uso \(1\)/.test(corpoRec),
    `Recursos: imagens, redes e volumes sem uso (${corpoRec.slice(0, 80)})`);
  confere(/Espaço por app/.test(corpoRec) && /Memos3\.0 GB/.test(corpoRec) && /Homebox4 KB/.test(corpoRec) && /Total3\.0 GB/.test(corpoRec), `Recursos: espaço por app, do maior para o menor (${corpoRec.slice(-120)})`);
  const apagar = porTexto($("r-body"), "Apagar");
  confere(apagar.length === 3, "um Apagar por tipo");
  const antesPrune = posts.length;
  apagar[0].listeners.click();
  confere(posts.length === antesPrune && porTexto($("r-body"), "Confirmar").length === 1, "o primeiro clique só pede confirmação");
  porTexto($("r-body"), "Confirmar")[0].listeners.click(); await esperar(900);
  confere(posts.slice(antesPrune).some((x) => x.rota === "/api/prune" && x.corpo.kind === "images"), "o segundo clique apaga as imagens");
  confere(/removed x/.test($("r-out").textContent), "a saída do trabalho aparece");
  $("resources").open = false;
  // after an update: a hint with the size, and a way in
  api.openPanel("homebox"); await esperar(30);
  await api.hintClean();
  confere(!$("p-clean").hidden && /1 imagem\(ns\) sem uso ocupam até 3\.0 GB/.test($("p-clean").textContent) && porTexto($("p-clean"), "Limpar…").length === 1,
    `depois de atualizar: dica com o tamanho (${$("p-clean").textContent})`);
  $("panel").open = false;

  // backup before updating: a box that shows only when there is data and something to update, and rides along
  const hb = api.S.apps.find((x) => x.id === "homebox");
  Object.assign(hb, { has_data: true });
  hb.units = [unidade("homebox", { drift: "changed", image: "x:2" })];
  api.openPanel("homebox"); await esperar(30);
  confere(!!$("backup-first") && /Backup antes/.test($("p-actions").textContent), "painel: caixa 'Backup antes' ao lado de Atualizar");
  $("backup-first").checked = true;
  const antesBk = posts.length;
  await botoes($("p-actions")).find((b) => /^Atualizar/.test(b.textContent)).listeners.click(); await esperar(30);
  const envioBk = posts.slice(antesBk).find((x) => x.rota === "/api/run");
  confere(envioBk && envioBk.corpo.action === "update" && envioBk.corpo.backup_first === true, `a atualização leva backup_first (${JSON.stringify(envioBk && envioBk.corpo)})`);
  hb.has_data = false;
  api.openPanel("homebox"); await esperar(30);
  confere(!$("backup-first") || !$("p-actions").textContent.includes("Backup antes"), "sem dados: sem a caixa");
  hb.units = [unidade("homebox")];
  $("panel").open = false;

  // live logs: follows the stream, filters what arrived, and lets go when the panel closes
  api.openPanel("homebox"); await esperar(30);
  api.showLogs("homebox");
  const fonte = fontes[fontes.length - 1];
  confere(fonte.url === "/api/logs/stream?unit=homebox", "logs: abre o stream do journal da unit");
  fonte.onopen();
  for (const l of ["nov 15 start ok", "nov 15 ERROR boom", "nov 15 request served"]) fonte.onmessage({ data: l });
  await esperar(250);
  const areaLogs = [...$("p-section").walk()].find((e) => e.attrs && e.attrs.class === "logs");
  confere(areaLogs.textContent.split("\n").length === 3 && /ao vivo/.test($("p-section").textContent), "logs: as linhas chegam, e o estado diz ao vivo");
  const campoFiltro = [...$("p-section").walk()].find((e) => e.tag === "input" && e.attrs.type === "search");
  campoFiltro.value = "error";
  campoFiltro.listeners.input();
  confere(areaLogs.textContent === "nov 15 ERROR boom", `logs: o filtro mostra só o que casa, sem diferenciar maiúsculas (${areaLogs.textContent})`);
  campoFiltro.value = "zzz"; campoFiltro.listeners.input();
  confere(/nenhuma linha casa/.test(areaLogs.textContent), "logs: avisa quando nada casa");
  campoFiltro.value = ""; campoFiltro.listeners.input();
  fonte.onmessage({ data: "nov 15 later" }); await esperar(250);
  confere(areaLogs.textContent.split("\n").length === 4, "logs: continua recebendo depois de mudar o filtro");
  // a repaint still pending when the logs are reopened must not stop the next ones from painting
  fonte.onmessage({ data: "nov 15 pending" });
  api.showLogs("homebox");
  const f2 = fontes[fontes.length - 1];
  f2.onopen(); f2.onmessage({ data: "nov 15 after reopen" }); await esperar(250);
  confere(/after reopen/.test([...$("p-section").walk()].find((e) => e.attrs && e.attrs.class === "logs").textContent), "logs: reabrir com um repaint pendente ainda mostra as linhas");
  api.showLogs("homebox");
  confere(fonte.closed === true && fontes[fontes.length - 1] !== fonte, "logs: abrir outro fecha o stream anterior");
  fontes[fontes.length - 1].onerror();
  confere(/encerrado/.test($("p-section").textContent), "logs: o fim do stream aparece");
  $("panel").open = false;

  // console: the screen engine, the keys, and the WebSocket
  const tm = api.termNew();
  api.termFeed(tm, "$ ls\r\nfile1  \x1b[1;34mdir\x1b[0m\r\n$ ");
  confere(tm.lines.join("|") === "$ ls|file1  dir|$ ", `console: cores e quebras de linha (${tm.lines.join("|")})`);
  api.termFeed(tm, "abc\b\b \bX\r$ Y");
  confere(tm.lines[2] === "$ YXc", `console: backspace apaga, \\r volta ao começo e sobrescreve (${tm.lines[2]})`);
  const t2 = api.termNew();
  api.termFeed(t2, "olá\b \b\b \b");
  api.termFeed(t2, "x\x1b[");           // an escape cut in two
  api.termFeed(t2, "6ny");
  confere(t2.lines[0] === "oxy", `console: uma sequência cortada no meio entre dois pedaços é descartada (${JSON.stringify(t2.lines[0])})`);
  const t3 = api.termNew(); api.termFeed(t3, "a\tb");
  confere(t3.lines[0] === "a       b", "console: tab anda até a próxima coluna de 8");
  const tecla = (key, extra = {}) => api.termKey({ key, ctrlKey: false, altKey: false, metaKey: false, ...extra });
  confere(tecla("Enter") === "\r" && tecla("Backspace") === "\x7f" && tecla("ArrowUp") === "\x1b[A" && tecla("a") === "a" && tecla("F5") === null,
    "console: teclas viram o que o terminal espera, e as que não são dele passam");
  confere(tecla("c", { ctrlKey: true }) === "\x03" && tecla("d", { ctrlKey: true }) === "\x04" && tecla("v", { ctrlKey: true }) === null && tecla("t", { altKey: true }) === null,
    "console: Ctrl-C e Ctrl-D vão, Ctrl-V e Alt-… ficam com o navegador");
  api.openPanel("homebox"); await esperar(30);
  api.showConsole("homebox");
  const sk = sockets[sockets.length - 1];
  confere(/^wss?:\/\/.*\/api\/shell\?unit=homebox$/.test(sk.url) || sk.url === "ws:///api/shell?unit=homebox", `console: abre o WebSocket da unit (${sk.url})`);
  sk.onopen();
  confere(sk.sent[0].t === "size" && sk.sent[0].c === 100, "console: informa o tamanho ao abrir");
  const telaC = [...$("p-section").walk()].find((e) => e.attrs && e.attrs.class === "term");
  telaC.listeners.keydown({ key: "l", ctrlKey: false, altKey: false, metaKey: false, preventDefault() {} });
  telaC.listeners.keydown({ key: "Enter", ctrlKey: false, altKey: false, metaKey: false, preventDefault() {} });
  confere(sk.sent.slice(1).map((m) => m.d).join("") === "l\r", "console: o que se digita vai como entrada");
  sk.onmessage({ data: "hello\r\n$ " }); await esperar(80);
  confere(telaC.textContent === "hello\n$ ", `console: a saída aparece (${JSON.stringify(telaC.textContent)})`);
  api.showLogs("homebox");
  confere(sk.closed === true, "console: abrir os logs fecha a sessão");
  $("panel").open = false;

  // an install made under media-stack: said above everything, with a button that starts the migration
  api.S.legacy = [{ from: "media-stack", units: [{ old: "media-stack-sonarr", new: "sonarr" }, { old: "media-stack-jellyfin", new: "jellyfin" }] }];
  api.setView("apps"); api.renderGrid();
  confere(!$("legacy").hidden && /Uma instalação antiga do media-stack foi encontrada \(2 apps\)/.test($("legacy").textContent) && /nada é copiado nem apagado/.test($("legacy").textContent), "migração: o aviso de uma instalação antiga");
  rotas["/api/migrate"] = { job: "jm", apps: ["sonarr", "jellyfin"] }; rotas["/api/job/jm"] = { output: "done\n", next: 1, rc: 0 };
  const antesMg = posts.length;
  porTexto($("legacy"), "Migrar")[0].listeners.click(); await esperar(1300);
  confere(posts.slice(antesMg).some((x) => x.rota === "/api/migrate" && x.corpo.from === "media-stack"), "o botão Migrar pede a migração");
  api.S.legacy = []; api.renderGrid();
  confere($("legacy").hidden, "sem instalação antiga, sem aviso");
  $("bulk").open = false;

  // a stopped or paused app greys out: the tile says its state, and the stylesheet does the rest
  const bdTile = api.S.apps.find((x) => x.id === "homebox");
  api.setView("apps");
  const estadoTile = (u) => { bdTile.units = u; api.renderGrid(); return [...$("grid").walk()].find((e) => e.attrs && /(^| )tile( |$)/.test(e.attrs.class || "") && /Homebox/.test(e.textContent)).attrs["data-run"]; };
  confere(estadoTile([unidade("homebox")]) === "running", "tile: rodando fica colorido (data-run=running)");
  confere(estadoTile([unidade("homebox", { service: "inactive", container: "—" })]) === "stopped", "tile: parado marca data-run=stopped");
  confere(estadoTile([unidade("homebox", { container: "paused" })]) === "paused", "tile: pausado marca data-run=paused");
  confere(/\.card\.tile:not\(\[data-run=running\]\) \.plate[^}]*grayscale\(1\)[^}]*opacity/.test(fs.readFileSync(path.join(__dirname, "..", "style.css"), "utf8")), "o CSS deixa o ícone preto e branco e com transparência");
  bdTile.units = [unidade("homebox")];

  // progress of a job: the plan as steps, which one is under way, and what is done; a chunk may end in the middle of a line
  const lis = (host) => [...host.walk()].filter((e) => e.tag === "li");
  const classe = (li) => li.attrs.class.replace("pr-step ", "");
  const pg = api.jobProgress($("p-progress"));
  pg.reset();
  pg.feed("  !  sem TAILNET: aviso\nhomebox: instalação, 4 passos\n  -> mkdir -p /h/.config/containers/volumes/homebox/data\n  -> cp apps/homebox/homebox.container -> /h/x/homebox.container\n  -> systemctl --user restart homebox  (acompanha o log enquanto sobe)\n");
  pg.feed("  -> wait until it is healthy (up to 120s), or put the previous version back\n");
  confere(!$("p-progress").hidden && lis($("p-progress")).map(classe).join(",") === "wait,wait,wait,wait", "progresso: o plano aparece como passos à espera");
  pg.feed("[1/4] mkdir -p /h/x\n(sandbox, não executado: x)\n[2/4] cp apps/homebox/homebox.container -> /h/x\n");
  confere(lis($("p-progress")).map(classe).join(",") === "done,now,wait,wait" && /Passo 2 de 4/.test($("p-progress").textContent) && /Copiar a unit/.test($("p-progress").textContent) && /Criar a pasta dos dados/.test($("p-progress").textContent), "progresso: o passo 1 feito, o 2 em andamento, com nomes legíveis");
  pg.feed("[3/");
  confere(lis($("p-progress")).map(classe).join(",") === "done,now,wait,wait", "uma linha cortada ao meio espera o resto");
  pg.feed("4] systemctl --user restart homebox  (acompanha o log enquanto sobe)\n");
  confere(lis($("p-progress")).map(classe).join(",") === "done,done,now,wait" && /Reiniciar homebox/.test($("p-progress").textContent), "progresso: o restart em andamento");
  const barraP = [...$("p-progress").walk()].find((e) => e.tag === "i");
  confere(barraP.style.width === "50%", `a barra vai a metade com 2 de 4 feitos (${barraP.style.width})`);
  pg.feed("[4/4] wait until it is healthy (up to 120s), or put the previous version back\n       … homebox: esperando ficar saudável (10s / 120s)\n");
  confere(/Esperar ficar saudável \(até 120s\)/.test($("p-progress").textContent) && classe(lis($("p-progress"))[3]) === "now", "o último passo, esperar a saúde, mostra o tempo e fica em andamento");
  pg.finish(0);
  confere(lis($("p-progress")).every((li) => classe(li) === "done") && /Concluído/.test($("p-progress").textContent) && [...$("p-progress").walk()].find((e) => e.tag === "i").style.width === "100%", "ao terminar com sucesso: tudo feito, 100%");
  pg.reset(); pg.feed("homebox: atualização, 3 passos\n  -> mkdir -p x\n  -> systemctl --user daemon-reload\n  -> systemctl --user restart homebox\n[1/3] mkdir -p x\n[2/3] systemctl --user daemon-reload\n\nFALHOU em: systemctl --user daemon-reload\nboom\n");
  pg.finish(1);
  confere(lis($("p-progress")).map(classe).join(",") === "done,bad,wait" && /Falhou neste passo/.test($("p-progress").textContent), "ao falhar: o passo que falhou em vermelho e os seguintes à espera");
  pg.reset(); pg.feed("a: atualização, 1 passos\n  -> mkdir -p a\n[1/1] mkdir -p a\n\nb: atualização, 2 passos\n  -> mkdir -p b\n  -> systemctl --user restart b\n[1/2] mkdir -p b\n");
  confere(lis($("p-progress")).length === 2 && classe(lis($("p-progress"))[0]) === "now" && /Reiniciar b/.test($("p-progress").textContent), "um segundo plano no mesmo job (atualizar tudo) recomeça a lista");
  pg.finish(0); pg.reset();
  confere(api.stepLabel("mkdir -p /h/.config/containers/volumes/a/data") === "Criar a pasta dos dados" && api.stepLabel("mkdir -p /h/.config/containers/systemd") === "Criar a pasta das units" && api.stepLabel("podman pull docker.io/x/y:1") === "Baixar a imagem" && api.stepLabel("something unknown") === "something unknown", "nomes legíveis, e o que não se conhece fica como está");

  // the same progress as a terminal: the output as it comes, the steps marked, kept as a preference
  const pt2 = api.jobProgress($("p-progress"));
  pt2.reset();
  pt2.feed("homebox: instalação, 2 passos\n  -> mkdir -p /h/.config/containers/volumes/homebox/data\n  -> systemctl --user restart homebox\n[1/2] mkdir -p /h/x\n       (sandbox, não executado: x)\n  !  um aviso\n");
  const botaoModo = (rot) => [...$("p-progress").walk()].find((e) => e.tag === "button" && e.textContent === rot);
  confere(botaoModo("Passos").attrs["aria-pressed"] === "true" && botaoModo("Terminal").attrs["aria-pressed"] === "false" && lis($("p-progress")).length === 2, "o andamento começa nos passos, com a opção Terminal ao lado");
  botaoModo("Terminal").listeners.click();
  const term = [...$("p-progress").walk()].find((e) => e.tag === "pre" && e.attrs.class === "live-term");
  const spans = term ? [...term.walk()].filter((e) => e.tag === "span") : [];
  confere(!!term && lis($("p-progress")).length === 0 && /\[1\/2\] mkdir -p \/h\/x/.test(term.textContent) && /um aviso/.test(term.textContent), "terminal: a saída como ela vem, no lugar dos passos");
  confere(spans.some((e) => e.attrs.class === "step" && /\[1\/2\]/.test(e.textContent)) && spans.some((e) => e.attrs.class === "warn") && spans.some((e) => e.attrs.class === "dim") && spans.some((e) => e.attrs.class === "cursor"), "terminal: o passo, o aviso e o que é só detalhe têm cor, e há um cursor enquanto roda");
  confere(guardado.get("qh-progress") === "terminal", "a escolha fica guardada no navegador");
  pt2.feed("[2/2] systemctl --user restart homebox\n");
  confere(/\[2\/2\] systemctl --user restart homebox/.test([...$("p-progress").walk()].find((e) => e.tag === "pre" && e.attrs.class === "live-term").textContent), "terminal: acompanha a saída que chega");
  pt2.finish(1);
  const termFim = [...$("p-progress").walk()].find((e) => e.tag === "pre" && e.attrs.class === "live-term");
  confere(![...termFim.walk()].some((e) => e.attrs && e.attrs.class === "cursor") && /Falhou neste passo/.test($("p-progress").textContent), "ao terminar o cursor some, e o estado fica no alto");
  const pt3 = api.jobProgress($("p-progress"));              // a new job opens in the terminal, as chosen
  pt3.reset(); pt3.feed("a: instalação, 1 passos\n  -> mkdir -p a\n[1/1] mkdir -p a\n");
  confere([...$("p-progress").walk()].some((e) => e.tag === "pre" && e.attrs.class === "live-term"), "o próximo trabalho já abre no terminal");
  botaoModo("Passos").listeners.click();
  confere(lis($("p-progress")).length === 1 && guardado.get("qh-progress") === "steps", "voltar aos passos");
  pt3.finish(0); pt3.reset();

  // the window of a bigger job (a migration, update all) follows the same preference
  guardado.set("qh-progress", "terminal");
  api.S.legacy = [{ from: "media-stack", units: [{ old: "media-stack-sonarr", new: "sonarr" }] }];
  api.setView("apps"); api.renderGrid();
  rotas["/api/migrate"] = { job: "jm2", apps: ["sonarr"] };
  rotas["/api/job/jm2"] = { output: "media-stack: migrar, 1 passos\n  -> mkdir -p /h/x\n[1/1] mkdir -p /h/x\n", next: 3, rc: 0 };
  porTexto($("legacy"), "Migrar")[0].listeners.click(); await esperar(1400);
  confere($("b-out").hidden === true && [...$("b-progress").walk()].some((e) => e.tag === "pre" && e.attrs.class === "live-term"), "a janela de um trabalho grande segue a preferência: terminal no lugar do log");
  api.S.legacy = []; api.renderGrid(); $("bulk").open = false; guardado.delete("qh-progress");

  // per-app CPU and memory: a short history kept while the page is open, drawn as two sparklines in the app's panel
  const bs = api.S.apps.find((x) => x.id === "homebox");
  bs.units = [unidade("homebox", { service: "active" })];
  for (const cpu of [10, 30, 20, 55]) { rotas["/api/stats"] = { stats: { homebox: { cpu, mem: 100 * 2 ** 20 + cpu * 2 ** 20 } } }; await api.pollStats(); }
  api.openPanel("homebox"); await esperar(60);
  const barras = [...$("p-info").walk()].filter((e) => e.tag === "i");
  confere(barras.length === 0 && !/CPU|Memória/.test($("p-info").textContent) && api.S.rhist === undefined, `o painel não mostra CPU nem memória, nem os gráficos (${barras.length} barras)`);
  $("panel").open = false;
  bs.units = [unidade("homebox")];

  // health, what really runs, force verbs: buttons per unit, each opening its view in the panel
  const bh = api.S.apps.find((x) => x.id === "homebox");
  bh.units = [unidade("homebox", { service: "active", container: "healthy" })];
  rotas["/api/health"] = { status: "unhealthy", streak: 3, running: true, config: { test: "node scripts/health-check.js", shell: true, interval: 30, timeout: 5, start_period: 20, retries: 3, on_failure: null },
    runs: [{ start: "2026-11-18T20:05:00-03:00", end: "x", exit: 1, output: "curl: (7) refused" }, { start: "2026-11-18T20:04:00-03:00", end: "x", exit: 0, output: "" }] };
  rotas["/api/health/run"] = { rc: 1, output: "boom", health: rotas["/api/health"] };
  rotas["/api/runtime"] = { name: "homebox", image: "docker.io/x/homebox:1", digest: "sha256:ab", command: "/app serve", user: "1000", workdir: "/app", created: "2026-11-18T00:00:00Z", started: "2026-11-18T00:00:01Z", restarts: 2,
    networks: [{ name: "tsdproxy-net", ip: "10.89.0.2", gateway: "10.89.0.1", aliases: ["homebox"] }], ports: [], mounts: [{ type: "bind", source: "/h/data", dest: "/data", rw: true }, { type: "bind", source: "/h/lib", dest: "/lib", rw: false }],
    env: [{ key: "ADMIN_TOKEN", value: "••••••••", secret: true }, { key: "TZ", value: "••••••••", secret: false }], revealed: false,
    limits: { read_only: true, pids: 256, memory: null, cap_drop: ["CAP_CHOWN"], cap_add: [], security: ["no-new-privileges"] } };
  rotas["/api/unit"] = { job: "jf" }; rotas["/api/job/jf"] = { output: "ok\n", next: 1, rc: 0 };
  api.openPanel("homebox"); await esperar(80);
  confere(["Saúde", "Detalhes", "Reiniciar à força", "Parar à força"].every((x) => porTexto($("p-units"), x).length === 1), "cada unit rodando ganha Saúde, Detalhes e as duas ações à força");
  porTexto($("p-units"), "Saúde")[0].listeners.click(); await esperar(60);
  confere(/com problema/.test($("p-section").textContent) && /3 falhas seguidas/.test($("p-section").textContent) && /curl: \(7\) refused/.test($("p-section").textContent) && /node scripts\/health-check\.js/.test($("p-section").textContent) && /A cada 30s/.test($("p-section").textContent), "saúde: status, falhas seguidas, a sonda e o que a última execução imprimiu");
  const antesH = posts.length;
  porTexto($("p-section"), "Rodar agora")[0].listeners.click(); await esperar(80);
  confere(posts.slice(antesH).some((x) => x.rota === "/api/health/run" && x.corpo.unit === "homebox") && /A sonda falhou \(saída 1\)\. boom/.test($("p-section").textContent), "rodar agora: pede e mostra a saída da sonda");
  porTexto($("p-units"), "Detalhes")[0].listeners.click(); await esperar(60);
  confere(/docker\.io\/x\/homebox:1/.test($("p-section").textContent) && /tsdproxy-net/.test($("p-section").textContent) && /\/h\/lib/.test($("p-section").textContent) && /só leitura/.test($("p-section").textContent) && /Nenhuma: só se chega por uma rede/.test($("p-section").textContent), "detalhes: imagem, redes, montagens (com somente leitura) e que não há porta publicada");
  confere(!/hunter2/.test($("p-section").textContent) && (($("p-section").textContent.match(/••••••••/g) || []).length === 2) && /secret/.test($("p-section").textContent), "detalhes: valores mascarados, e a variável de um Secret= marcada");
  rotas["/api/runtime"] = { ...rotas["/api/runtime"], revealed: true, env: [{ key: "ADMIN_TOKEN", value: "hunter2", secret: true }, { key: "TZ", value: "UTC", secret: false }] };
  porTexto($("p-section"), "Mostrar os valores")[0].listeners.click(); await esperar(60);
  confere(/hunter2/.test($("p-section").textContent) && porTexto($("p-section"), "Esconder os valores").length === 1, "mostrar os valores pede de novo, com reveal");
  // force verbs: asked twice, then the unit verb goes to the server
  const antesF = posts.length;
  porTexto($("p-units"), "Parar à força")[0].listeners.click();
  confere(posts.length === antesF && porTexto($("p-units"), "Confirmar: mata na hora").length === 1, "parar à força: o primeiro clique só pede confirmação");
  porTexto($("p-units"), "Confirmar: mata na hora")[0].listeners.click(); await esperar(1300);
  confere(posts.slice(antesF).some((x) => x.rota === "/api/unit" && x.corpo.verb === "force-stop" && x.corpo.unit === "homebox"), "o segundo clique manda force-stop");
  $("panel").open = false;
  bh.units = [unidade("homebox")];

  // all the images: who uses each, what it says about itself, and only an unused one can be deleted
  rotas["/api/images"] = { images: [
    { id: "a".repeat(64), short: "aaaaaaaaaaaa", names: ["docker.io/x/old:1"], size: 900 * 2 ** 20, created: "2026-01-01T00:00:00Z", used_by: [], in_use: false, wanted: false, removable: true, labels: { version: "1.0", revision: "0123456789abcdef" } },
    { id: "b".repeat(64), short: "bbbbbbbbbbbb", names: ["docker.io/x/homebox:2", "docker.io/x/homebox:latest"], size: 300 * 2 ** 20, created: "2026-02-01T00:00:00Z", used_by: [{ container: "homebox", unit: "homebox", app: "homebox", state: "running" }], in_use: true, wanted: true, removable: false, labels: {} }] };
  rotas["/api/images/history"] = { layers: [{ created: "2026-01-01T00:00:00Z", by: "CMD node app.js", size: 0 }] };
  rotas["/api/images/rm"] = { job: "jr2" }; rotas["/api/job/jr2"] = { output: "removed\n", next: 1, rc: 0 };
  await api.openResources(); await esperar(60);
  const corpoI = $("r-body").textContent;
  confere(/Todas as imagens/.test(corpoI) && /docker\.io\/x\/old:1/.test(corpoI) && /900\.0 MB/.test(corpoI) && /1\.0 · 01234567/.test(corpoI) && /Homebox/.test(corpoI) && /ninguém · sem uso/.test(corpoI), `imagens: tamanho, quem usa, versão e revisão (${corpoI.slice(-260)})`);
  const apagarI = porTexto($("r-body"), "Apagar").filter((b) => b.attrs.class && /force/.test(b.attrs.class));
  confere(apagarI.length === 1, "só a imagem sem uso tem Apagar");
  const antesI = posts.length;
  apagarI[0].listeners.click();
  confere(posts.length === antesI && porTexto($("r-body"), "Confirmar").length >= 1, "apagar a imagem: o primeiro clique só pede confirmação");
  porTexto($("r-body"), "Confirmar").filter((b) => b.attrs.class && /force/.test(b.attrs.class))[0].listeners.click(); await esperar(1400);
  confere(posts.slice(antesI).some((x) => x.rota === "/api/images/rm" && x.corpo.id === "a".repeat(64)), "o segundo clique apaga pelo id completo");
  $("bulk").open = false; $("resources").open = false;

  // a unit the repository changed since the install: the panel says so, and shows what changed before the update
  const bd = api.S.apps.find((x) => x.id === "homebox");
  bd.units = [unidade("homebox", { drift: "changed" })];
  rotas["/api/drift"] = { unit: "homebox", changed: true, diff: "--- installed\n+++ repository\n@@ -1,3 +1,3 @@\n [Container]\n-HealthCmd=CMD-SHELL node /app/src/scripts/health-check.js\n+HealthCmd=CMD-SHELL node scripts/health-check.js" };
  api.openPanel("homebox"); await esperar(80);
  const spansD = [...$("p-drift-diff").walk()].filter((e) => e.tag === "span");
  confere(!$("p-drift").hidden && /O \.container de homebox mudou no repositório/.test($("p-drift-title").textContent) && /Atualizar escreve o arquivo novo/.test($("p-drift-hint").textContent), "painel: um .container mudado no repositório é dito, antes de atualizar");
  confere(spansD.some((e) => e.attrs.class === "add" && /node scripts\/health-check\.js/.test(e.textContent)) && spansD.some((e) => e.attrs.class === "del" && /src\/scripts/.test(e.textContent)) && !spansD.some((e) => e.attrs.class === "add" && /\+\+\+/.test(e.textContent)), "a diferença: o que sai em vermelho, o que entra em verde, sem as linhas de cabeçalho");
  bd.units = [unidade("homebox")];
  api.openPanel("homebox"); await esperar(60);
  confere($("p-drift").hidden, "sem diferença, sem aviso");
  $("panel").open = false;

  // My apps: counters as filters (updates, problems) and a one-line summary
  const mh = api.S.apps.find((x) => x.id === "homebox"), mm = api.S.apps.find((x) => x.id === "memos");
  mh.units = [unidade("homebox", { drift: "changed", image: "x:2" })];
  mm.units = [unidade("memos", { service: "failed", container: "down" })];
  api.setView("apps");
  const chips = () => botoes($("groups")).map((b) => b.textContent.trim());
  confere(chips().join("|") === "Todos 2|Com atualização 1|Com problema 1", `filtros com contadores (${chips().join("|")})`);
  confere(/1 rodando · 1 parado/.test($("summary").textContent), `resumo no topo (${$("summary").textContent})`);
  botoes($("groups"))[1].listeners.click();
  confere($("grid").kids.length === 1 && /Homebox/.test($("grid").textContent), "filtro 'com atualização' mostra só o app com atualização");
  botoes($("groups"))[2].listeners.click();
  confere($("grid").kids.length === 1 && /Memos/.test($("grid").textContent), "filtro 'com problema' mostra só o app com problema");
  botoes($("groups"))[2].listeners.click();
  confere($("grid").kids.length === 2, "clicar de novo no filtro ativo volta a mostrar todos");
  api.setView("store"); api.setView("apps");
  confere($("grid").kids.length === 2, "trocar de aba zera o filtro");
  mh.units = [unidade("homebox")]; mm.units = [unidade("memos")];
  api.renderGrid();

  // failure state: loop, failed with the exit code, and a recovered restart; details and last failure in the panel
  const bf = api.S.apps.find((x) => x.id === "homebox");
  const falha = (extra) => ({ restarts: 0, exit: 0, result: "success", state: "active", sub: "running", last: 1700000000, ...extra });
  api.setView("apps");
  bf.units = [unidade("homebox", { service: "activating", failure: falha({ restarts: 7, exit: 1, result: "exit-code", state: "activating", sub: "auto-restart" }) })];
  api.renderGrid();
  confere(/loop de restart \(7×\)/.test($("grid").textContent), `card: loop de restart com a contagem (${$("grid").textContent.slice(0, 60)})`);
  bf.units = [unidade("homebox", { service: "failed", failure: falha({ exit: 125, result: "exit-code", state: "failed", sub: "failed" }) })];
  api.renderGrid();
  confere(/falhou \(saída 125\)/.test($("grid").textContent), "card: falhou, com o código de saída");
  api.openPanel("homebox"); await esperar(30);
  confere(!$("p-fail").hidden && /homebox: falhou .*saída 125 \(exit-code\) · última falha/.test($("p-fail").textContent), `painel: detalhes e última falha (${$("p-fail").textContent})`);
  $("panel").open = false;
  bf.units = [unidade("homebox", { failure: falha({ restarts: 2 }) })];
  api.renderGrid();
  confere(/reiniciou 2×/.test($("grid").textContent), "card: recuperado depois de reiniciar mostra só um aviso");
  bf.units = [unidade("homebox")];
  api.renderGrid();
  confere(!/reiniciou|loop de restart|falhou \(/.test($("grid").textContent), "sem falha: sem selo");

  // site monitor: a running app that does not answer is a red dot; one that answers says how fast
  api.S.mon = { homebox: { ok: false, status: null, ms: null } };
  api.setView("apps"); api.renderGrid();
  confere(/não responde/.test(menuCtx(doHomebox()).textContent), "monitor: rodando mas sem resposta, o menu diz que não responde");
  api.S.mon = { homebox: { ok: true, status: 200, ms: 42 } };
  api.renderGrid();
  confere(/rodando · responde em 42 ms/.test(menuCtx(doHomebox()).textContent), "monitor: respondendo, o menu diz em quanto tempo");
  api.S.mon = {};
  api.renderGrid();

  // a newer version: a small arrow on the icon, no words
  const upAntes = api.S.upd.homebox;
  api.S.upd.homebox = { bucket: "BEHIND", there: "9.9", unit: "homebox" };
  api.setView("apps"); api.renderGrid();
  const tileHb = doHomebox();
  const itemUp = [...menuCtx(tileHb).walk()].find((e) => e.tag === "button" && /(^| )up( |$)/.test(e.attrs.class || ""));
  confere(itemUp && /9\.9/.test(itemUp.textContent) && !/nova versão|9\.9/.test(tileHb.textContent), `nova versão: nada no azulejo; no menu, "Atualizar para 9.9" em destaque (${itemUp && itemUp.textContent})`);
  if (upAntes === undefined) delete api.S.upd.homebox; else api.S.upd.homebox = upAntes;
  api.renderGrid();

  // play / pause / stop: the three buttons enable by state, and a click asks the server
  const bc = api.S.apps.find((x) => x.id === "homebox");
  const estadoBotoes = () => [...$("p-actions").walk()].filter((e) => e.attrs && e.attrs.class === "ctl").map((e) => (e.attrs.disabled === undefined ? "on" : "off")).join(",");
  api.openPanel("homebox"); await esperar(30);
  confere(estadoBotoes() === "off,on,on", `rodando: só pausar e parar (${estadoBotoes()})`);
  bc.units = [unidade("homebox", { container: "paused" })];
  api.setView("apps");
  api.openPanel("homebox"); await esperar(30);
  confere(estadoBotoes() === "on,off,on" && /pausado/.test($("p-info").textContent + $("grid").textContent + $("p-meta").textContent + $("panel").textContent), `pausado: retomar e parar, e o selo diz pausado (${estadoBotoes()})`);
  bc.units = [unidade("homebox", { service: "inactive", container: null })];
  api.openPanel("homebox"); await esperar(30);
  confere(estadoBotoes() === "on,off,off", `parado: só iniciar (${estadoBotoes()})`);
  bc.units = [unidade("homebox", { service: "inactive", container: null, stopped: true })];
  api.setView("apps"); api.renderGrid();
  confere(/parado/.test(menuCtx(doHomebox()).textContent) && !/parado|Atenção|atenção/.test($("grid").textContent), "parado de propósito: o azulejo não alarma, o menu diz parado");
  bc.units = [unidade("homebox")];
  rotas["/api/control"] = { job: "jc" }; rotas["/api/job/jc"] = { output: "", next: 0, rc: 0 };
  api.openPanel("homebox"); await esperar(30);
  const antesCtl = posts.length;
  [...$("p-actions").walk()].filter((e) => e.attrs && e.attrs.class === "ctl")[1].listeners.click(); await esperar(900);
  confere(posts.slice(antesCtl).some((x) => x.rota === "/api/control" && x.corpo.verb === "pause" && x.corpo.app === "homebox"), "o botão pausar chama /api/control");
  $("panel").open = false;

  // customize before installing: the form opens on an app that is not installed, keeps the choice, and the install carries it
  const gi = api.S.apps.find((x) => x.id === "gitea");
  api.openPanel("gitea"); await esperar(30);
  porTexto($("p-actions"), "Instalação personalizada…")[0].listeners.click(); await esperar(100);
  const formPre = () => folhaC;
  confere($("custom").open && /Antes de instalar/.test(formPre().textContent) && porTexto(formPre(), "Instalar").length === 1
    && porTexto(formPre(), "Salvar e aplicar").length === 0, "antes de instalar: a tela abre, com Instalar e sem Salvar e aplicar");
  confere(/Imagem Docker/.test(formPre().textContent) && /Nome do contêiner/.test(formPre().textContent) && /Clique em “\+”/.test(formPre().textContent),
    "a tela mostra a imagem, o nome do contêiner e a dica de lista vazia");
  // the folder picker beside a volume: list, go down, choose with a new sub-folder
  rotas["/api/dirs"] = { path: "/h/vol", value: "%h/vol", shown: "~/vol", parent: null, at_root: true, dirs: [{ name: "a", path: "/h/vol/a" }] };
  const botaoPasta = [...formPre().walk()].filter((e) => e.tag === "button" && e.attrs.title === "Escolher pasta")[0];
  const linhaVol = (() => { let e = botaoPasta; const todos = [...formPre().walk()]; return todos.find((r) => r.attrs && r.attrs.class === "cust-row" && [...r.walk()].includes(botaoPasta)); })();
  const painelPasta = [...linhaVol.walk()].find((e) => e.attrs && e.attrs.class === "picker");
  confere(painelPasta.hidden === true, "o seletor de pasta começa fechado");
  botaoPasta.listeners.click(); await esperar(50);
  confere(painelPasta.hidden === false, "e abre ao clicar no ícone");
  confere(/~\/vol/.test(painelPasta.textContent) && /📁 a/.test(painelPasta.textContent), `seletor: lista as pastas permitidas (${painelPasta.textContent})`);
  rotas["/api/dirs"] = { path: "/h/vol/a", value: "%h/vol/a", shown: "~/vol/a", parent: "/h/vol", at_root: false, dirs: [] };
  [...painelPasta.walk()].find((e) => e.tag === "button" && /📁 a/.test(e.textContent)).listeners.click(); await esperar(50);
  confere(/~\/vol\/a/.test(painelPasta.textContent) && /Sem subpastas/.test(painelPasta.textContent), "seletor: entra na pasta");
  const novaPasta = [...painelPasta.walk()].find((e) => e.tag === "input");
  const campoHostPre = [...linhaVol.walk()].find((e) => e.tag === "input");
  novaPasta.value = "com espaço";
  [...painelPasta.walk()].find((e) => e.tag === "button" && e.textContent === "Usar esta pasta").listeners.click();
  confere(campoHostPre.value !== "%h/vol/a/com espaço", "seletor: recusa nome de pasta com espaço");
  novaPasta.value = "novo";
  [...painelPasta.walk()].find((e) => e.tag === "button" && e.textContent === "Usar esta pasta").listeners.click();
  confere(campoHostPre.value === "%h/vol/a/novo", `seletor: escolhe a pasta, com a subpasta nova (${campoHostPre.value})`);
  delete rotas["/api/dirs"];
  const urlsPre = []; const fetchAntes = global.fetch;
  global.fetch = async (u, o) => { urlsPre.push(u); return fetchAntes(u, o); };
  const previaAntes = rotas["/api/custom/preview"];
  rotas["/api/custom/preview"] = { text: "# base=x\n[Container]\nEnvironment=A=1\n", errors: [], warnings: [], generated: "", changed: true };
  rotas["/api/plan"] = { rc: 0, output: "x", nothing: false };
  porTexto(formPre(), "Instalar")[0].listeners.click(); await esperar(150);
  global.fetch = fetchAntes;
  if (previaAntes === undefined) delete rotas["/api/custom/preview"]; else rotas["/api/custom/preview"] = previaAntes;
  const prev = posts.filter((x) => x.rota === "/api/custom/preview").pop().corpo;
  confere(prev.pre === true && prev.unit === "gitea", "a prévia leva pre: true");
  confere(urlsPre.some((u) => /\/api\/custom\?unit=gitea&pre=1|\/api\/custom\/preview/.test(u)), "e pede o estado da unit ainda não instalada");
  confere(!!api.S.preCustom.gitea && !$("custom").open && !$("p-form").hidden, "Instalar guarda a escolha, fecha a tela e abre a confirmação da instalação");
  api.openPanel("gitea"); await esperar(30);
  confere(porTexto($("p-actions"), "Instalação personalizada… ✓").length === 1, "o botão mostra que há personalização guardada");
  rotas["/api/plan"] = { rc: 0, output: "x", nothing: false };
  rotas["/api/run"] = { job: "jr" }; rotas["/api/job/jr"] = { output: "ok\n", next: 1, rc: 0 };
  porTexto($("p-actions"), "Instalar")[0].listeners.click(); await esperar(100);
  confere(/Personalização guardada para gitea/.test($("p-form").textContent), "o formulário de instalação diz que a personalização vai junto");
  // ask: the manifest's form (label, hint, type, limits) reaches the inputs
  const giteaApp = api.S.apps.find((x) => x.id === "gitea");
  giteaApp.asks = { secrets: [{ secret: "gitea-tok", instruction: "paste it", exists: false,
    field: { type: "password", label: { en: "Token", pt: "Token do runner" }, hint: { en: "From Gitea.", pt: "Do Gitea." }, min: 12, max: 40, required: true, regex: "[a-z]+", pattern_error: { en: "x", pt: "só letras" } } }],
    vars: [{ name: "MEDIA_DATA_DIR", default: "~/data", set: false, field: { type: "path", label: { en: "Media", pt: "Pasta de mídia" }, hint: { en: "h", pt: "Onde fica a biblioteca." } } }] };
  api.openPanel("gitea"); await esperar(30);
  porTexto($("p-actions"), "Instalar")[0].listeners.click(); await esperar(100);
  const camposAsk = [...$("p-form").walk()].filter((e) => e.tag === "input");
  const campoTok = camposAsk.find((e) => e.attrs["data-secret"] === "gitea-tok");
  confere(campoTok && campoTok.attrs.type === "password" && campoTok.attrs.minlength === 12 && campoTok.attrs.maxlength === 40 && campoTok.attrs.required === "" && campoTok.attrs.pattern === "[a-z]+" && campoTok.attrs.title === "só letras", "ask: tipo, limites, obrigatório e padrão viram atributos do campo");
  confere(/Token do runner/.test($("p-form").textContent) && /Do Gitea\./.test($("p-form").textContent) && /Pasta de mídia/.test($("p-form").textContent) && /Onde fica a biblioteca/.test($("p-form").textContent), "ask: rótulo e dica no idioma da tela");
  giteaApp.asks = { secrets: [], vars: [] };
  api.openPanel("gitea"); await esperar(30);
  porTexto($("p-actions"), "Instalar")[0].listeners.click(); await esperar(100);
  const antesRun = posts.length;
  await $("p-form").onsubmit({ preventDefault() {} }); await esperar(1000);
  const instalou = posts.slice(antesRun).find((x) => x.rota === "/api/run");
  confere(instalou && instalou.corpo.action === "install" && instalou.corpo.custom && instalou.corpo.custom.gitea, `a instalação leva a personalização (${JSON.stringify(instalou && Object.keys(instalou.corpo))})`);
  confere(!api.S.preCustom.gitea, "depois de instalar, o que estava guardado é descartado");
  $("panel").open = false;
  const areaRaw = () => [...folhaC.walk()].find((e) => e.tag === "textarea" && e.attrs.class === "raw");
  // before an install, the person's own .container rides along (and the form is left out for that unit)
  const REPO_PRE = "[Container]\nImage=x:1\n";
  rotas["/api/custom"] = { ...rotas["/api/custom"], unit_source: REPO_PRE, repo_text: REPO_PRE, custom_unit: false, installed_text: null };
  rotas["/api/custom/unit-check"] = { errors: [], warnings: [], changed: true };
  const previaGuardada = rotas["/api/custom/preview"];
  rotas["/api/custom/preview"] = { text: null, errors: [], warnings: [], generated: "", changed: false };
  api.openPanel("gitea"); await esperar(30);
  porTexto($("p-actions"), "Instalação personalizada…")[0].listeners.click(); await esperar(100);
  areaRaw().value = REPO_PRE + "Label=meu=sim\n"; areaRaw().listeners.input();
  porTexto(folhaC, "Instalar")[0].listeners.click(); await esperar(200);
  confere(api.S.preUnit.gitea && api.S.preUnit.gitea.gitea === REPO_PRE + "Label=meu=sim\n" && !$("custom").open, "antes de instalar: o .container editado fica guardado e a tela fecha");
  api.openPanel("gitea"); await esperar(30);
  confere(porTexto($("p-actions"), "Instalação personalizada… ✓").length === 1, "o botão mostra que há personalização (o .container)");
  porTexto($("p-actions"), "Instalar")[0].listeners.click(); await esperar(100);
  const antesRun2 = posts.length;
  await $("p-form").onsubmit({ preventDefault() {} }); await esperar(1000);
  const inst2 = posts.slice(antesRun2).find((x) => x.rota === "/api/run");
  confere(inst2 && inst2.corpo.custom_units && inst2.corpo.custom_units.gitea.includes("meu=sim") && inst2.corpo.ack === true && !inst2.corpo.custom, "a instalação leva o .container próprio (e não o formulário dessa unit)");
  confere(!api.S.preUnit.gitea, "depois de instalar, o .container guardado é descartado");
  if (previaGuardada === undefined) delete rotas["/api/custom/preview"]; else rotas["/api/custom/preview"] = previaGuardada;
  $("panel").open = false;

  // instances: an installed base app offers "New instance" (Configure tab), and the install carries the name; an instance does not offer it
  const gitea = api.S.apps.find((x) => x.id === "gitea"), giteaEra = gitea.installed;
  gitea.installed = true;
  api.openPanel("gitea"); await esperar(30);
  (await cfgBtn("Nova instância")).listeners.click(); await esperar(30);
  const nomeInst = [...$("p-section").walk()].find((e) => e.tag === "input" && e.attrs.type === "text");
  nomeInst.value = "casa";
  const antesInst = posts.length;
  porTexto($("p-section"), "Criar instância")[0].listeners.click(); await esperar(1200);
  const inst = posts.slice(antesInst).find((x) => x.rota === "/api/run");
  confere(inst && inst.corpo.action === "install" && inst.corpo.instance === "casa" && inst.corpo.app === "gitea", `a instância é criada pelo install com o nome (${JSON.stringify(inst && inst.corpo)})`);
  gitea.instance_of = "outro";
  api.openPanel("gitea"); await esperar(30);
  await cfgBtn("Personalizar");
  confere(porTexto($("p-section"), "Nova instância").length === 0 && /instância de outro/.test($("p-desc").textContent), "uma instância não gera outra, e diz de quem é");
  gitea.installed = giteaEra;
  delete api.S.apps.find((x) => x.id === "gitea").instance_of;
  $("panel").open = false;

  // install options: asked in the install form, sent with the install, read-only in the panel once installed
  const gt = api.S.apps.find((x) => x.id === "gitea");
  gt.options = [{ key: "database", question: "Which database?", default: "sqlite", chosen: "sqlite",
                  values: [{ value: "sqlite", label: "SQLite" }, { value: "postgres", label: "PostgreSQL" }] }];
  api.openPanel("gitea"); await esperar(30);
  porTexto($("p-actions"), "Instalar")[0].listeners.click(); await esperar(100);
  const seletor = [...$("p-form").walk()].find((e) => e.tag === "select" && e.attrs["data-option"] === "database");
  confere(seletor && /Which database/.test($("p-form").textContent) && /PostgreSQL/.test($("p-form").textContent), "o formulário pergunta a opção de instalação");
  seletor.value = "postgres";
  const antesOp = posts.length;
  await $("p-form").onsubmit({ preventDefault() {} }); await esperar(1000);
  const comOpcao = posts.slice(antesOp).find((x) => x.rota === "/api/run");
  confere(comOpcao && comOpcao.corpo.options && comOpcao.corpo.options.database === "postgres", `a instalação leva a opção escolhida (${JSON.stringify(comOpcao && comOpcao.corpo.options)})`);
  gt.options[0].chosen = "postgres"; gt.options_locked = true; gt.installed = true;
  api.openPanel("gitea"); await esperar(30);
  confere($("p-options").hidden === false && /PostgreSQL/.test($("p-options").textContent) && /mudar move os dados/.test($("p-options").textContent), "instalado: a opção aparece só para leitura");
  gt.options = []; gt.installed = false;
  api.openPanel("gitea"); await esperar(30);
  confere($("p-options").hidden === true, "sem opções: nada");
  $("panel").open = false;

  // the panel on its own: settings, update everything, delete the data
  rotas["/api/settings"] = { access: "tailnet", default: true, drift: ["memos", "gitea"], tailnet: false, modes: ["local", "tailnet", "both"] };
  rotas["/api/job/js"] = { output: "rule saved\n", next: 1, rc: 0 };
  await api.openSettings(); await esperar(50);
  const textoCfg = $("s-body").textContent;
  confere(/Como os apps são acessados/.test(textoCfg) && /Ainda não escolhida/.test(textoCfg) && /2 serviço\(s\) instalado\(s\) não seguem/.test(textoCfg) && /Tailnet não configurada/.test(textoCfg),
    `Configurações: a regra, quem não a segue e a tailnet (${textoCfg.slice(0, 60)})`);
  // alerts: the form comes with the settings, nothing is on by default, the token is write-only
  rotas["/api/alerts"] = { config: { enabled: false, server: "", topic: "", cooldown_hours: 6, disk_percent: 90, has_token: true,
                           kinds: { failed: true, unhealthy: true, restart_loop: true, backup: true, update: true, disk: true } },
                           kinds: ["failed", "unhealthy", "restart_loop", "backup", "update", "disk"], sent: 0 };
  rotas["/api/alerts/test"] = { ok: true };
  rotas["/api/ui"] = { theme: "system", accent: "orange", card: "shadow", density: "comfortable", bg_blur: 8, bg_dim: 35, background: false, bg_version: null };
  await api.openSettings(); await esperar(50);
  // podman: the version here, and a warning when it is older than the one the repository was verified on
  api.S.podman = "6.0.2"; api.S.podmanRec = "6.1.4"; api.S.podmanOutdated = true;
  await api.openSettings(); await esperar(50);
  confere(/Podman 6\.0\.2/.test($("s-body").textContent) && /verificado no Podman 6\.1\.4/.test($("s-body").textContent) && /6\.1\.1 a 6\.1\.3/.test($("s-body").textContent), "Configurações: Podman antigo, com o aviso");
  api.S.podman = "6.1.4"; api.S.podmanOutdated = false;
  await api.openSettings(); await esperar(50);
  confere(/Podman 6\.1\.4/.test($("s-body").textContent) && /Igual ou mais nova que a 6\.1\.4/.test($("s-body").textContent) && !/Atualize o pacote/.test($("s-body").textContent), "Configurações: Podman em dia, sem aviso");
  // power: each button asks again before it sends anything
  rotas["/api/power"] = { action: "poweroff" };
  const antesPow = posts.length;
  porTexto($("s-body"), "Desligar o servidor")[0].listeners.click();
  confere(posts.length === antesPow && porTexto($("s-body"), "Confirmar: Desligar o servidor").length === 1, "desligar: pede confirmação antes de enviar");
  porTexto($("s-body"), "Cancelar")[0].listeners.click();
  confere(posts.length === antesPow && porTexto($("s-body"), "Desligar o servidor").length === 1, "cancelar volta aos botões sem enviar");
  porTexto($("s-body"), "Desligar o servidor")[0].listeners.click();
  porTexto($("s-body"), "Confirmar: Desligar o servidor")[0].listeners.click(); await esperar(30);
  confere(posts.slice(antesPow).some((x) => x.rota === "/api/power" && x.corpo.action === "poweroff") && /Para ligar de novo/.test($("s-body").textContent), "desligar: confirmado, envia e avisa");
  // scheduled power: what is armed shows with a way to cancel it; a new one goes out with the delay or the time
  rotas["/api/power"] = { scheduled: { action: "reboot", at: Math.floor(Date.now() / 1000) + 3600 } };
  await api.openSettings(); await esperar(50);
  confere(/Reiniciar agendado para/.test($("s-body").textContent) && porTexto($("s-body"), "Cancelar agendamento").length === 1, "agendado: mostra o que está armado e como cancelar");
  rotas["/api/power"] = { scheduled: null };
  porTexto($("s-body"), "Cancelar agendamento")[0].listeners.click(); await esperar(30);
  confere(posts.some((x) => x.rota === "/api/power" && x.corpo.action === "cancel") && !/agendado para/.test($("s-body").textContent), "cancelar o agendamento");
  const selAg = (rot) => [...$("s-body").walk()].find((e) => e.tag === "select" && e.attrs["aria-label"] === rot);
  const oqueSel = selAg("O quê"), quandoSel = selAg("Agendar");
  oqueSel.value = "poweroff"; quandoSel.value = "at"; quandoSel.onchange();
  const campoHora = [...$("s-body").walk()].find((e) => e.tag === "input" && e.attrs.type === "time");
  confere(campoHora && campoHora.hidden === false, "um horário: aparece o campo de hora");
  campoHora.value = "04:15";
  rotas["/api/power"] = { scheduled: { action: "poweroff", at: Math.floor(Date.now() / 1000) + 7200 } };
  const antesAg = posts.length;
  porTexto($("s-body"), "Agendar").filter((e) => e.tag === "button")[0].listeners.click(); await esperar(30);
  confere(posts.slice(antesAg).some((x) => x.rota === "/api/power" && x.corpo.action === "poweroff" && x.corpo.at === "04:15"), "agendar: envia a ação e o horário");
  confere(/Desligar agendado para/.test($("s-body").textContent), "e mostra o agendamento");
  // network: the three choices, the state of each piece, what the host still needs, and Apply starts the qh job
  rotas["/api/network"] = { mode: "tailscale", chosen: false, server_url: "http://192.168.1.10:8093", tailnet: "",
    tailscale: { installed: false, active: false, backend: null, ip: null, domain: null, operator: false },
    headscale: { installed: false, active: false }, tsdproxy: { installed: true, active: true, authkey: true }, access: null,
    commands: { install: ["sudo transactional-update pkg install tailscale"], service: ["sudo systemctl enable --now tailscaled"], operator: ["sudo tailscale set --operator=$USER"] } };
  rotas["/api/job/jn"] = { output: "network: headscale\n", next: 1, rc: 0 };
  await api.openSettings(); await esperar(50);
  confere(/Rede \(tailnet\)/.test($("s-body").textContent) && /Só local/.test($("s-body").textContent) && /Headscale/.test($("s-body").textContent), "Rede: as três escolhas");
  confere(/Tailscale no host: não instalado/.test($("s-body").textContent) && /tsdproxy: rodando/.test($("s-body").textContent), "Rede: o estado de cada peça");
  confere(/sudo transactional-update pkg install tailscale/.test($("s-body").textContent), "Rede: o que falta no host, como comando para copiar");
  porTexto($("s-body"), "Headscale")[0].listeners.click();
  confere(/Endereço do servidor Headscale/.test($("s-body").textContent) && /Nome da rede/.test($("s-body").textContent) && /HTTP na tailnet/.test($("s-body").textContent), "Rede: escolher Headscale pede o endereço e o nome, e avisa do HTTP");
  const campoNome = [...$("s-body").walk()].find((e) => e.tag === "input" && e.attrs["aria-label"] === "Nome da rede");
  campoNome.value = "casa";
  rotas["/api/network"] = { ...rotas["/api/network"], mode: "headscale" };
  const antesNet = posts.length;
  const aplicarRede = porTexto($("s-body"), "Aplicar").pop();
  aplicarRede.listeners.click(); await esperar(1200);
  const envNet = posts.slice(antesNet).find((x) => x.rota === "/api/network");
  confere(envNet && envNet.corpo.mode === "headscale" && envNet.corpo.tailnet === "casa" && envNet.corpo.server_url === "http://192.168.1.10:8093", `Rede: Aplicar manda a escolha (${JSON.stringify(envNet && envNet.corpo)})`);
  rotas["/api/network"] = { ...rotas["/api/network"], mode: "tailscale" };
  // appearance: picking applies at once, on <html>, and is saved on the server
  confere(/Aparência/.test($("s-body").textContent) && /Cor de destaque/.test($("s-body").textContent) && /Imagem de fundo/.test($("s-body").textContent), "Configurações: seção de aparência");
  const antesAp = posts.length;
  rotas["/api/ui"] = { ...rotas["/api/ui"], theme: "dark", accent: "teal", density: "compact" };     // what the server answers once saved
  [...$("s-body").walk()].find((e) => e.tag === "button" && e.attrs["aria-label"] === "Petróleo").listeners.click(); await esperar(30);
  porTexto($("s-body"), "Escuro")[0].listeners.click(); await esperar(30);
  porTexto($("s-body"), "Compacta")[0].listeners.click(); await esperar(30);
  const raizAttr = document.documentElement.attrs;
  confere(raizAttr["data-accent"] === "teal" && raizAttr["data-theme"] === "dark" && raizAttr["data-density"] === "compact", `aplica na hora, no <html> (${JSON.stringify(raizAttr)})`);
  rotas["/api/ui"] = { ...rotas["/api/ui"], icon_size: "large", depth: "soft" };
  porTexto($("s-body"), "Grande")[0].listeners.click(); await esperar(30);
  porTexto($("s-body"), "Com profundidade e cor")[0].listeners.click(); await esperar(30);
  confere(document.documentElement.attrs["data-isize"] === "large" && document.documentElement.attrs["data-depth"] === "soft", "tamanho dos ícones e fundo com profundidade aplicam na hora");
  const salvos = posts.slice(antesAp).filter((x) => x.rota === "/api/ui").map((x) => { const { lang, ...resto } = x.corpo; return JSON.stringify(resto); });
  confere(salvos.join(" ") === '{"accent":"teal"} {"theme":"dark"} {"density":"compact"} {"icon_size":"large"} {"depth":"soft"}', `e salva cada escolha no servidor (${salvos})`);
  confere(porTexto($("s-body"), "Escuro")[0].attrs["aria-pressed"] === "true" && porTexto($("s-body"), "Claro")[0].attrs["aria-pressed"] === "false", "o botão escolhido fica marcado");
  rotas["/api/ui"] = { ...rotas["/api/ui"], background: true, bg_version: 5 };
  await api.openSettings(); await esperar(50);
  confere(/Alertas/.test($("s-body").textContent) && /Disco cheio/.test($("s-body").textContent) && /Backup falhou/.test($("s-body").textContent), "Configurações: seção de alertas");
  const entradas = [...$("s-body").walk()].filter((e) => e.tag === "input" && ["text", "password"].includes(e.attrs.type)
    && !["Nome da rede", "Endereço do servidor Headscale"].includes(e.attrs["aria-label"]));
  confere(entradas.length === 3 && entradas[2].attrs.placeholder && /já definido/.test(entradas[2].attrs.placeholder), "o token já definido não volta: só o aviso");
  entradas[0].value = "https://ntfy.example.org"; entradas[1].value = "lab";
  const antesAl = posts.length;
  porTexto($("s-body"), "Enviar teste")[0].listeners.click(); await esperar(80);
  const salvou = posts.slice(antesAl).find((x) => x.rota === "/api/alerts");
  confere(salvou && salvou.corpo.server === "https://ntfy.example.org" && salvou.corpo.topic === "lab" && salvou.corpo.token === undefined && salvou.corpo.kinds.disk === true, `alertas: salva sem reenviar o token (${JSON.stringify(salvou && salvou.corpo)})`);
  confere(posts.slice(antesAl).some((x) => x.rota === "/api/alerts/test"), "o teste só sai depois de salvar");
  const rBoth = [...$("s-body").walk()].find((e) => e.tag === "input" && e.attrs.value === "both");
  rBoth.listeners.change();
  rotas["/api/settings"] = { ...rotas["/api/settings"], access: "both", default: false, drift: [] };
  const antesCfg = posts.length;
  porTexto($("s-body"), "Aplicar aos instalados")[0].listeners.click(); await esperar(1000);
  confere(posts.slice(antesCfg).some((x) => x.rota === "/api/settings" && x.corpo.access === "both" && x.corpo.apply === true), "Aplicar aos instalados envia a regra com apply");
  $("settings").open = false;

  // update everything: two clicks, then a window with the job
  const ua = api.S.apps.find((x) => x.id === "homebox");
  ua.units = [unidade("homebox", { drift: "changed" })];
  api.setView("apps");
  const botaoTodos = [...$("summary").walk()].find((e) => e.tag === "button" && e.attrs.id === "update-all");
  confere(!!botaoTodos && /Atualizar todos \(1\)/.test(botaoTodos.textContent), `Meus apps: botão Atualizar todos com a contagem (${botaoTodos && botaoTodos.textContent})`);
  rotas["/api/update-all"] = { job: "ju", apps: ["homebox"] }; rotas["/api/job/ju"] = { output: "homebox ok\n", next: 1, rc: 0 };
  const antesTodos = posts.length;
  botaoTodos.listeners.click({ target: botaoTodos });
  confere(posts.length === antesTodos && /Confirmar/.test(botaoTodos.textContent), "o primeiro clique só pede confirmação");
  botaoTodos.listeners.click({ target: botaoTodos }); await esperar(1200);
  confere(posts.slice(antesTodos).some((x) => x.rota === "/api/update-all") && /homebox ok/.test($("b-out").textContent), "o segundo clique atualiza, e a janela mostra a saída");
  ua.units = [unidade("homebox")];
  api.renderGrid(); $("bulk").open = false;

  // delete the data: a tick, a typed name, and the purge rides on the remove
  api.openPanel("homebox"); await esperar(30);
  porTexto($("p-danger"), "Remover")[0].listeners.click(); await esperar(100);
  const tick = [...$("p-form").walk()].find((e) => e.tag === "input" && e.attrs.id === "purge");
  const blocoPurge = [...$("p-form").walk()].find((e) => e.attrs && e.attrs.class === "purge");
  confere(!!tick && blocoPurge.hidden === true, "remover: a opção de apagar dados começa desligada");
  tick.checked = true; tick.listeners.change({ target: tick });
  confere(blocoPurge.hidden === false && /não tem volta/.test(blocoPurge.textContent), "marcar mostra o aviso e pede o nome");
  [...$("p-form").walk()].find((e) => e.attrs && e.attrs.id === "purge-confirm").value = "homebox";
  rotas["/api/run"] = { job: "jp" }; rotas["/api/job/jp"] = { output: "removed\n", next: 1, rc: 0 };
  const antesPurge = posts.length;
  await $("p-form").onsubmit({ preventDefault() {} }); await esperar(1000);
  const apagou = posts.slice(antesPurge).find((x) => x.rota === "/api/run");
  confere(apagou && apagou.corpo.action === "remove" && apagou.corpo.purge === true && apagou.corpo.confirm === "homebox", `o remove leva purge e o nome digitado (${JSON.stringify(apagou && apagou.corpo)})`);
  $("panel").open = false;

  // notes: what used to be an app's README
  const hn = api.S.apps.find((x) => x.id === "homebox");
  hn.notes = { en: "Open the page.\n\n### Password\n\nIt is generated.", pt: "Open the page.\n\n### Password\n\nIt is generated." };
  api.openPanel("homebox"); await esperar(30);
  confere($("p-notes").hidden === false && /Notas/.test($("p-notes-title").textContent), `painel: notas (${$("p-notes-title").textContent})`);
  confere(/Open the page/.test($("p-notes-body").textContent) && /Password/.test($("p-notes-body").textContent), "as notas aparecem, renderizadas");
  hn.notes = null;
  api.openPanel("homebox"); await esperar(30);
  confere($("p-notes").hidden === true, "sem notas: nada");
  $("panel").open = false;

  // permissions: what the unit asks for, read from the unit, shown before the install
  hn.permissions = [{ kind: "podman_socket", items: [] }, { kind: "devices", items: ["/dev/kvm"] }];
  api.openPanel("homebox"); await esperar(30);
  confere($("p-perms").hidden === false && /Controla todo o seu Podman/.test($("p-perms").textContent) && /\/dev\/kvm/.test($("p-perms").textContent), `painel: permissões (${$("p-perms").textContent})`);
  hn.permissions = [];
  api.openPanel("homebox"); await esperar(30);
  confere($("p-perms").hidden === true, "sem permissões sensíveis: nada");
  $("panel").open = false;

  // minimum Podman: the panel says when the host is older than the app needs
  api.S.podman = "4.9.0";
  Object.assign(api.S.apps.find((x) => x.id === "homebox"), { podman_too_old: true, min_podman: "5.0" });
  api.openPanel("homebox"); await esperar(50);
  confere(/precisa do Podman 5\.0\+; o host tem 4\.9\.0/.test($("p-notice").textContent), `painel: Podman antigo (${$("p-notice").textContent})`);
  api.S.apps.find((x) => x.id === "homebox").podman_too_old = false;
  $("panel").open = false;

  // HTTPS: warned only where the rule in force is plain HTTP (local)
  hn.requires_https = true; api.S.rule = "local";
  api.openPanel("homebox"); await esperar(30);
  confere(/precisa de HTTPS/.test($("p-notice").textContent) && !$("p-notice").hidden, `painel: aviso de HTTPS (${$("p-notice").textContent})`);
  api.S.rule = "tailnet";
  api.openPanel("homebox"); await esperar(30);
  confere($("p-notice").hidden === true, "pela tailnet: sem aviso de HTTPS");
  hn.requires_https = false;
  $("panel").open = false;

  // trial: the notice says when it ends, there is a Keep button, and the install form offers the choice
  api.S.apps.find((x) => x.id === "homebox").trial = { mode: "time", expires: Date.now() / 1000 + 5 * 3600 + 60, purge: false };
  api.openPanel("homebox"); await esperar(50);
  confere(/Experimento: termina em 5 h/.test($("p-notice").textContent) && /ficam no fim/.test($("p-notice").textContent),
    `painel: o aviso de experimento diz quando termina (${$("p-notice").textContent})`);
  confere(botoes($("p-actions")).some((b) => b.textContent === "Manter"), "painel: botão Manter");
  api.S.apps.find((x) => x.id === "homebox").trial = { mode: "reboot", expires: null, purge: true };
  api.openPanel("homebox"); await esperar(50);
  confere(/próximo reinício/.test($("p-notice").textContent) && /serão apagados/.test($("p-notice").textContent), "até reiniciar, com os dados apagados");
  $("panel").open = false;
  api.S.apps.find((x) => x.id === "homebox").trial = null;
  api.openPanel("homebox"); await esperar(50);
  confere($("p-notice").hidden === true && !botoes($("p-actions")).some((b) => b.textContent === "Manter"), "sem experimento: sem aviso nem Manter");
  $("panel").open = false;

  // Customize: the form shows what the unit carries, and sends the whole list back
  api.openPanel("homebox"); await esperar(100);
  const personalizar = await cfgBtn("Personalizar");
  confere(!!personalizar, "o painel de um app instalado tem o botão Personalizar");
  personalizar.listeners.click(); await esperar(100);
  const formulario = () => folhaC;
  const linhasDe = (titulo) => [...[...formulario().walk()].filter((e) => e.attrs && e.attrs.class === "cust-group")
    .find((x) => x.kids[0] && x.kids[0].textContent.startsWith(titulo)).walk()].filter((e) => e.attrs && e.attrs.class === "cust-row");
  confere($("custom").open, "a tela Personalizar abre");
  confere(linhasDe("Portas").length === 2 && linhasDe("Volumes").length === 2 && linhasDe("Variáveis").length === 1, "mostra o que a unit tem: portas, volumes e variável");
  const opaca = linhasDe("Portas")[1];
  confere(/\$\{DNS\}:53:53\/udp/.test(opaca.textContent) && /vem da unit/.test(opaca.textContent) && ![...opaca.walk()].some((e) => e.tag === "input"),
    "a entrada de forma não simples aparece como está, sem campo");
  confere(/não delega os controladores memory e cpu/.test(formulario().textContent) && /Delegate=/.test(formulario().textContent),
    "sem os controladores: avisa o motivo e como ligar");
  const deslizantes = () => [...formulario().walk()].filter((e) => e.tag === "input" && e.attrs.type === "range");
  confere(deslizantes().length === 2 && deslizantes().every((x) => x.attrs.disabled !== undefined), "os campos de limite aparecem, desligados, quando o host não delega");
  confere(/ficam em Configurar/.test(formulario().textContent) && !/desmarcar a comenta/.test(formulario().textContent),
    "a dica das variáveis é a da personalização, não a do formulário do .env");
  confere(!porTexto(formulario(), "Reverter ao padrão").length, "sem personalização, não há botão de reverter");
  confere(/Pastas permitidas para volumes novos: ~\/\.config\/containers\/volumes/.test(formulario().textContent), "diz onde um volume novo pode morar");
  const caps = (n) => [...formulario().walk()].find((e) => e.id === `cap-homebox-${n}`);
  confere(caps("CHOWN").checked && !caps("KILL").checked, "capabilities: marca as que a unit tem");
  porTexto(formulario(), "+ Adicionar")[0].listeners.click(); await esperar(20);
  const [, hostIn, contIn] = [...linhasDe("Portas")[2].walk()].filter((e) => e.tag === "input");
  hostIn.value = "8123"; contIn.value = "80";
  [...linhasDe("Volumes")[0].walk()].find((e) => e.tag === "button" && e.attrs.class === "x").listeners.click(); await esperar(20);
  confere(linhasDe("Volumes").length === 1, "remover tira a linha do volume");
  porTexto(folhaC, "Pré-visualizar")[0].listeners.click(); await esperar(100);
  const pre = posts.filter((x) => x.rota === "/api/custom/preview").pop().corpo;
  confere(pre.unit === "homebox" && pre.config.ports.length === 3, "o payload leva a lista inteira de portas");
  confere(JSON.stringify(pre.config.ports[2]) === '{"bind":"","host":8123,"container":80,"proto":"tcp"}', "a porta nova, com os tipos certos");
  confere(pre.config.ports[1].opaque === true && pre.config.ports[1].raw === "${DNS}:53:53/udp", "a entrada opaca volta intacta");
  confere(pre.config.volumes.length === 1 && pre.config.volumes[0].host === "%h/b" && pre.config.volumes[0].ro === true, "o volume removido não vai; o outro mantém as opções");
  confere(pre.config.caps.length === 1 && pre.config.caps[0].name === "CHOWN" && pre.config.restart === "always", "capabilities e reinício");
  confere(!/null|undefined/.test(folhaC.textContent), "nenhum 'null' solto na tela");
  confere(/rede local/.test(formulario().textContent) && /PublishPort=/.test(formulario().textContent) && /podman run x/.test(formulario().textContent),
    "a pré-visualização mostra o aviso, o arquivo e o comando gerado");
  rotas["/api/custom/preview"] = { errors: ["volume '/etc': fora das pastas permitidas"], warnings: [], text: null, generated: "", changed: false };
  const antes = posts.length;
  porTexto(folhaC, "Salvar e aplicar")[0].listeners.click(); await esperar(150);
  confere(!posts.slice(antes).some((x) => x.rota === "/api/custom/apply") && /fora das pastas/.test(formulario().textContent), "com erro, o Salvar não aplica e mostra o motivo");
  rotas["/api/custom/preview"] = { errors: [], warnings: [], text: "[Container]\nPublishPort=\n", generated: "", changed: true };
  rotas["/api/custom"] = { ...rotas["/api/custom"], override: true, text: "x" };
  porTexto(folhaC, "Salvar e aplicar")[0].listeners.click(); await esperar(1500);
  const ap = posts.filter((x) => x.rota === "/api/custom/apply").pop();
  confere(ap && ap.corpo.config.ports.length === 3, "sem erro, aplica com a configuração do formulário");
  confere(!$("custom").open, "aplicado: a tela fecha");
  (await cfgBtn("Personalizar")).listeners.click(); await esperar(100);
  confere(porTexto(formulario(), "Reverter ao padrão").length === 1 && /50-store\.conf/.test(formulario().textContent), "reaberta: o arquivo e o botão de reverter");
  porTexto(formulario(), "Reverter ao padrão")[0].listeners.click(); await esperar(1500);
  confere(posts.some((x) => x.rota === "/api/custom/reset" && x.corpo.unit === "homebox"), "reverter chama o reset da unit");
  // the .container as text: shown, edited, checked, saved as the person's own after the warnings are acknowledged
  const REPO = "[Container]\nImage=x:1\n";
  rotas["/api/custom"] = { ...rotas["/api/custom"], unit_source: REPO, repo_text: REPO, custom_unit: false, installed_text: REPO, override: false, text: null };
  (await cfgBtn("Personalizar")).listeners.click(); await esperar(100);
  confere(areaRaw() && areaRaw().value === REPO && /O \.container \(código\)/.test(folhaC.textContent) && /pode executar comandos/.test(folhaC.textContent) && /Igual ao repositório/.test(folhaC.textContent),
    "Personalizar mostra o .container, com o aviso e dizendo que é igual ao repositório");
  areaRaw().value = REPO + "PodmanArgs=--privileged\n"; areaRaw().listeners.input();
  confere(/Diferente do repositório/.test(folhaC.textContent), "editado: diz que difere");
  rotas["/api/custom/unit-check"] = { errors: [], warnings: ["PodmanArgs=--privileged: roda com --privileged"], changed: true };
  rotas["/api/custom/unit-save"] = { job: "j1" };
  const antesU = posts.length;
  porTexto(folhaC, "Salvar e aplicar")[0].listeners.click(); await esperar(150);
  confere(!posts.slice(antesU).some((x) => x.rota === "/api/custom/unit-save") && /roda com --privileged/.test(folhaC.textContent) && $("custom").open, "com aviso e sem confirmar, não salva e mostra o aviso");
  const caixaAck = [...folhaC.walk()].find((e) => e.tag === "input" && e.attrs.type === "checkbox" && /rawack-/.test(e.attrs.id || ""));
  caixaAck.checked = true;
  porTexto(folhaC, "Salvar e aplicar")[0].listeners.click(); await esperar(1500);
  const us = posts.slice(antesU).find((x) => x.rota === "/api/custom/unit-save");
  confere(us && us.corpo.unit === "homebox" && us.corpo.text.includes("--privileged") && us.corpo.ack === true && !posts.slice(antesU).some((x) => x.rota === "/api/custom/apply"), "confirmado: salva o .container (e não aplica o formulário junto)");
  rotas["/api/custom/unit-check"] = { errors: ["quadlet: converting x"], warnings: [], changed: true };
  (await cfgBtn("Personalizar")).listeners.click(); await esperar(100);
  areaRaw().value = "lixo"; areaRaw().listeners.input();
  const antesU2 = posts.length;
  porTexto(folhaC, "Salvar e aplicar")[0].listeners.click(); await esperar(150);
  confere(!posts.slice(antesU2).some((x) => x.rota === "/api/custom/unit-save") && /quadlet: converting x/.test(folhaC.textContent), "com erro, não salva");
  rotas["/api/custom"] = { ...rotas["/api/custom"], unit_source: REPO + "Label=a=b\n", custom_unit: true };
  $("custom").open = false;
  (await cfgBtn("Personalizar")).listeners.click(); await esperar(100);
  confere(/É o seu \.container/.test(folhaC.textContent) && porTexto(folhaC, "Voltar ao do repositório").length >= 1, "um .container próprio: diz que é o seu e oferece voltar");
  const antesU3 = posts.length;
  botoes(folhaC).filter((b) => b.textContent === "Voltar ao do repositório" && b.attrs.class && /danger/.test(b.attrs.class))[0].listeners.click(); await esperar(1500);
  confere(posts.slice(antesU3).some((x) => x.rota === "/api/custom/unit-reset" && x.corpo.unit === "homebox"), "voltar ao do repositório chama unit-reset");
  rotas["/api/custom"] = { ...rotas["/api/custom"], custom_unit: false, unit_source: REPO };
  $("panel").open = false;
  // limits, when the host delegates the controllers: the fields are live and ride along in the form
  rotas["/api/custom"] = { ...rotas["/api/custom"], limits: { memory: true, cpu: true }, limit_values: { memory: "1g", cpus: "" } };
  (await cfgBtn("Personalizar")).listeners.click(); await esperar(100);
  const [cm, cc] = deslizantes();
  confere(cm.attrs.disabled === undefined && cc.attrs.disabled === undefined && cm.value === "2" && cc.value === "6" && /Valem na próxima partida/.test(formulario().textContent),
    `com os controladores delegados: deslizantes ligados, no valor atual (1 GB, sem limite de CPU), e a dica (${cm.value}/${cc.value})`);
  cm.value = "3"; cm.listeners.input(); cc.value = "3"; cc.listeners.input();
  porTexto(folhaC, "Pré-visualizar")[0].listeners.click(); await esperar(100);
  const prelim = posts.filter((x) => x.rota === "/api/custom/preview").pop().corpo.config.limits;
  confere(prelim.memory === "2g" && prelim.cpus === "2", `os limites vão na configuração (${JSON.stringify(prelim)})`);
  rotas["/api/custom"] = { ...rotas["/api/custom"], limits: { memory: false, cpu: false }, limit_values: { memory: "", cpus: "" } };
  $("panel").open = false;
  rotas["/api/custom"] = { ...rotas["/api/custom"], override: false };

  // Meus apps × Loja: what is installed as a launcher, the catalog as somewhere to browse
  api.setView("apps");
  const grade = $("grid");
  const tiles = grade.kids.filter((k) => k.attrs && /tile/.test(k.attrs.class || ""));
  confere(grade.className === "apps" && tiles.length === 2, `Meus apps: só os 2 instalados, em azulejos (${tiles.length})`);
  confere(!/Gitea/.test(grade.textContent), "Meus apps: o que não está instalado não aparece");
  const abas = ["tab-apps", "tab-store"].map($);
  confere(/Meus apps2/.test(abas[0].textContent) && /Loja3/.test(abas[1].textContent), "abas com contagem");
  confere(abas[0].attrs["aria-selected"] === "true" && $("groups").hidden === false
    && botoes($("groups")).length === 3 && !/Ferramentas|Produtividade/.test($("groups").textContent), "a aba ativa é Meus apps, com filtros e sem categorias");
  const doMemos = tiles.find((k) => /Memos/.test(k.textContent)), doHome = tiles.find((k) => /Homebox/.test(k.textContent));
  const ancora = [...doMemos.walk()].find((e) => e.tag === "a");
  confere(ancora && ancora.attrs.href === "https://memos.example.ts" && ancora.attrs.target === "_blank" && /noopener/.test(ancora.attrs.rel),
    "azulejo com endereço único: o clique abre o app em outra aba");
  menuCtx(doMemos);
  const gerenciar = porTexto($("ctx"), "Gerenciar")[0];
  confere($("ctx").classList.contains("open") && !!gerenciar, "o menu tem Gerenciar");
  gerenciar.listeners.click(); await esperar(50);
  confere(api.current().id === "memos" && $("panel").open && !$("ctx").classList.contains("open"), "Gerenciar abre o painel do app e fecha o menu");
  $("panel").open = false;
  confere(![...doHome.walk()].some((e) => e.tag === "a"), "azulejo sem endereço: um botão só, que abre o painel");
  api.S.search = "gitea"; api.renderGrid();
  confere(/Nenhum app encontrado\./.test($("empty").textContent), "busca sem resultado diz isso");
  api.S.search = "";
  api.setView("store");
  const cartoes = grade.kids.filter((k) => k.attrs && k.attrs.class === "card");
  confere(grade.className === "" && cartoes.length === 3 && /Gitea/.test(grade.textContent), "Loja: o catálogo todo, em cartões");
  confere($("groups").hidden === false, "Loja: com categorias");
  confere(cartoes.find((k) => /Homebox/.test(k.textContent)).textContent.includes("instalado")
    && !cartoes.find((k) => /Gitea/.test(k.textContent)).textContent.includes("instalado"), "Loja: marca o que já está instalado");
  const guardados = api.S.apps; api.S.apps = guardados.map((a) => ({ ...a, installed: false }));
  api.setView("apps");
  const botaoLoja = [...$("empty").walk()].find((e) => e.tag === "button");
  confere(/Nenhum app instalado ainda\./.test($("empty").textContent) && botaoLoja && /Abrir a Loja/.test(botaoLoja.textContent), "sem instalados: convida a abrir a Loja");
  botaoLoja.listeners.click(); await esperar(20);
  confere(api.S.view === "store", "…e o botão leva à Loja");

  api.S.apps = guardados;

  // Quick Launch: any letter typed on the page opens the search; installed first; Enter takes the highlighted one
  for (const id of ["panel", "custom", "settings", "history", "resources", "bulk", "ql"]) $(id).open = false;
  docOuvintes.keydown({ key: "m", target: { tagName: "BODY" }, preventDefault() {} });
  confere($("ql").open && $("ql-input").value === "m", "Quick Launch: uma letra na página abre a busca com ela");
  const itensQl = () => [...$("ql-list").walk()].filter((e) => e.attrs && e.attrs.role === "option");
  confere(/Memos/.test(itensQl()[0].textContent) && /Abrir/.test(itensQl()[0].textContent) && /na web/.test(itensQl().pop().textContent),
    `instalado primeiro, com Abrir, e a busca na web por último (${itensQl().map((e) => e.textContent).join(" | ")})`);
  global.abertos = [];
  $("ql-input").listeners.keydown({ key: "Enter", preventDefault() {} });
  confere(!$("ql").open && global.abertos.length === 1 && global.abertos[0][0] === "https://memos.example.ts", `Enter abre o app (${JSON.stringify(global.abertos)})`);
  docOuvintes.keydown({ key: "g", target: { tagName: "BODY" }, preventDefault() {} });
  $("ql-input").value = "git"; $("ql-input").listeners.input();
  confere(/Gitea/.test(itensQl()[0].textContent) && /Ver na loja/.test(itensQl()[0].textContent), "o que não está instalado leva à página na loja");
  $("ql-input").listeners.keydown({ key: "ArrowDown", preventDefault() {} });
  $("ql-input").listeners.keydown({ key: "Enter", preventDefault() {} });
  confere(global.abertos.some((a) => /duckduckgo\.com\/\?q=git/.test(a[0])), "a seta desce até a busca na web, e Enter a abre");
  $("ql").open = false;
  docOuvintes.keydown({ key: "a", target: { tagName: "INPUT" }, preventDefault() {} });
  confere(!$("ql").open, "digitar num campo não abre a busca");
  $("panel").open = true;
  docOuvintes.keydown({ key: "a", target: { tagName: "BODY" }, preventDefault() {} });
  confere(!$("ql").open, "com uma janela aberta, também não");
  $("panel").open = false;

  // service widgets: two numbers on the tile, all of them in the panel, the key typed there and never shown back
  api.S.svc = { homebox: [{ type: "immich", unit: "homebox", slot: "homebox", auth: ["key"], configured: true, url: true,
    fields: [{ key: "photos", value: 12400, kind: "count", level: null }, { key: "storage", value: 5 * 2 ** 30, kind: "bytes", level: null },
             { key: "videos", value: 30, kind: "count", level: "warn" }] }] };
  api.setView("apps"); api.renderGrid();
  const linhaSvc = [...$("grid").walk()].find((e) => e.attrs && /svc-line/.test(e.attrs.class || ""));
  confere(linhaSvc && /12k fotos/.test(linhaSvc.textContent) && /5\.0 GB armazenamento/.test(linhaSvc.textContent) && !/vídeos/.test(linhaSvc.textContent),
    `widget: o azulejo mostra os dois primeiros números (${linhaSvc && linhaSvc.textContent})`);
  api.openPanel("homebox"); await esperar(30);
  confere(!$("p-svc").hidden && /Números do app/.test($("p-svc").textContent) && /30vídeos/.test($("p-svc").textContent.replace(/\s/g, "")), `widget: o painel mostra todos (${$("p-svc").textContent})`);
  confere([...$("p-svc").walk()].some((e) => e.attrs && e.attrs.class === "svc-stat lv-warn"), "widget: o destaque pinta o número");
  porTexto($("p-svc"), "Configurar widget")[0].listeners.click(); await esperar(20);
  const chaveSvc = [...$("p-section").walk()].find((e) => e.tag === "input" && e.attrs["aria-label"] === "Chave de API");
  confere(chaveSvc && chaveSvc.attrs.type === "password" && /já definida/.test(chaveSvc.attrs.placeholder) && /Chaves de API/.test($("p-section").textContent),
    "widget: a chave é um campo de senha, já definida não volta, e a tela diz onde achar");
  rotas["/api/svc/config"] = { apps: api.S.svc };
  chaveSvc.value = "nova-chave";
  const antesSvc = posts.length;
  porTexto($("p-section"), "Salvar")[0].listeners.click(); await esperar(40);
  const envSvc = posts.slice(antesSvc).find((x) => x.rota === "/api/svc/config");
  confere(envSvc && envSvc.corpo.slot === "homebox" && envSvc.corpo.values.key === "nova-chave" && !("url" in envSvc.corpo.values), `widget: salva a chave no servidor (${JSON.stringify(envSvc && envSvc.corpo)})`);
  api.S.svc = { homebox: [{ type: "immich", unit: "homebox", slot: "homebox", auth: ["key"], configured: true, url: true, error: "HTTP 401" }] };
  api.renderGrid();
  confere([...$("grid").walk()].some((e) => e.attrs && /svc-line/.test(e.attrs.class || "") && e.attrs.title === "HTTP 401"), "widget: uma chave recusada vira um aviso discreto no azulejo");
  api.S.svc = {}; api.renderGrid(); $("panel").open = false;

  // icon plates: the tone comes from the logo; app.json `icon` (bg, fit, tone) wins over it
  const doApp = (cfg) => ({ id: "x", icon: "/assets/x/icon.svg", icon_cfg: cfg });
  let pl = api.iconPlate(doApp({ bg: "#12352a", fit: 1.2 }));
  confere(pl.attrs["data-custom"] === "1" && pl.style["--bgc"] === "#12352a" && pl.style["--fit"] === "1.2", `icon.bg e icon.fit valem sobre o automático (${JSON.stringify(pl.style)})`);
  pl = api.iconPlate(doApp({ tone: "full", bg: "#000000" }));
  confere(pl.attrs["data-tone"] === "full" && !pl.attrs["data-custom"], "tom 'full': o logo preenche, e a cor de fundo não vale");
  pl = api.iconPlate(doApp({ tone: "dark" }));
  confere(pl.attrs["data-tone"] === "dark", "icon.tone escolhe a placa");
  pl = api.iconPlate(doApp(null));
  confere(!pl.attrs["data-tone"] && /^\d+$/.test(pl.style["--h"]), "sem nada no app.json: placa clara, com um matiz provisório até o logo ser lido");

  // home: greeting, the server at a glance (four cards), and what was used last
  api.S.view = "apps"; api.S.search = ""; api.S.filter = null;
  api.S.hostData = { cpus: 4, load: 1, cpu: { pct: 12.4 }, mem: { total: 8, used: 2 }, disk: { total: 100, used: 65 }, net: { rx_rate: 2048, tx_rate: 1 } };
  api.S.hist = { cpu: [10, 20, 12], mem: [25, 25], disk: [65], net: [1024, 2048] };
  api.S.recent = [];
  api.renderHome();
  confere(/Bom dia|Boa tarde|Boa noite/.test($("home").textContent) && [...$("home").walk()].filter((e) => e.attrs && e.attrs.class === "stat").length === 4, "início: saudação e quatro cartões do servidor");
  confere(/12%/.test($("home").textContent) && /25%/.test($("home").textContent) && /65%/.test($("home").textContent) && /↓ 2 KB\/s/.test($("home").textContent), `início: os números (${$("home").textContent.slice(0, 120)})`);
  confere(!/Usados recentemente/.test($("home").textContent), "sem uso ainda: sem a fileira de recentes");
  api.touchRecent("homebox"); api.renderHome();
  confere(/Usados recentemente/.test($("home").textContent) && /Homebox|HomeBox/i.test($("home").textContent) && /Todos os apps/.test($("home").textContent), "depois de abrir um app, ele aparece em Usados recentemente");
  api.S.search = "memos"; api.renderHome();
  confere($("home").kids.length === 0, "ao buscar, o início some e fica só o resultado");
  api.S.search = ""; api.renderHome();

  // navigation: open at the start, folds to icons, and remembers
  const nav = () => document.body.dataset.nav;
  confere(nav() === "open", "a barra lateral começa aberta");
  $("nav-toggle").listeners.click();
  confere(nav() === "collapsed" && guardado.get("qh-nav") === "collapsed", "recolher: fica só nos ícones e guarda a escolha");
  $("nav-toggle").listeners.click();
  confere(nav() === "open" && guardado.get("qh-nav") === "open", "e expande de volta");

  console.log(falhas ? `\n${falhas} falha(s)` : "\ntudo passou");
  process.exit(falhas ? 1 : 0);
})();

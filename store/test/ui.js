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
    this.hidden = false; this.open = false; this.disabled = false; this.checked = false; this.value = ""; this.id = ""; this.className = ""; }
  setAttribute(k, v) { this.attrs[k] = v; if (k === "id") this.id = v;
    if (k === "value") this.value = v; if (k === "checked") this.checked = true; if (k === "disabled") this.disabled = true;
    if (k.startsWith("data-")) this.dataset[k.slice(5).replace(/-(.)/g, (_, c) => c.toUpperCase())] = v; }
  addEventListener(e, f) { this.listeners[e] = f; }
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
  hidden: false, documentElement: new El("html"),
  createElement: (t) => new El(t), createTextNode: (s) => new Txt(s),
  getElementById: (id) => (byId[id] ||= Object.assign(new El("div"), { id })),
  querySelector: (sel) => { for (const e of Object.values(byId)) { const r = e.querySelector(sel); if (r) return r; } return null; },
};
global.Node = El;
global.localStorage = { getItem: () => "pt", setItem() {} };
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
  if (opts.method === "POST") posts.push({ rota, corpo: JSON.parse(opts.body) });
  if (!(rota in rotas)) return { status: 404, ok: false, json: async () => ({ error: "404 " + rota }) };
  return { status: 200, ok: true, json: async () => rotas[rota] };
};

const codigo = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const api = new Function(codigo + "; return { S, openPanel, showEnv, current, renderGrid, pollStats, pollHost, openSettings, showLogs, showConsole, termNew, termFeed, termKey, openResources, hintClean, openHistory, setView };")();
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
let falhas = 0;
const confere = (cond, msg) => { if (!cond) { falhas++; console.log("FALHOU:", msg); } else console.log("ok   ", msg); };
const $ = (id) => document.getElementById(id);
const botoes = (raiz) => [...raiz.walk()].filter((e) => e.tag === "button");
const porTexto = (raiz, texto) => botoes(raiz).filter((e) => e.textContent === texto);

(async () => {
  await esperar(100);
  const card = document.querySelector('[data-res="homebox"]');
  confere(card && card.textContent === "1.5% · 150 MB", `o azulejo mostra CPU e memória (${card && card.textContent})`);

  // the panel of an installed app: resources, disk, architectures, and no stray "null"
  api.openPanel("homebox"); await esperar(100);
  const info = $("p-info").textContent;
  confere(/CPU 1\.5%/.test(info) && /Memória 150 MB/.test(info) && /Disco 5 MB/.test(info), `painel: CPU, memória e disco (${info})`);
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

  // gallery, project links, history
  const shots = $("p-shots");
  confere(!shots.hidden && [...shots.walk()].filter((e) => e.tag === "img").length === 2, "galeria: duas capturas");
  confere([...shots.walk()].filter((e) => e.tag === "a").every((a) => a.attrs.target === "_blank" && /noopener/.test(a.attrs.rel)), "galeria: outra aba, com noopener");
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
  rotas["/api/host"] = { cpus: 4, load: 1, mem: { total: 8 * 2 ** 30, used: 2 * 2 ** 30 }, temp: 50, uptime: 90000 };
  rotas["/api/arch"] = { host: "amd64", runs: ["amd64", "arm64"], units: [{ unit: "homebox", ok: true }] };
  api.openPanel("gitea"); await esperar(100);
  confere($("p-actions").textContent === "InstalarPersonalizarNova instânciaHistórico", `app não instalado: Instalar, Personalizar, Nova instância e Histórico (${$("p-actions").textContent})`);
  confere(!/null|undefined/.test($("p-info").textContent) && /Roda em amd64, arm64$/.test($("p-info").textContent), "app não instalado: info sem 'null'");
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
  confere($("p-actions").textContent === "Histórico", `painel: sem botão de instalar (${$("p-actions").textContent})`);
  $("panel").open = false;
  api.setView("apps");
  const azulejoMemos = $("grid").kids.find((k) => /Memos/.test(k.textContent));
  confere(/descontinuado/.test(azulejoMemos.textContent), "Meus apps: o azulejo de um instalado também leva o selo");
  api.openPanel("memos"); await esperar(50);
  confere(/Descontinuado: Arquivado no upstream\./.test($("p-notice").textContent) && !/Não dá para instalar/.test($("p-notice").textContent),
    "instalado: mostra o motivo, sem dizer que não instala");
  confere(botoes($("p-actions")).some((b) => b.textContent === "Remover"), "instalado: continua dando para gerenciar e remover");
  $("panel").open = false;
  api.openPanel("homebox"); await esperar(50);
  confere($("p-notice").hidden === true, "um app sem marca não mostra aviso");
  $("panel").open = false;
  api.S.apps.find((x) => x.id === "gitea").deprecated = null;
  api.S.apps.find((x) => x.id === "memos").deprecated = null;

  // host summary: one line at the top
  await api.pollHost();
  confere($("host").textContent === "carga 25% · RAM 2.0/8.0 GB · 50 °C · ligado há 1 d", `topo: resumo do servidor (${$("host").textContent})`);

  // resources: the dialog lists what is unused and prunes in two clicks; volumes want the word
  rotas["/api/resources"] = { reclaimable: 3 * 2 ** 30, networks: [{ name: "stray" }], volumes: [{ name: "vf" }],
    images: [{ id: "i2", name: "docker.io/o/old:1", size: 3 * 2 ** 30, created: 0 }] };
  rotas["/api/prune"] = { job: "j9" };
  rotas["/api/job/j9"] = { output: "removed x\n", next: 1, rc: 0 };
  await api.openResources(); await esperar(30);
  const corpoRec = $("r-body").textContent;
  confere(/Imagens sem uso \(1\)/.test(corpoRec) && /docker\.io\/o\/old:1/.test(corpoRec) && /3\.0 GB/.test(corpoRec) && /Redes sem uso \(1\)/.test(corpoRec) && /Volumes sem uso \(1\)/.test(corpoRec),
    `Recursos: imagens, redes e volumes sem uso (${corpoRec.slice(0, 80)})`);
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
  confere(/parado/.test($("grid").textContent) && !/Atenção|atenção/.test($("grid").textContent), "parado de propósito: selo neutro, não alarme");
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
  porTexto($("p-actions"), "Personalizar")[0].listeners.click(); await esperar(100);
  const formPre = () => [...$("p-section").walk()].find((e) => e.tag === "form");
  confere(!!formPre() && /Antes de instalar/.test(formPre().textContent) && porTexto(formPre(), "Guardar para a instalação").length === 1
    && porTexto(formPre(), "Salvar e aplicar").length === 0, "antes de instalar: o formulário abre, com Guardar e sem Salvar e aplicar");
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
  porTexto(formPre(), "Guardar para a instalação")[0].listeners.click(); await esperar(100);
  global.fetch = fetchAntes;
  if (previaAntes === undefined) delete rotas["/api/custom/preview"]; else rotas["/api/custom/preview"] = previaAntes;
  const prev = posts.filter((x) => x.rota === "/api/custom/preview").pop().corpo;
  confere(prev.pre === true && prev.unit === "gitea", "a prévia leva pre: true");
  confere(urlsPre.some((u) => /\/api\/custom\?unit=gitea&pre=1|\/api\/custom\/preview/.test(u)), "e pede o estado da unit ainda não instalada");
  confere(/Guardado: vai junto/.test($("p-out").textContent), "guardar avisa que vai junto com a instalação");
  api.openPanel("gitea"); await esperar(30);
  confere(porTexto($("p-actions"), "Personalizar ✓").length === 1, "o botão mostra que há personalização guardada");
  rotas["/api/plan"] = { rc: 0, output: "x", nothing: false };
  rotas["/api/run"] = { job: "jr" }; rotas["/api/job/jr"] = { output: "ok\n", next: 1, rc: 0 };
  porTexto($("p-actions"), "Instalar")[0].listeners.click(); await esperar(100);
  confere(/Personalização guardada para gitea/.test($("p-form").textContent), "o formulário de instalação diz que a personalização vai junto");
  const antesRun = posts.length;
  await $("p-form").onsubmit({ preventDefault() {} }); await esperar(1000);
  const instalou = posts.slice(antesRun).find((x) => x.rota === "/api/run");
  confere(instalou && instalou.corpo.action === "install" && instalou.corpo.custom && instalou.corpo.custom.gitea, `a instalação leva a personalização (${JSON.stringify(instalou && Object.keys(instalou.corpo))})`);
  confere(!api.S.preCustom.gitea, "depois de instalar, o que estava guardado é descartado");
  $("panel").open = false;

  // instances: a base app offers "New instance", and the install carries the name; an instance does not offer it
  api.openPanel("gitea"); await esperar(30);
  porTexto($("p-actions"), "Nova instância")[0].listeners.click(); await esperar(30);
  const nomeInst = [...$("p-section").walk()].find((e) => e.tag === "input" && e.attrs.type === "text");
  nomeInst.value = "casa";
  const antesInst = posts.length;
  porTexto($("p-section"), "Criar instância")[0].listeners.click(); await esperar(1200);
  const inst = posts.slice(antesInst).find((x) => x.rota === "/api/run");
  confere(inst && inst.corpo.action === "install" && inst.corpo.instance === "casa" && inst.corpo.app === "gitea", `a instância é criada pelo install com o nome (${JSON.stringify(inst && inst.corpo)})`);
  api.S.apps.find((x) => x.id === "gitea").instance_of = "outro";
  api.openPanel("gitea"); await esperar(30);
  confere(porTexto($("p-actions"), "Nova instância").length === 0 && /instância de outro/.test($("p-desc").textContent), "uma instância não gera outra, e diz de quem é");
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
  await api.openSettings(); await esperar(50);
  confere(/Alertas/.test($("s-body").textContent) && /Disco cheio/.test($("s-body").textContent) && /Backup falhou/.test($("s-body").textContent), "Configurações: seção de alertas");
  const entradas = [...$("s-body").walk()].filter((e) => e.tag === "input" && ["text", "password"].includes(e.attrs.type));
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
  porTexto($("p-actions"), "Remover")[0].listeners.click(); await esperar(100);
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
  const personalizar = porTexto($("p-actions"), "Personalizar")[0];
  confere(!!personalizar, "o painel de um app instalado tem o botão Personalizar");
  personalizar.listeners.click(); await esperar(100);
  const formulario = () => [...$("p-section").walk()].find((e) => e.tag === "form");
  const linhasDe = (titulo) => [...[...formulario().walk()].filter((e) => e.attrs && e.attrs.class === "cust-group")
    .find((x) => x.kids[0] && x.kids[0].textContent.startsWith(titulo)).walk()].filter((e) => e.attrs && e.attrs.class === "cust-row");
  confere(!!formulario() && !$("p-section").hidden, "a tela Personalizar abre");
  confere(linhasDe("Portas").length === 2 && linhasDe("Volumes").length === 2 && linhasDe("Variáveis").length === 1, "mostra o que a unit tem: portas, volumes e variável");
  const opaca = linhasDe("Portas")[1];
  confere(/\$\{DNS\}:53:53\/udp/.test(opaca.textContent) && /vem da unit/.test(opaca.textContent) && ![...opaca.walk()].some((e) => e.tag === "input"),
    "a entrada de forma não simples aparece como está, sem campo");
  confere(/não delega os controladores memory e cpu/.test(formulario().textContent) && /Delegate=/.test(formulario().textContent),
    "sem os controladores: avisa o motivo e como ligar");
  const campoMem = [...formulario().walk()].find((e) => e.id === "lim-mem"), campoCpu = [...formulario().walk()].find((e) => e.id === "lim-cpu");
  confere(campoMem.attrs.disabled !== undefined && campoCpu.attrs.disabled !== undefined, "os campos de limite aparecem, desligados, quando o host não delega");
  confere(/ficam em Configurar/.test(formulario().textContent) && !/desmarcar a comenta/.test(formulario().textContent),
    "a dica das variáveis é a da personalização, não a do formulário do .env");
  confere(!porTexto(formulario(), "Reverter ao padrão").length, "sem personalização, não há botão de reverter");
  confere(/Pastas permitidas para volumes novos: ~\/\.config\/containers\/volumes/.test(formulario().textContent), "diz onde um volume novo pode morar");
  const caps = (n) => [...formulario().walk()].find((e) => e.id === `cap-${n}`);
  confere(caps("CHOWN").checked && !caps("KILL").checked, "capabilities: marca as que a unit tem");
  porTexto(formulario(), "+ Adicionar")[0].listeners.click(); await esperar(20);
  const [, hostIn, contIn] = [...linhasDe("Portas")[2].walk()].filter((e) => e.tag === "input");
  hostIn.value = "8123"; contIn.value = "80";
  [...linhasDe("Volumes")[0].walk()].find((e) => e.tag === "button" && e.attrs.class === "x").listeners.click(); await esperar(20);
  confere(linhasDe("Volumes").length === 1, "remover tira a linha do volume");
  porTexto(formulario(), "Pré-visualizar")[0].listeners.click(); await esperar(100);
  const pre = posts.filter((x) => x.rota === "/api/custom/preview").pop().corpo;
  confere(pre.unit === "homebox" && pre.config.ports.length === 3, "o payload leva a lista inteira de portas");
  confere(JSON.stringify(pre.config.ports[2]) === '{"bind":"","host":8123,"container":80,"proto":"tcp"}', "a porta nova, com os tipos certos");
  confere(pre.config.ports[1].opaque === true && pre.config.ports[1].raw === "${DNS}:53:53/udp", "a entrada opaca volta intacta");
  confere(pre.config.volumes.length === 1 && pre.config.volumes[0].host === "%h/b" && pre.config.volumes[0].ro === true, "o volume removido não vai; o outro mantém as opções");
  confere(pre.config.caps.length === 1 && pre.config.caps[0].name === "CHOWN" && pre.config.restart === "always", "capabilities e reinício");
  confere(!/null|undefined/.test($("p-section").textContent), "nenhum 'null' solto na tela");
  confere(/rede local/.test(formulario().textContent) && /PublishPort=/.test(formulario().textContent) && /podman run x/.test(formulario().textContent),
    "a pré-visualização mostra o aviso, o arquivo e o comando gerado");
  rotas["/api/custom/preview"] = { errors: ["volume '/etc': fora das pastas permitidas"], warnings: [], text: null, generated: "", changed: false };
  const antes = posts.length;
  porTexto(formulario(), "Salvar e aplicar")[0].listeners.click(); await esperar(150);
  confere(!posts.slice(antes).some((x) => x.rota === "/api/custom/apply") && /fora das pastas/.test(formulario().textContent), "com erro, o Salvar não aplica e mostra o motivo");
  rotas["/api/custom/preview"] = { errors: [], warnings: [], text: "[Container]\nPublishPort=\n", generated: "", changed: true };
  rotas["/api/custom"] = { ...rotas["/api/custom"], override: true, text: "x" };
  porTexto(formulario(), "Salvar e aplicar")[0].listeners.click(); await esperar(1500);
  const ap = posts.filter((x) => x.rota === "/api/custom/apply").pop();
  confere(ap && ap.corpo.config.ports.length === 3, "sem erro, aplica com a configuração do formulário");
  confere(porTexto(formulario(), "Reverter ao padrão").length === 1 && /50-store\.conf/.test(formulario().textContent), "depois de aplicado: o arquivo e o botão de reverter");
  porTexto(formulario(), "Reverter ao padrão")[0].listeners.click(); await esperar(1500);
  confere(posts.some((x) => x.rota === "/api/custom/reset" && x.corpo.unit === "homebox"), "reverter chama o reset da unit");
  // limits, when the host delegates the controllers: the fields are live and ride along in the form
  rotas["/api/custom"] = { ...rotas["/api/custom"], limits: { memory: true, cpu: true }, limit_values: { memory: "1g", cpus: "" } };
  porTexto($("p-actions"), "Personalizar")[0].listeners.click(); await esperar(100);
  const cm = [...formulario().walk()].find((e) => e.id === "lim-mem"), cc = [...formulario().walk()].find((e) => e.id === "lim-cpu");
  confere(cm.attrs.disabled === undefined && cc.attrs.disabled === undefined && cm.attrs.value === "1g" && /Valem na próxima partida/.test(formulario().textContent),
    "com os controladores delegados: campos ligados, com o valor atual, e a dica");
  cm.value = "2g"; cc.value = "1.5";
  porTexto(formulario(), "Pré-visualizar")[0].listeners.click(); await esperar(100);
  const prelim = posts.filter((x) => x.rota === "/api/custom/preview").pop().corpo.config.limits;
  confere(prelim.memory === "2g" && prelim.cpus === "1.5", `os limites vão na configuração (${JSON.stringify(prelim)})`);
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
  const engrenagem = [...doMemos.walk()].find((e) => e.tag === "button" && e.attrs.class === "gear");
  confere(!!engrenagem && /Gerenciar/.test(engrenagem.attrs["aria-label"]), "…e a engrenagem gerencia");
  engrenagem.listeners.click(); await esperar(50);
  confere(api.current().id === "memos" && $("panel").open, "a engrenagem abre o painel do app");
  $("panel").open = false;
  confere(![...doHome.walk()].some((e) => e.tag === "a") && ![...doHome.walk()].some((e) => e.attrs && e.attrs.class === "gear"),
    "azulejo sem endereço: um botão só, que abre o painel");
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

  console.log(falhas ? `\n${falhas} falha(s)` : "\ntudo passou");
  process.exit(falhas ? 1 : 0);
})();

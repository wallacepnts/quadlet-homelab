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
  showModal() { this.open = true; } close() { this.open = false; }
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
  "/api/links": { links: [{ kind: "repo", url: "https://github.com/o/r" }, { kind: "releases", url: "https://github.com/o/r/releases" },
    { kind: "recipe", url: "https://github.com/me/qh/tree/main/apps/homebox" }] },
  "/api/history": { entries: [
    { id: "a1", app: "homebox", action: "install", unit: "", start: 1700000000, end: 1700000042, rc: 0, from: "127.0.0.1" },
    { id: "a2", app: "homebox", action: "restart", unit: "homebox", start: 1700000100, end: 1700000101, rc: 1, from: "127.0.0.1" }] },
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
const api = new Function(codigo + "; return { S, openPanel, showEnv, current, renderGrid, pollStats, openHistory, setView };")();
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

  // gallery, project links, history
  const shots = $("p-shots");
  confere(!shots.hidden && [...shots.walk()].filter((e) => e.tag === "img").length === 2, "galeria: duas capturas");
  confere([...shots.walk()].filter((e) => e.tag === "a").every((a) => a.attrs.target === "_blank" && /noopener/.test(a.attrs.rel)), "galeria: outra aba, com noopener");
  confere(/Projeto ↗/.test($("p-project").textContent) && /Releases ↗/.test($("p-project").textContent), "links do projeto");
  await api.openHistory("homebox"); await esperar(50);
  const linhasHist = [...$("h-list").walk()].filter((e) => e.tag === "tr" && e.attrs.class === "run");
  confere($("history").open && linhasHist.length === 2 && /✓/.test(linhasHist[0].textContent) && /✗ 1/.test(linhasHist[1].textContent), "histórico: linhas com o resultado");
  await linhasHist[1].onclick();
  confere(/Job failed/.test($("h-out").textContent) && /de 127\.0\.0\.1/.test($("h-out").textContent), "histórico: a saída e de onde veio");
  $("history").open = false;

  // an app that is not installed, and a host the image supports
  rotas["/api/arch"] = { host: "amd64", runs: ["amd64", "arm64"], units: [{ unit: "homebox", ok: true }] };
  api.openPanel("gitea"); await esperar(100);
  confere($("p-actions").textContent === "InstalarHistórico", `app não instalado: só Instalar e Histórico (${$("p-actions").textContent})`);
  confere(!/null|undefined/.test($("p-info").textContent) && /Roda em amd64, arm64$/.test($("p-info").textContent), "app não instalado: info sem 'null'");
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
  confere(/indisponível aqui/.test(formulario().textContent), "avisa que limite de memória e CPU não existe neste host");
  confere(/ficam em Configurar/.test(formulario().textContent) && !/desmarcar a comenta/.test(formulario().textContent),
    "a dica das variáveis é a da personalização, não a do formulário do .env");
  confere(!porTexto(formulario(), "Reverter ao padrão").length, "sem personalização, não há botão de reverter");
  confere(/Pastas permitidas para volumes novos: ~\/\.config\/containers\/volumes/.test(formulario().textContent), "diz onde um volume novo pode morar");
  const caps = (n) => [...formulario().walk()].find((e) => e.id === `cap-${n}`);
  confere(caps("CHOWN").checked && !caps("KILL").checked, "capabilities: marca as que a unit tem");
  porTexto(formulario(), "+ Adicionar")[0].listeners.click(); await esperar(20);
  const [, hostIn, contIn] = [...linhasDe("Portas")[2].walk()].filter((e) => e.tag === "input");
  hostIn.value = "8123"; contIn.value = "80";
  [...linhasDe("Volumes")[0].walk()].find((e) => e.tag === "button").listeners.click(); await esperar(20);
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
  confere(abas[0].attrs["aria-selected"] === "true" && $("groups").hidden === true, "a aba ativa é Meus apps, sem categorias");
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

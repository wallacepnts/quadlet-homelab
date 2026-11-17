// Drives a real Chromium through the store over the DevTools protocol, takes screenshots and
// reports anything the browser logged (errors, CSP violations). No dependencies: Node's own WebSocket.
//
//     node store/test/browser.js <base-url> <token-file> <out-dir> [real|sandbox]
//
//   real     (default) reads and previews only — it never applies a customization, installs or removes.
//   sandbox  also applies and reverts a customization; point it ONLY at a store started with --prefix.
//
// Screenshots go to <out-dir>. Hostnames of the tailnet are masked in what is printed.
const { spawn } = require("child_process");
const fs = require("fs");
const http = require("http");
const [BASE, TOKEN_FILE, OUT, MODO = "real"] = process.argv.slice(2);
const PORT = 9333, PERFIL = fs.mkdtempSync("/tmp/qh-browser-");
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
const getJSON = (url) => new Promise((res, rej) => http.get(url, (r) => { let d = ""; r.on("data", (c) => d += c); r.on("end", () => { try { res(JSON.parse(d)); } catch (e) { rej(e); } }); }).on("error", rej));
const mascara = (s) => String(s).replace(/[a-z0-9-]+\.ts\.net/g, "<your-tailnet>.ts.net");

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const chrome = spawn("/usr/bin/chromium", ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${PERFIL}`,
    "--window-size=1280,900", "--no-first-run", "--disable-gpu", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
  let alvos;
  for (let i = 0; i < 50; i++) { try { alvos = await getJSON(`http://127.0.0.1:${PORT}/json/list`); if (alvos.length) break; } catch (e) {} await esperar(200); }
  const ws = new WebSocket(alvos.find((a) => a.type === "page").webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = new Map(); const erros = [];
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); return; }
    if (d.method === "Runtime.exceptionThrown") erros.push("EXCEÇÃO: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text));
    if (d.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(d.params.type)) erros.push(`console.${d.params.type}: ` + d.params.args.map((a) => a.value ?? a.description).join(" "));
    if (d.method === "Log.entryAdded" && ["error", "warning"].includes(d.params.entry.level)) erros.push(`log ${d.params.entry.level}: ${d.params.entry.text} ${d.params.entry.url || ""}`.slice(0, 220));
  };
  const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expr) => { const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true }); return r.result?.result?.value; };
  const ate = async (expr, ms = 20000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr)) return true; await esperar(250); } return false; };
  const foto = async (nome) => { const r = await send("Page.captureScreenshot", { format: "png" }); fs.writeFileSync(`${OUT}/${nome}.png`, Buffer.from(r.result.data, "base64")); console.log("foto", nome); };
  const ir = async (url) => { await send("Page.navigate", { url }); await esperar(400); await ate("document.readyState === 'complete'"); };
  const fim = async () => { console.log("\n=== erros e avisos do navegador:", erros.length); [...new Set(erros)].forEach((e) => console.log(" ", e)); ws.close(); chrome.kill(); await esperar(800); fs.rmSync(PERFIL, { recursive: true, force: true, maxRetries: 5 }); process.exit(0); };
  for (const d of ["Page", "Runtime", "Log", "Network"]) await send(d + ".enable");

  const abrir = (nome) => ev(`(() => { const c = [...document.querySelectorAll('.card')].find((x) => x.querySelector('h3').textContent === ${JSON.stringify(nome)}); if (!c) return false; (c.querySelector('.gear') || c.querySelector('.tile-open') || c).click(); return true; })()`);
  const botao = (texto) => ev(`(() => { const b = [...document.querySelectorAll('#panel button')].find((x) => x.textContent === ${JSON.stringify(texto)}); if (!b) return false; b.click(); return true; })()`);
  const tab = async (idt) => { await ev(`document.getElementById('${idt}').click()`); await esperar(500); };
  const grupo = (titulo) => `[...document.querySelectorAll('.cust-group')].find((x) => x.querySelector('h4').textContent.startsWith(${JSON.stringify(titulo)}))`;
  const maisLinha = (titulo) => ev(`(() => { const g = ${grupo(titulo)}; g.querySelector('h4 button').click(); return g.querySelectorAll('.cust-row').length; })()`);
  const poeLinha = (titulo, i, valores) => ev(`(() => { const r = ${grupo(titulo)}.querySelectorAll('.cust-row')[${i}]; const ins = r.querySelectorAll('input'); ${JSON.stringify(valores)}.forEach((v, k) => { ins[k].value = v; }); return ins.length; })()`);
  const clicaForm = (texto) => ev(`(() => { const b = [...document.querySelectorAll('#custom button')].find((x) => x.textContent === ${JSON.stringify(texto)}); if (!b) return false; b.click(); return true; })()`);
  const formTexto = () => ev("document.getElementById('custom').textContent");

  // login: a wrong token first, through the real form, then the real one
  await ir(`${BASE}/login`);
  await ev(`document.getElementById('token').value='errado'; document.querySelector('form').submit()`);
  await esperar(1800); await ate("document.readyState === 'complete'");
  console.log("após token errado:", await ev("location.pathname + location.search"), "| aviso:", await ev("(document.querySelector('.erro')||{}).textContent"));
  const token = fs.readFileSync(TOKEN_FILE, "utf8").trim();
  await ev(`document.getElementById('token').value=${JSON.stringify(token)}; document.querySelector('form').submit()`);
  await esperar(800);
  console.log("grade carregou:", await ate("document.querySelectorAll('.card').length > 0"), "| azulejos:", await ev("document.querySelectorAll('.tile').length"));
  await esperar(2500);

  // Meus apps: the launcher
  console.log("aba ativa:", await ev("document.querySelector('#tabs [aria-selected=true]').textContent"), "| com link:", await ev("document.querySelectorAll('.tile a.tile-open').length"), "| com engrenagem:", await ev("document.querySelectorAll('.tile .gear').length"));
  console.log("exemplo de link:", mascara(await ev("(document.querySelector('.tile a.tile-open')||{}).href")).slice(0, 60), "| 'null' solto:", await ev("/null|undefined/.test(document.getElementById('grid').textContent)"));
  await foto("01-meus-apps");

  if (MODO === "deprecated") {
    // needs a store whose repository marks one installed and one uninstalled service as deprecated
    console.log("selos 'descontinuado' em Meus apps:", await ev("[...document.querySelectorAll('.tile .badge')].filter((b) => b.textContent === 'descontinuado').length"));
    await foto("01-meus-apps-descontinuado");
    await tab("tab-store");
    console.log("cartões com o selo na Loja:", await ev("[...document.querySelectorAll('#grid .card')].filter((c) => /descontinuado/.test(c.textContent)).map((c) => c.querySelector('h3').textContent).join(', ')"));
    await foto("02-loja-descontinuado");
    console.log("abrir Gitea:", await abrir("Gitea")); await esperar(1200);
    console.log("painel aberto:", await ev("document.getElementById('panel').open"), "| nome:", await ev("document.getElementById('p-name').textContent"));
    console.log("painel de um não instalado → aviso:", await ev("document.getElementById('p-notice').textContent"), "| botões:", await ev("[...document.querySelectorAll('#p-actions button')].map((b) => b.textContent).join(' | ')"));
    await foto("03-painel-descontinuado");
    await ev("document.getElementById('p-close').click()"); await esperar(300);
    await abrir("HomeBox"); await esperar(1200);
    console.log("painel de um instalado → aviso:", await ev("document.getElementById('p-notice').textContent"), "| botões:", await ev("[...document.querySelectorAll('#p-actions button')].map((b) => b.textContent).join(' | ')"));
    await foto("04-painel-instalado-descontinuado");
    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
    await esperar(800); await ev("document.getElementById('p-close').click()"); await esperar(300);
    console.log("celular: scrollWidth", await ev("document.documentElement.scrollWidth"), "innerWidth", await ev("innerWidth"));
    await foto("05-celular-descontinuado");
    return fim();
  }

  if (MODO === "abas-loja") {
    await tab("tab-store");
    await abrir("Immich"); await esperar(1500);
    await botao("Personalizar"); await ate("document.querySelectorAll('#c-body .cust').length > 0", 15000); await esperar(400);
    console.log("abas:", await ev("[...document.querySelectorAll('#c-tabs button')].map((b) => b.textContent).join(' | ')"), "| visíveis:", await ev("!document.getElementById('c-tabs').hidden"));
    await foto("23-abas-loja");
    await ev("[...document.querySelectorAll('#c-tabs button')][1].click()"); await esperar(300);
    console.log("aba:", await ev("document.querySelector('#c-tabs [aria-selected=true]').textContent"), "| imagem:", await ev("document.querySelector('#c-body .cust-two .field.ro input').value"));
    return fim();
  }
  if (MODO === "abas") {
    // reads only: a stack opens Customize with a tab per container
    await abrir("Media Stack"); await esperar(1500);
    await botao("Personalizar"); await ate("document.querySelectorAll('#c-body .cust').length > 0", 15000); await esperar(400);
    console.log("abas:", await ev("[...document.querySelectorAll('#c-tabs button')].map((b) => b.textContent).join(' | ')"));
    await ev("[...document.querySelectorAll('#c-tabs button')][2].click()"); await esperar(300);
    console.log("aba ativa:", await ev("document.querySelector('#c-tabs [aria-selected=true]').textContent"), "| contêiner:", await ev("document.querySelector('#c-body .field.ro:nth-of-type(2) input, #c-body .cust > .field.ro input').value"));
    await ev("document.querySelector('#c-body details.adv').scrollIntoView()"); await ev("document.querySelector('#c-body details.adv > summary').click()"); await esperar(300);
    await foto("22-abas");
    return fim();
  }

  if (MODO === "portas") {
    // reads only: opens Customize and adds empty rows to look at the layout; never saves
    await abrir("Actual Budget"); await esperar(1500);
    await botao("Personalizar"); await ate("!!document.querySelector('#custom .cust, #c-body .cust')", 10000); await esperar(400);
    for (const t of ["Portas", "Portas", "Variáveis", "Volumes"]) await maisLinha(t);
    await poeLinha("Portas", 0, ["", "5335", "53"]);
    await ev("document.getElementById('c-body').scrollTo(0, 280)"); await esperar(300);
    await foto("20-portas");
    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
    await esperar(600); await ev("document.getElementById('c-body').scrollTo(0, 500)"); await esperar(300);
    await foto("21-portas-celular");
    return fim();
  }

  if (MODO === "install") {
    // reads only: opens an uninstalled app and asks for the plan; never confirms
    await tab("tab-store");
    console.log("abrir Mailpit:", await abrir("Mailpit")); await esperar(1500);
    await foto("10-loja-detalhe");
    console.log("Instalar:", await botao("Instalar")); await esperar(2500);
    await foto("11-instalar-plano");
    console.log("status:", await ev("document.getElementById('p-status').textContent"), "| form:", await ev("document.getElementById('p-form').textContent.slice(0, 120)"));
    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
    await esperar(800); await foto("12-celular-instalar");
    await ev("document.getElementById('p-close').click()"); await esperar(300);
    await foto("13-celular-loja");
    return fim();
  }

  // Customize, on the first installed app that offers it
  const app = MODO === "sandbox" ? "HomeBox" : "Actual Budget";
  await abrir(app); await ate("document.getElementById('p-info').textContent.includes('Disco') && !document.getElementById('p-info').textContent.includes('calculando')", 25000);
  console.log("botões:", await ev("[...document.querySelectorAll('#p-actions button')].map(b=>b.textContent).join(' | ')"));
  await ate("document.querySelectorAll('#p-project a').length > 2", 8000);
  console.log("links do projeto:", mascara(await ev("[...document.querySelectorAll('#p-project a')].map((a) => a.textContent.replace(' ↗', '') + '=' + a.href).join('  |  ')")));
  await foto("00-painel-links");
  console.log("Personalizar:", await botao("Personalizar")); await ate("!!document.querySelector('#custom .cust')", 10000); await esperar(400);
  console.log("grupos:", await ev("[...document.querySelectorAll('.cust-group h4')].map(h => h.firstChild.textContent).join(' | ')"));
  console.log("linhas:", await ev("[...document.querySelectorAll('.cust-group')].map(g => g.querySelector('h4').firstChild.textContent + '=' + g.querySelectorAll('.cust-row').length).join(' ')"), "| restart:", await ev("[...document.querySelectorAll('#custom .cust-group')].pop().querySelector('select').value"));
  console.log("limites avisados:", await ev("/indisponível aqui/.test(document.getElementById('custom').textContent)"), "| 'null' solto:", await ev("/null|undefined/.test(document.getElementById('custom').textContent)"));
  await ev("document.getElementById('custom').scrollIntoView()"); await esperar(300); await foto("02-personalizar");
  await clicaForm("Pré-visualizar"); await esperar(1500);
  console.log("pré-visualização sem mudança:", (await formTexto()).includes("Nada diferente da unit do repositório."));
  // a port and a variable, previewed: the file that would be written, and what Quadlet makes of it
  await maisLinha("Portas"); await poeLinha("Portas", await ev(`${grupo("Portas")}.querySelectorAll('.cust-row').length - 1`), ["", "8199", "3000"]);
  await maisLinha("Variáveis"); await poeLinha("Variáveis", await ev(`${grupo("Variáveis")}.querySelectorAll('.cust-row').length - 1`), ["NOVA", 'a b $x 100%']);
  await clicaForm("Pré-visualizar"); await esperar(2000);
  const t1 = await formTexto();
  console.log("prévia com porta e variável:", "PublishPort=8199:3000:", t1.includes("PublishPort=8199:3000"), "| escape:", t1.includes('NOVA="a b $$x 100%%"'), "| aviso da rede local:", t1.includes("rede local"), "| comando gerado:", /--publish 8199:3000/.test(t1));
  await ev("document.querySelector('.cust-out').scrollIntoView()"); await esperar(300); await foto("03-personalizar-previa");
  // a refusal: a folder outside the permitted roots
  await maisLinha("Volumes"); await poeLinha("Volumes", await ev(`${grupo("Volumes")}.querySelectorAll('.cust-row').length - 1`), ["/etc", "/e"]);
  await clicaForm("Pré-visualizar"); await esperar(1500);
  console.log("volume em /etc recusado:", (await formTexto()).includes("fora das pastas permitidas"));
  await foto("04-personalizar-recusa");

  if (MODO === "sandbox") {
    // remove the /etc row, then really apply and revert — in the sandbox only
    await ev(`(() => { const rows = ${grupo("Volumes")}.querySelectorAll('.cust-row'); rows[rows.length - 1].querySelector('.x').click(); })()`);
    await clicaForm("Salvar e aplicar"); await ate("/Reverter ao padrão/.test(document.getElementById('custom').textContent)", 20000); await esperar(800);
    console.log("aplicado — botão Reverter:", (await formTexto()).includes("Reverter ao padrão"), "| arquivo:", (await formTexto()).includes("50-store.conf"), "| saída:", (await ev("document.getElementById('p-out').textContent")).replace(/\n+/g, " / ").slice(0, 120));
    console.log("selo 'personalizado' no painel:", await ev("document.getElementById('p-info').textContent.includes('personalizado')"));
    await foto("05-aplicado");
    await clicaForm("Reverter ao padrão"); await ate("!/Reverter ao padrão/.test(document.getElementById('custom').textContent)", 20000); await esperar(800);
    console.log("revertido — sem o botão:", !(await formTexto()).includes("Reverter ao padrão"));
  }
  await ev("document.getElementById('p-close').click()"); await esperar(300);

  // Loja, reload, phone
  await tab("tab-store");
  console.log("Loja → hash:", await ev("location.hash"), "| cartões:", await ev("document.querySelectorAll('#grid .card').length"), "| categorias visíveis:", await ev("getComputedStyle(document.getElementById('groups')).display !== 'none'"));
  await foto("06-loja");
  await send("Page.reload"); await esperar(600); await ate("document.querySelectorAll('.card').length > 10");
  console.log("após recarregar com #store → aba:", await ev("document.querySelector('#tabs [aria-selected=true]').textContent"));
  await tab("tab-apps");
  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await esperar(800);
  console.log("celular Meus apps: scrollWidth", await ev("document.documentElement.scrollWidth"), "innerWidth", await ev("innerWidth"));
  await abrir(app); await esperar(2500); await botao("Personalizar"); await ate("!!document.querySelector('#custom .cust')", 10000); await esperar(600);
  await ev("document.getElementById('custom').scrollIntoView()"); await esperar(300);
  console.log("celular Personalizar: scrollWidth", await ev("document.documentElement.scrollWidth"), "| diálogo cabe:", await ev("(() => { const r = document.getElementById('panel').getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth; })()"));
  await foto("07-celular-personalizar");
  return fim();
})().catch((e) => { console.error("FALHOU:", e); process.exit(1); });

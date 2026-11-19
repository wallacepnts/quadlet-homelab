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

  const abrir = (nome) => ev(`(() => { const c = [...document.querySelectorAll('.card')].find((x) => x.querySelector('h3').textContent === ${JSON.stringify(nome)}); if (!c) return false; const m = c.querySelector('.more'); if (m) { m.click(); const g = [...document.querySelectorAll('#ctx .it')].find((x) => x.textContent === 'Gerenciar'); if (g) { g.click(); return true; } } (c.querySelector('.tile-open') || c).click(); return true; })()`);
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

  if (MODO === "progresso") {
    // sandbox only: installs HomeBox through the panel and looks at the progress
    await esperar(1500);
    await ev("location.hash = '#store'"); await esperar(800);
    await ev("(() => { const c = [...document.querySelectorAll('.card, #grid button, #grid .row, #grid > *')].find((x) => /HomeBox/i.test(x.textContent)); c.click(); })()"); await esperar(1500);
    await ev("[...document.querySelectorAll('#p-actions button')].find((b) => b.textContent.trim().startsWith('Instalar')).click()"); await esperar(1500);
    await ev("(() => { for (const i of document.querySelectorAll('#p-form input[data-secret]')) i.value = 'tskey-auth-test'; })()");
    await ev("[...document.querySelectorAll('#p-form button')].find((b) => /Instalar agora/.test(b.textContent)).click()"); await esperar(4500);
    if (process.env.QH_PROGRESS_TERMINAL) { await ev("[...document.querySelectorAll('#p-progress .seg-btn')].find((b) => b.textContent.trim() === 'Terminal').click()"); await esperar(500); }
    console.log("progresso:", await ev("document.getElementById('p-progress').hidden ? 'oculto' : document.getElementById('p-progress').textContent.replace(/\\s+/g, ' ').slice(0, 300)"));
    await ev("document.getElementById('p-progress').scrollIntoView()"); await esperar(300);
    await foto("98-progresso");
  }

  if (MODO === "fase15") {
    // reads only: health tab, what really runs, the list of images
    await ate("document.querySelectorAll('.tile').length > 0", 15000); await esperar(2000);
    await ev("(() => { const t = [...document.querySelectorAll('.tile')].find((x) => /Actual/.test(x.textContent)); t.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, clientX: 300, clientY: 300 })); })()"); await esperar(400);
    await ev("[...document.querySelectorAll('#ctx button')].find((b) => /Gerenciar/.test(b.textContent)).click()"); await esperar(1200);
    console.log("botões da unit:", await ev("[...document.querySelectorAll('#p-units button')].map((b) => b.textContent.trim()).join(' | ')"));
    await ev("[...document.querySelectorAll('#p-units button')].find((b) => b.textContent.trim() === 'Saúde').click()"); await esperar(1200);
    console.log("saúde:", await ev("document.getElementById('p-section').textContent.replace(/\\s+/g, ' ').slice(0, 260)"));
    await ev("document.getElementById('p-section').scrollIntoView()"); await esperar(300); await foto("95-saude");
    await ev("[...document.querySelectorAll('#p-units button')].find((b) => b.textContent.trim() === 'Detalhes').click()"); await esperar(1200);
    console.log("detalhes:", await ev("document.getElementById('p-section').textContent.replace(/\\s+/g, ' ').slice(0, 300)"));
    await ev("document.getElementById('p-section').scrollIntoView()"); await esperar(300); await foto("96-detalhes");
    await ev("document.getElementById('p-close').click()"); await esperar(300);
    await ev("document.getElementById('resources-btn').click()"); await esperar(3000);
    console.log("imagens:", await ev("document.querySelectorAll('table.imgs tr').length + ' linhas; ' + [...document.querySelectorAll('table.imgs tr')].slice(1, 4).map((r) => r.textContent.replace(/\\s+/g, ' ').slice(0, 110)).join(' || ')"));
    await ev("document.querySelector('table.imgs').scrollIntoView()"); await esperar(300); await foto("97-imagens");
  }

  if (MODO === "abas") {
    // reads only: the manager of an installed app, tab by tab
    await ate("document.querySelectorAll('.tile').length > 0", 15000); await esperar(2000);
    await ev("(() => { const t = [...document.querySelectorAll('.tile')].find((x) => /Actual/.test(x.textContent)); t.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, clientX: 300, clientY: 300 })); })()"); await esperar(400);
    await ev("[...document.querySelectorAll('#ctx button')].find((b) => /Gerenciar/.test(b.textContent)).click()"); await esperar(1200);
    console.log("topo:", await ev("[...document.querySelectorAll('#p-actions button, #p-actions a')].map((b) => b.textContent.trim()).join(' | ')"));
    console.log("abas:", await ev("[...document.querySelectorAll('#p-tabs button')].map((b) => b.textContent.trim()).join(' | ')"));
    await foto("98-aba-resumo");
    await ev("[...document.querySelectorAll('#p-tabs button')].find((b) => b.textContent.trim() === 'Configurar').click()"); await esperar(600); await foto("99-aba-configurar");
    await ev("[...document.querySelectorAll('#p-tabs button')].find((b) => b.textContent.trim() === 'Backups').click()"); await esperar(1500); await foto("99-aba-backups");
  }

  if (MODO === "legado") {
    // reads only: the banner of an old media-stack install, and what the new apps look like in the store
    await ate("document.querySelectorAll('.tile').length > 0", 15000); await esperar(2000);
    console.log("aviso:", await ev("(() => { const e = document.getElementById('legacy'); return e.hidden ? 'oculto' : e.textContent.trim().slice(0, 160); })()"));
    await foto("90-aviso-migracao");
    await tab("tab-store"); await esperar(900);
    console.log("loja tem:", await ev("['Jellyfin','Sonarr','Radarr','Deluge','Gluetun','Seerr'].filter((n) => document.body.textContent.includes(n)).join(', ')"));
    await foto("91-loja-novos-apps");
  }

  if (MODO === "cinza") {
    // reads only: a stopped or paused app's icon is grey and a little transparent
    await ate("document.querySelectorAll('.tile').length > 0", 15000); await esperar(2500);
    console.log("estados:", await ev("[...document.querySelectorAll('.tile')].map((t) => t.dataset.run + ':' + t.querySelector('h3').textContent).join(', ')"));
    console.log("estilo parado:", await ev("(() => { const t = document.querySelector('.tile:not([data-run=running]) .plate'); if (!t) return 'nenhum parado'; const c = getComputedStyle(t); return c.filter + ' / opacity ' + c.opacity; })()"));
    console.log("estilo rodando:", await ev("(() => { const t = document.querySelector('.tile[data-run=running] .plate'); const c = getComputedStyle(t); return c.filter + ' / opacity ' + c.opacity; })()"));
    await foto("80-parados-cinza");
  }

  if (MODO === "drift") {
    // reads only: does a changed .container count as an update?
    await ate("document.querySelectorAll('.tile').length > 0", 15000); await esperar(2500);
    console.log("chips:", await ev("[...document.querySelectorAll('#groups button')].map((b) => b.textContent.trim()).join(' | ')"));
    console.log("resumo:", await ev("document.getElementById('summary').textContent.trim()"));
    await ev("[...document.querySelectorAll('#groups button')].find((b) => /atualização/.test(b.textContent)).click()"); await esperar(600);
    console.log("com atualização:", await ev("[...document.querySelectorAll('.tile h3, .tile .name')].map((x) => x.textContent.trim()).join(', ') || document.getElementById('grid').textContent.slice(0, 200)"));
    await foto("70-filtro-atualizacao");
    await ev("[...document.querySelectorAll('#groups button')][0].click()"); await esperar(300);
    await ev("(() => { const t = [...document.querySelectorAll('.tile')].find((x) => /Actual/.test(x.textContent)); t.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, clientX: 300, clientY: 300 })); })()"); await esperar(400);
    console.log("menu:", await ev("document.getElementById('ctx').textContent.trim().slice(0, 300)"));
    await foto("71-menu-actual");
    await ev("[...document.querySelectorAll('#ctx button')].find((b) => /Gerenciar/.test(b.textContent)).click()"); await esperar(1200);
    console.log("acoes:", await ev("[...document.querySelectorAll('#p-actions button, #p-actions a')].map((b) => b.textContent.trim()).join(' | ')"));
    await ev("document.getElementById('p-drift').open = true"); await esperar(300);
    console.log("drift:", await ev("document.getElementById('p-drift-title').textContent + ' || ' + document.getElementById('p-drift-diff').textContent.trim()"));
    await foto("72-actual-gerenciar");
  }

  if (MODO === "unit") {
    // reads only: Customize → the .container as text (nothing is saved)
    await ate("document.querySelectorAll('.tile').length > 0", 15000); await esperar(1500);
    await ev("(() => { const t = [...document.querySelectorAll('.tile')].find((x) => /Actual/.test(x.textContent)); t.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, clientX: 300, clientY: 300 })); })()"); await esperar(400);
    await ev("[...document.querySelectorAll('#ctx button')].find((b) => /Gerenciar/.test(b.textContent)).click()"); await esperar(1200);
    await ev("[...document.querySelectorAll('#p-actions button')].find((b) => b.textContent.trim().startsWith('Personalizar')).click()"); await esperar(1500);
    await ev("document.querySelector('.raw-sec').open = true"); await esperar(400);
    await ev("document.querySelector('.raw-sec').scrollIntoView()"); await esperar(300);
    await foto("60-unit-codigo");
    console.log("texto no editor:", (await ev("document.querySelector('textarea.raw').value.slice(0, 80)")));
    await ev("(() => { const a = document.querySelector('textarea.raw'); a.value = a.value + 'PodmanArgs=--privileged\\n'; a.dispatchEvent(new Event('input')); })()");
    await ev("[...document.querySelectorAll('.raw-sec button')].find((b) => b.textContent.trim() === 'Verificar').click()"); await esperar(2500);
    await ev("document.querySelector('.raw-sec').scrollIntoView()");
    await foto("61-unit-verificar");
    console.log("avisos:", await ev("[...document.querySelectorAll('.raw-sec .cust-warn li, .raw-sec .cust-errors li')].map((x) => x.textContent).join(' | ')"));
  }

  if (MODO === "arquivos") {
    // writes, then undoes: a folder "qh-teste" is made inside the first app's volume and deleted again
    const clicar = (txt) => ev(`(() => { const b = [...document.querySelectorAll('#files button')].find((x) => x.textContent.trim().startsWith(${JSON.stringify(txt)})); if (!b) return false; b.click(); return true; })()`);
    await ev("document.getElementById('files-btn').click()"); await esperar(1200);
    await foto("50-arquivos-apps");
    console.log("entrou no app:", await ev("(() => { const b = document.querySelector('#f-body .fname.dir'); if (!b) return false; b.click(); return true; })()"), await esperar(800));
    console.log("entrou no volume:", await ev("(() => { const b = document.querySelector('#f-body .fname.dir'); if (!b) return false; b.click(); return true; })()"), await esperar(800));
    await foto("51-arquivos-volume");
    console.log("barra:", await ev("[...document.querySelectorAll('#f-bar button')].map((b) => b.textContent).join(' | ')"));
    await clicar("Nova pasta"); await esperar(200);
    await ev("(() => { const i = document.querySelector('#f-bar input'); i.value = 'qh-teste'; i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' })); })()"); await esperar(1500);
    console.log("criou:", await ev("[...document.querySelectorAll('#f-body .fname')].some((b) => b.textContent.includes('qh-teste'))"));
    await ev("(() => { const c = [...document.querySelectorAll('#f-body input[type=checkbox]')].find((x) => x.getAttribute('aria-label') === 'qh-teste'); c.checked = true; c.dispatchEvent(new Event('change')); })()"); await esperar(800);
    await foto("52-arquivos-selecionado");
    await clicar("Apagar"); await esperar(200); await clicar("Confirmar"); await esperar(1500);
    console.log("apagou:", !(await ev("[...document.querySelectorAll('#f-body .fname')].some((b) => b.textContent.includes('qh-teste'))")));
    await foto("53-arquivos-depois");
    await ev("(() => { const b = [...document.querySelectorAll('#f-bar button')].find((x) => x.textContent.trim() === 'Grade'); if (b) b.click(); })()"); await esperar(800);
    await foto("54-arquivos-grade");
    await ev("document.getElementById('f-side').querySelector('button').click()"); await esperar(1000);
    await foto("55-arquivos-raiz-grade");
    await ev("localStorage.setItem('qh-fview','list')");
  }

  if (MODO === "tema") {
    // reads only: the Clean theme — the home, the store, the right-click menu, Appearance
    await ate("document.querySelectorAll('.tile').length > 0", 15000); await esperar(2500);
    await foto("40-inicio");
    await ev("(() => { const t = document.querySelectorAll('.tile')[1].getBoundingClientRect(); document.querySelectorAll('.tile')[1].dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, clientX: t.left + 40, clientY: t.top + 40 })); })()"); await esperar(400);
    await foto("41-menu-de-contexto");
    await ev("document.body.click()"); await esperar(200);
    await tab("tab-store"); await esperar(800); await foto("42-loja");
    await tab("tab-apps"); await ev("document.getElementById('nav-toggle').click()"); await esperar(300); await foto("43-barra-recolhida");
    await ev("document.getElementById('nav-toggle').click()"); await esperar(200);
    await ev("document.getElementById('settings-btn').click()"); await esperar(1500); await foto("44-configuracoes");
    await ev("document.getElementById('s-close').click()"); await esperar(200);
    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true }); await esperar(800);
    await foto("45-celular-inicio");
    console.log("celular: scrollWidth", await ev("document.documentElement.scrollWidth"), "innerWidth", await ev("innerWidth"));
    return fim();
  }

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

  if (MODO === "f9") {
    // reads only: Quick Launch, Settings → Appearance (looked at, nothing picked) is NOT created
    await ev("document.dispatchEvent(new KeyboardEvent('keydown', { key: 'v', bubbles: true }))"); await esperar(500);
    console.log("quick launch aberto:", await ev("document.getElementById('ql').open"), "| itens:", await ev("document.querySelectorAll('#ql-list li').length"));
    await foto("30-quick-launch");
    await ev("document.getElementById('ql').close()"); await esperar(200);
    await ev("document.getElementById('settings-btn').click()"); await esperar(1500);
    await ev("document.getElementById('s-body').scrollTo(0, 0)"); await foto("31-aparencia");
    await ev("document.getElementById('s-close').click()"); await esperar(200);
    await ev("document.documentElement.setAttribute('data-theme','dark'); document.documentElement.setAttribute('data-accent','teal')"); await esperar(300);
    await foto("32-escuro-petroleo");
    await ev("document.documentElement.setAttribute('data-theme','light'); document.documentElement.setAttribute('data-accent','orange'); document.documentElement.setAttribute('data-density','compact'); document.documentElement.setAttribute('data-card','hairline')"); await esperar(300);
    await foto("33-compacto-borda");
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

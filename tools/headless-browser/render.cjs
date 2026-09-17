const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const HB = '/home/user/tools/headless-browser';
const WS_FILE = process.env.WS_FILE || HB + '/ws_endpoint.txt';

function arg(name, def) { const i = process.argv.indexOf('--'+name); return i>=0 ? process.argv[i+1] : def; }
function flag(name) { return process.argv.includes('--'+name); }

(async () => {
  const url = process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : arg('url');
  if (!url) { console.error('usage: render.cjs <url> [--wait networkidle|load|domcontentloaded] [--settle ms] [--sel css] [--html] [--shot] [--state f] [--save-state f] [--out name]'); process.exit(2); }
  const waitUntil = arg('wait','networkidle');
  const settle = parseInt(arg('settle','3500'),10);
  const sel = arg('sel');
  const stateIn = arg('state');
  const stateOut = arg('save-state');
  const outName = arg('out','page');

  const ws = fs.readFileSync(WS_FILE,'utf8').trim();
  const browser = await chromium.connect(ws);
  const ctxOpts = { ignoreHTTPSErrors: true, userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' };
  if (stateIn && fs.existsSync(stateIn)) ctxOpts.storageState = stateIn;
  const ctx = await browser.newContext(ctxOpts);
  const page = await ctx.newPage();
  let status = null;
  try {
    const resp = await page.goto(url, { waitUntil, timeout: 60000 });
    status = resp ? resp.status() : null;
  } catch (e) { console.error('[goto] ' + e.message.split('\n')[0]); }
  if (sel) { try { await page.waitForSelector(sel, { timeout: 20000 }); } catch(e){ console.error('[sel] not found: '+sel); } }
  if (settle) await page.waitForTimeout(settle);

  const text = await page.evaluate(() => document.body ? document.body.innerText : '');
  console.error('[hb] status=' + status + ' textlen=' + text.length + ' title=' + JSON.stringify(await page.title()));
  process.stdout.write(text);

  if (flag('html')) { const f = HB+'/out/'+outName+'.html'; fs.writeFileSync(f, await page.content()); console.error('[hb] html -> '+f); }
  if (flag('shot'))  { const f = HB+'/out/'+outName+'.png';  await page.screenshot({ path: f, fullPage: true }); console.error('[hb] shot -> '+f); }
  if (stateOut) { await ctx.storageState({ path: stateOut }); console.error('[hb] state -> '+stateOut); }

  await ctx.close();
  await browser.close(); // disconnects this client; server stays up
})();

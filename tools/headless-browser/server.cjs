const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
const WS_FILE = process.env.WS_FILE || '/home/user/tools/headless-browser/ws_endpoint.txt';
(async () => {
  const server = await chromium.launchServer({
    headless: true,
    args: ['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']
  });
  const ws = server.wsEndpoint();
  fs.writeFileSync(WS_FILE, ws);
  console.log('[hb-server] up. wsEndpoint written to ' + WS_FILE);
  console.log('[hb-server] ' + ws);
  const bye = async () => { try { await server.close(); } catch {} process.exit(0); };
  process.on('SIGTERM', bye); process.on('SIGINT', bye);
})();

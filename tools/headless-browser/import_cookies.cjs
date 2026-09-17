// usage: node import_cookies.cjs <cookies.json> <out-state.json> [originUrl]
// cookies.json = array of {name,value,domain,path,expires?,httpOnly?,secure?,sameSite?} (browser "EditThisCookie"/DevTools export)
const fs = require('fs');
const [,, inF, outF] = process.argv;
if (!inF || !outF) { console.error('usage: import_cookies.cjs <cookies.json> <out-state.json>'); process.exit(2); }
let raw = JSON.parse(fs.readFileSync(inF,'utf8'));
const cookies = (Array.isArray(raw) ? raw : raw.cookies).map(c => ({
  name: c.name, value: c.value,
  domain: c.domain.startsWith('.') ? c.domain : c.domain,
  path: c.path || '/',
  expires: c.expires && c.expires>0 ? Math.floor(c.expires) : -1,
  httpOnly: !!c.httpOnly, secure: c.secure!==false,
  sameSite: ({'no_restriction':'None','lax':'Lax','strict':'Strict'}[String(c.sameSite).toLowerCase()] || 'Lax')
}));
fs.writeFileSync(outF, JSON.stringify({ cookies, origins: [] }, null, 2));
console.error('[hb] wrote storageState with ' + cookies.length + ' cookies -> ' + outF);

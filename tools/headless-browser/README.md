# headless-browser — reusable JS/auth-gated page fetcher (Playwright over WebSocket)

Renders pages WebFetch can't: JS/SPA content and login-walled sites. A persistent
Chromium runs as a WS server; lightweight client calls connect to it. All contexts
use `ignoreHTTPSErrors: true` and inherit the session's HTTPS_PROXY, so the agent
proxy's re-terminated TLS is handled automatically.

## Use
    ./hb up                 # start persistent browser server (writes ws_endpoint.txt), survives across calls
    ./hb status             # show ws endpoint / up|down
    ./hb render <url> [opts]# connect over WS, render, print innerText to stdout
    ./hb down               # stop server

### render opts
    --wait networkidle|load|domcontentloaded   (default networkidle)
    --settle <ms>        extra wait after load (default 3500)
    --sel <css>          wait for a selector before scraping
    --html               also dump full HTML to out/<name>.html
    --shot               full-page screenshot to out/<name>.png
    --state <file>       load storageState (cookies) -> authenticated fetch
    --save-state <file>  persist storageState after load
    --out <name>         basename for html/shot artifacts

## Authenticated sites (e.g. Kaggle)
Kaggle gates competition data/rules behind login. To fetch as a logged-in user:
  1. Export cookies from a logged-in browser (DevTools/EditThisCookie) as JSON array.
  2. node import_cookies.cjs kaggle_cookies.json state/kaggle.json
  3. ./hb render "<kaggle-url>" --state state/kaggle.json --html --out kaggle

## Known limits
- Cloudflare "I'm human" challenges (e.g. cantina.xyz) can loop (ERR_TOO_MANY_RETRIES);
  needs a stealth/context tweak, not yet added.

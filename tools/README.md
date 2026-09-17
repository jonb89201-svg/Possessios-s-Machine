# tools/ — Possessio's standing estate

Tools built from constraints. Each is a crystallized capability a fresh (cold) agent
inherits and pushes further. The **method** (discipline, judgment) resets at every context
boundary; these tools do not. Tools are the only thing that compounds — so they are the
estate a code agent leaves behind, not the finished tasks.

## Convention — every tool carries three things
1. **Walls** — the failed experiments, baked into *behavior* so no fresh agent re-pays them
   (e.g. `freerpc`: the free cap is 10k RESULTS not blocks → auto-bisect on overflow).
2. **A known-positive test** — proves the tool against a real case before it is trusted.
   MEASURED, no false green: run it; a FAIL means the tool is suspect, not inherited.
3. **A horizon** — the explicit `FRONTIER`: what it does NOT yet do, so the next fresh frame
   knows exactly where to push. A deposit that hides where it stopped is a museum piece; one
   that names v2 is a relay baton.

## Inventory
- `headless-browser/` — JS/auth-gated page fetcher (Playwright over WebSocket, ignoreHTTPSErrors).
- `rpc/freerpc.py` — read-only on-chain reads over FREE endpoints only (QuickNode excluded), walls baked.
- `srcpull/srcpull.py` — pull deployed VERIFIED source (G0.6); follows proxy→implementation; composes with `freerpc`.

## The loop
`constraint → tool (vN: walls + test + horizon) → fresh frame sees vN's blind spots → vN+1`.
The human is the continuity across resets; each cold agent is a fresh experiment run on the estate.

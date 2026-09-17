"""radar — sweep bounty/competition platforms, surface FRESH + PERMISSIONLESS + LOW-SATURATION
smart-contract targets that fit our winning profile, minus what we've already audited.

Fossilized walls (paid for this session):
- Cantina API returns 5 items unless you pass ?limit=N ; live comps live in groups.currentCompetitions.
- Cantina does NOT flag LLM authorship (unlike some) -> good venue; keep it primary.
- web2 targets (AI apps, custody, wallets, chain clients) LOOK like bounties but have no
  unprivileged value-moving contract surface -> exclude by instruction keywords, not by pot.
- winning profile = fresh deploy + permissionless value core (AMM/lending/vault/perps), low saturation.
"""
import requests, datetime as dt
API="https://cantina.xyz/api/v0"
S=requests.Session(); S.headers["User-Agent"]="radar/0.1"

# already audited / walled this session (skip) — lowercased substrings
AUDITED={"polymarket","robinhood","reserve","tenbin","tenor","superform","mezo","ammalgam",
         "ondo","usdt0","morpho","midnight","pump","boros","coinbase","uniswap","euler",
         "agglayer","lifi","li.fi","debridge","paxos","phantom","usdai","kinetiq","symbiotic",
         "monad","liquity","kiln","pancakeswap","dydx","modular account","injective","chronicle","pendle",
         "okx","bitgo","cantina bounty","alchemy","rogo"}   # rogo/bitgo/okx/alchemy = web2/custody

DEFI=["amm","lending","lend ","borrow","vault","dex","swap","perp","liquidity","yield","collateral",
      "stablecoin","dlex","staking","restaking","order book","orderbook","market maker","clob",
      "leverage","tokeniz","cross-chain","4626","margin","options"]
PERM=["permissionless","non-custodial","noncustodial","trustless","anyone can","open, decentralized"]
BAD=["ios app","web application","web app","custody","wallet","consensus","execution client",
     "infrastructure","ui bug","browser extension","mobile app","ai platform","ai-powered"]

def fetch_bounties(limit=80):
    j=S.get(f"{API}/opportunities?limit={limit}",timeout=40).json()
    return j.get("items",[]), j.get("groups",{})

def score(item):
    txt=(item.get("instructions") or "").lower()
    d=sum(1 for k in DEFI if k in txt); p=sum(1 for k in PERM if k in txt); b=sum(1 for k in BAD if k in txt)
    # PRESENCE of a permissionless value-core, not verbosity
    defi_present = 6 if d>=2 else (3 if d==1 else 0)
    perm_present = 5 if p>=1 else 0
    s = defi_present + perm_present - min(b,3)*6
    # freshness graded: +6 at age 0 -> 0 at 180d -> floor -6 at 360d+
    try:
        created=dt.datetime.fromisoformat(item["createdAt"].replace("Z","+00:00"))
        age=(dt.datetime.now(dt.timezone.utc)-created).days
        s += max(-6.0, 6 - age/30.0)
    except Exception: age=None
    # saturation graded: +3 at 0 findings -> 0 at 300 -> floor -3 at 600+
    f=item.get("totalFindings") or 0
    s += max(-3.0, 3 - f/100.0)
    return round(s,1), {"defi":d,"perm":p,"bad":b,"age":age,"findings":f}

def run():
    items,groups=fetch_bounties()
    print(f"Cantina live: {groups.get('currentBounties','?')} bounties, "
          f"{groups.get('currentCompetitions','?')} competitions")
    cand=[]
    for it in items:
        nm=(it.get("name") or "").lower()
        if not nm.strip(): continue
        if any(a in nm for a in AUDITED): continue
        s,why=score(it); cand.append((s,it,why))
    cand.sort(key=lambda x:x[0], reverse=True)
    print(f"\n{'score':>5} {'pot':>9} {'find':>5} {'age':>4}  name")
    for s,it,why in cand[:10]:
        pot=it.get("totalRewardPot","?")
        print(f"{s:>5} {pot:>9} {why['findings']:>5} {str(why['age']):>4}  {it.get('name')}")
    return cand

if __name__=="__main__":
    run()

# FRONTIER (v2 — where a fresh frame should push this):
# - add Sherlock / Code4rena / Immunefi via headless-browser (Cantina-only today)
# - auto-srcpull each shortlisted target's deployed scope so the list arrives audit-ready
# - pull scope contract addresses from the bounty's assetGroups; flag KYC/submission-fee
# - learn the fit-weights from which past targets actually paid (feedback loop)

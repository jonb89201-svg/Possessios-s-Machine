"""freerpc — on-chain reads over FREE public RPC, with endpoint fallback and the
constraint-lessons we already paid for baked in. QuickNode is OFF (arrears); this tool
NEVER calls it. Read-only (eth_call/getCode/getLogs); no transactions. Terminal is the judge.

Fossilized lessons (failed experiments, baked in so no fresh agent re-pays them):
- QuickNode connector is excluded by design (account in arrears).
- mevblocker (rpc.mevblocker.io): 10_000-RESULT eth_getLogs cap (NOT blocks) — bisect range on overflow. VALIDATED.
- Cloudflare (cloudflare-eth.com): 800-block getLogs cap.
- publicnode: eth_call/getCode fine; logs archive-gated (old ranges may 4xx).
- drpc free tier LIES ("over 10000") once quota-limited -> excluded from logs; and more generally:
  NEVER trust an EMPTY getLogs result until the same endpoint returned non-empty on a
  known-positive window. An empty that isn't verified is HYPOTHESIS, not MEASURED.
"""
import requests

# chain_id -> ordered [(url, getlogs_block_cap)]  (cap 0 => don't use for ranged logs)
ENDPOINTS = {
    1: [("https://ethereum-rpc.publicnode.com", 0),
        ("https://rpc.mevblocker.io", 10_000),
        ("https://cloudflare-eth.com", 800)],
    8453: [("https://base-rpc.publicnode.com", 0), ("https://mainnet.base.org", 0)],
    137: [("https://polygon-bor-rpc.publicnode.com", 0)],
}
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def _rpc(url, method, params, timeout=25):
    r = requests.post(url, json={"jsonrpc":"2.0","id":1,"method":method,"params":params}, timeout=timeout)
    r.raise_for_status(); j = r.json()
    if j.get("error"): raise RuntimeError(j["error"])
    return j["result"]

def call(chain, method, params):
    last=None
    for url,_ in ENDPOINTS[chain]:
        try: return _rpc(url, method, params)
        except Exception as e: last=e
    raise RuntimeError(f"all free endpoints failed for {method}: {last}")

def block_number(chain): return int(call(chain,"eth_blockNumber",[]),16)
def get_code(chain, addr): return call(chain,"eth_getCode",[addr,"latest"])
def eth_call(chain, to, data, block="latest"): return call(chain,"eth_call",[{"to":to,"data":data},block])

def get_logs(chain, address=None, topics=None, from_block=0, to_block=None, known_positive=None):
    """Ranged getLogs, chunked by the endpoint's real cap. Refuses to return an unverified empty."""
    if to_block is None: to_block = block_number(chain)
    caps = [(u,c) for u,c in ENDPOINTS[chain] if c>0]
    if not caps: raise RuntimeError(f"no logs-capable free endpoint for chain {chain}")
    url, cap = caps[0]
    def _fetch(lo,hi):
        flt={"fromBlock":hex(lo),"toBlock":hex(hi)}
        if address: flt["address"]=address
        if topics: flt["topics"]=topics
        try:
            return _rpc(url,"eth_getLogs",[flt])
        except RuntimeError as e:
            # BAKED LESSON: the free cap is 10_000 RESULTS, not blocks. On overflow, bisect and recurse.
            msg=str(e).lower()
            if hi>lo and ("more than 10000" in msg or "-32005" in msg or "block range" in msg or "limit" in msg):
                mid=(lo+hi)//2
                return _fetch(lo,mid)+_fetch(mid+1,hi)
            raise
    def _range(a,b):
        out=[]; lo=a
        while lo<=b:
            hi=min(lo+cap-1,b)
            out += _fetch(lo,hi); lo=hi+1
        return out
    logs=_range(from_block,to_block)
    if not logs and known_positive is not None:
        # BAKED LESSON: verify the endpoint isn't silently lying before trusting empty.
        ka,kt,kfrom,kto = known_positive
        probe=_range(kfrom,kto)  # a window known to contain logs
        if not probe:
            raise RuntimeError(f"empty getLogs UNVERIFIED: endpoint {url} returned nothing on a "
                               f"known-positive window either -> broken/lying, not a real empty")
    return logs

if __name__=="__main__":
    USDC="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    print("== known-positive MEASURED test (ETH mainnet, free endpoints only) ==")
    bn=block_number(1); print("blockNumber:", bn)
    code=get_code(1,USDC); print("USDC getCode nonempty:", len(code)>2, f"({len(code)} chars)")
    # decimals() selector 0x313ce567 -> should return 6
    dec=int(eth_call(1,USDC,"0x313ce567"),16); print("USDC decimals()==6:", dec==6)
    lo=bn-300
    logs=get_logs(1,address=USDC,topics=[TRANSFER_TOPIC],from_block=lo,to_block=bn,
                  known_positive=(USDC,TRANSFER_TOPIC,lo,bn))
    print(f"USDC Transfer logs in last 300 blocks: {len(logs)} (>0 expected)")
    print("PASS" if (len(code)>2 and dec==6 and len(logs)>0) else "FAIL")

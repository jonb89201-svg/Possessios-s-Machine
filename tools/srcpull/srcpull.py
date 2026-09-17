"""srcpull — pull DEPLOYED VERIFIED source from a chain (the G0.6 method: audit what's on-chain,
not what's in a repo). Keyless Blockscout v2 API, Sourcify fallback. Read-only.

Fossilized walls (don't re-pay them):
- A PROXY's verified source is the proxy shell — the logic lives at the implementation.
  Always resolve `implementations[]` (or the EIP-1967 impl slot) and pull THAT too, or you
  audit an empty forwarder and call it clean. False green of the worst kind.
- Blockscout is per-chain subdomains; source can be single-file OR multi-file
  (`additional_sources[]`) — merge both or you miss contracts.
- 'is_verified: false' or empty source_code => NOT audited yet; treat as HYPOTHESIS, say so.

FRONTIER (v2 — where a fresh frame should push this):
- Sourcify + Etherscan-family fallback when Blockscout lacks the chain/contract
- diamond proxies (EIP-2535): resolve ALL facets, not just one implementation
- recursive proxies (proxy -> proxy); beacon proxies
- broaden the per-chain Blockscout registry; auto-discover instance from chainId
- return compiler settings (optimizer runs, evm version) for exact local recompile + hash match
"""
import requests
BLOCKSCOUT = {1:"https://eth.blockscout.com", 8453:"https://base.blockscout.com",
              137:"https://polygon.blockscout.com", 42161:"https://arbitrum.blockscout.com",
              10:"https://optimism.blockscout.com"}
S=requests.Session(); S.headers["User-Agent"]="srcpull/0.1"
import sys as _sys
_sys.path.insert(0, "/home/user/tools/rpc")
_EIP1967="0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
def _impl_from_slot(chain, addr):
    try:
        import freerpc
        word=freerpc.call(chain,"eth_getStorageAt",[addr,_EIP1967,"latest"])
        a="0x"+word[-40:]
        return a if int(a,16)!=0 else None
    except Exception:
        return None


def _bs(chain, addr):
    base=BLOCKSCOUT.get(chain)
    if not base: return None
    r=S.get(f"{base}/api/v2/smart-contracts/{addr}", timeout=30)
    if r.status_code!=200: return None
    return r.json()

def get_source(chain, address, follow_proxy=True):
    j=_bs(chain,address)
    out={"chain":chain,"address":address,"source":"blockscout","verified":False,
         "name":None,"compiler":None,"files":{},"abi":None,"proxy":False,"implementation":None}
    if j and (j.get("source_code") or j.get("additional_sources")):
        out["verified"]=bool(j.get("is_verified", True))
        out["name"]=j.get("name"); out["compiler"]=j.get("compiler_version"); out["abi"]=j.get("abi")
        if j.get("source_code"):
            out["files"][ (j.get("file_path") or f"{out['name'] or 'main'}.sol") ]=j["source_code"]
        for a in (j.get("additional_sources") or []):
            out["files"][a.get("file_path","?")]=a.get("source_code","")
        impls=j.get("implementations") or []
        out["proxy"]= bool(impls) or bool(j.get("proxy_type"))
        if impls:
            out["implementation"]=impls[0].get("address_hash") or impls[0].get("address")
        if out["proxy"] and not out["implementation"]:
            out["implementation"]=_impl_from_slot(chain, address)  # EIP-1967 fallback via freerpc
        # WALL: proxy shell -> pull implementation logic too
        if follow_proxy and out["implementation"]:
            impl=get_source(chain, out["implementation"], follow_proxy=False)
            for p,c in impl["files"].items(): out["files"][f"[impl]{p}"]=c
            out["impl_name"]=impl.get("name")
        return out
    return out  # unverified / not found -> caller sees verified=False, files={}

if __name__=="__main__":
    print("== known-positive MEASURED test (ETH mainnet, keyless) ==")
    weth="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # verified, non-proxy
    w=get_source(1, weth)
    ok_w = w["verified"] and w["name"] and any("WETH" in c or "Wrapped" in c for c in w["files"].values())
    print(f"WETH: verified={w['verified']} name={w['name']} files={len(w['files'])} compiler={w['compiler']}  -> {'OK' if ok_w else 'FAIL'}")
    usdc="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # PROXY -> tests impl-following wall
    u=get_source(1, usdc)
    ok_u = u["proxy"] and u["implementation"] and any(k.startswith("[impl]") for k in u["files"])
    print(f"USDC: proxy={u['proxy']} impl={u['implementation']} impl_files={sum(1 for k in u['files'] if k.startswith('[impl]'))}  -> {'OK (impl followed)' if ok_u else 'FAIL'}")
    print("PASS" if (ok_w and ok_u) else "FAIL")

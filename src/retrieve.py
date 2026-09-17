"""Formula -> candidate structures via PubChem PUG-REST (async listkey flow), with disk cache.
For CASMI-grade work a curated NP DB (COCONUT) is better-scoped; PubChem proves the pipeline."""
import os, json, time, urllib.parse, requests
CACHE = os.path.join(os.path.dirname(__file__), '..', 'data', 'pubchem_cache')
os.makedirs(CACHE, exist_ok=True)
BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'
S = requests.Session(); S.headers['User-Agent']='casmi26-proto/0.1'

def _get(url, timeout=30):
    for _ in range(8):
        r = S.get(url, timeout=timeout)
        if r.status_code in (200,202):
            try: return r.json()
            except Exception: return None
        if r.status_code==404: return None
        time.sleep(1.0)
    return None

def formula_to_cids(formula, max_records=200):
    cf = os.path.join(CACHE, f'cids_{formula}_{max_records}.json')
    if os.path.exists(cf): return json.load(open(cf))
    url = f'{BASE}/compound/formula/{urllib.parse.quote(formula)}/cids/JSON?MaxRecords={max_records}'
    j = _get(url)
    # handle async ListKey
    if j and 'Waiting' in j:
        lk = j['Waiting']['ListKey']
        for _ in range(20):
            time.sleep(1.5)
            j2 = _get(f'{BASE}/compound/listkey/{lk}/cids/JSON')
            if j2 and 'IdentifierList' in j2: j=j2; break
    cids = (j or {}).get('IdentifierList',{}).get('CID',[]) if j else []
    json.dump(cids, open(cf,'w')); return cids

def cids_to_structs(cids):
    if not cids: return []
    out=[]; 
    for i in range(0,len(cids),100):
        chunk=cids[i:i+100]
        cf=os.path.join(CACHE, f'props_{chunk[0]}_{len(chunk)}.json')
        if os.path.exists(cf): j=json.load(open(cf))
        else:
            ids=','.join(map(str,chunk))
            j=_get(f'{BASE}/compound/cid/{ids}/property/ConnectivitySMILES,InChIKey/JSON')
            json.dump(j, open(cf,'w'))
        for p in (j or {}).get('PropertyTable',{}).get('Properties',[]):
            smi=p.get('ConnectivitySMILES') or p.get('SMILES') or p.get('CanonicalSMILES') or p.get('IsomericSMILES')
            if smi: out.append({'cid':p.get('CID'),'smiles':smi,'inchikey':p.get('InChIKey','')})
        time.sleep(0.25)
    return out

def retrieve(formula, max_records=200):
    return cids_to_structs(formula_to_cids(formula, max_records))

if __name__=='__main__':
    import sys
    f = sys.argv[1] if len(sys.argv)>1 else 'C8H14ClN5'
    t0=time.time(); structs=retrieve(f, 200)
    print(f"formula {f}: {len(structs)} structures in {time.time()-t0:.1f}s")
    keys={s['inchikey'][:14] for s in structs}
    print('Atrazine (MXWJVTOOROXGIU) present:', 'MXWJVTOOROXGIU' in keys)
    for s in structs[:5]: print(' ', s['cid'], s['inchikey'][:14], s['smiles'][:40])

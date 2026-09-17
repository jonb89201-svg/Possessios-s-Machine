"""CASMI 2026 submission kernel — SELF-CONTAINED, internet-OFF safe (numpy/pandas/pyarrow only).
Analog-propagation prong: pre-load test spectra, stream train blocked by precursor ppm,
pure-numpy modified cosine, match on train inchikey14, emit /kaggle/working/submission.csv.
No matchms/rdkit (not guaranteed on the internet-off image)."""
import numpy as np, pandas as pd, pyarrow.parquet as pq, os, time
PPM=20.0; TOL=0.02; MINPK=3; TOPK=25

def modcos(mz1,i1,p1, mz2,i2,p2, tol=TOL):
    """Greedy modified cosine. Returns (score, n_matches). Intensities assumed normalized."""
    if len(mz1)<MINPK or len(mz2)<MINPK: return 0.0,0
    shift=p1-p2
    # candidate matches: direct, and precursor-shifted (skip if it coincides with direct)
    deltas=[0.0] if abs(shift)<=tol else [0.0, shift]
    pair={}  # (a,b) -> max intensity product (dedup peaks matched via both routes)
    for delta in deltas:
        b2=mz2+delta
        for a in range(len(mz1)):
            lo=np.searchsorted(b2, mz1[a]-tol); hi=np.searchsorted(b2, mz1[a]+tol)
            for b in range(lo,hi):
                pr=i1[a]*i2[b]; key=(a,b)
                if pr>pair.get(key,0.0): pair[key]=pr
    if not pair: return 0.0,0
    cand=sorted(((pr,a,b) for (a,b),pr in pair.items()), reverse=True)
    ua=set(); ub=set(); sprod=0.0; n=0
    for prod,a,b in cand:
        if a in ua or b in ub: continue
        ua.add(a); ub.add(b); sprod+=prod; n+=1
    denom=np.sqrt((i1*i1).sum()*(i2*i2).sum())
    return (sprod/denom if denom>0 else 0.0), n

def _prep(mz,it):
    mz=np.asarray(mz,float); it=np.asarray(it,float)
    m=it.max() if len(it) and it.max()>0 else 1.0; it=it/m
    o=np.argsort(mz); return mz[o], it[o]

def run(train_path, test_path, out_path):
    test=pd.read_parquet(test_path)
    T=[]
    for _,r in test.iterrows():
        mz,it=_prep(r["ms2_mzs"],r["ms2_normalized_intensities"])
        if len(mz)>=MINPK: T.append((r["molecule_id"], float(r["precursor_mz"]), mz, it))
    T.sort(key=lambda x:x[1]); tmass=np.array([x[1] for x in T])
    best={}
    pf=pq.ParquetFile(train_path); cols=["inchikey14","normalized_smiles","precursor_mz","ms2_mzs","ms2_normalized_intensities"]
    for b in pf.iter_batches(batch_size=100000, columns=cols):
        d=b.to_pydict(); pm=np.asarray(d["precursor_mz"],float)
        for k in range(len(pm)):
            m=pm[k]; w=m*PPM/1e6
            lo=np.searchsorted(tmass,m-w); hi=np.searchsorted(tmass,m+w)
            if hi<=lo: continue
            mz2,i2=_prep(d["ms2_mzs"][k],d["ms2_normalized_intensities"][k])
            if len(mz2)<MINPK: continue
            smi=d["normalized_smiles"][k]
            for idx in range(lo,hi):
                mol,_,mz1,i1=T[idx]
                sc,n=modcos(mz1,i1,T[idx][1], mz2,i2,m)
                if n>=MINPK and sc>0:
                    dd=best.setdefault(mol,{})
                    if sc>dd.get(smi,0.0): dd[smi]=sc
    rows=[]
    for mol in test["molecule_id"].unique():
        dd=best.get(mol,{}); ranked=sorted(dd,key=dd.get,reverse=True)[:TOPK]
        rows.append((mol, ";".join(ranked) if ranked else "C"))
    pd.DataFrame(rows,columns=["molecule_id","smiles"]).to_csv(out_path,index=False)
    return len(rows), sum(1 for m in test["molecule_id"].unique() if best.get(m))

if __name__=="__main__":
    IN="/kaggle/input/enveda-CASMI26-molecule-id-mass-spectra"
    if os.path.isdir(IN):
        run(f"{IN}/train.parquet", f"{IN}/test.parquet", "/kaggle/working/submission.csv")
    else:
        run("train.parquet","test.parquet","submission_kernel.csv")

# FRONTIER (v2 — where a fresh frame should push this):
# - speed: vectorize/numba the modified cosine (pure-python greedy is slow; fine for 9h but wasteful)
# - add CLASS-2 prong: molecular-formula -> LOCAL COCONUT/PubChem retrieval -> rerank (our real edge)
# - add CLASS-3 prong: de-novo spectrum->SMILES (GPU); merge all prongs; dedup by tautomer-canon InChIKey14
# - aggregate multi-spectrum molecules with intensity-weighted / merged spectra, not just best-pair

"""Streaming analog propagation over the full 2.5M train set, memory-bounded.
Blocks by precursor ppm; streams train, compares near rows to test spectra, keeps only
best-score-per-structure per test molecule. Emits submission.csv. WALLS: never hold train in
memory (OOM at 0.02Da abs); ppm block; discard each batch."""
import pyarrow.parquet as pq, numpy as np, pandas as pd, time, sys
from matchms import Spectrum
from matchms.filtering import normalize_intensities
from matchms.similarity import ModifiedCosineGreedy
import warnings; warnings.filterwarnings("ignore")
PPM=20.0; MINPK=3; TOL=0.02
mc=ModifiedCosineGreedy(tolerance=TOL)

def mkspec(mz,it,pmz):
    mz=np.asarray(mz,float); it=np.asarray(it,float)
    if len(mz)<MINPK: return None
    o=np.argsort(mz)
    return normalize_intensities(Spectrum(mz=mz[o],intensities=it[o],
        metadata={"precursor_mz":float(pmz)},metadata_harmonization=False))

t0=time.time()
test=pd.read_parquet("test.parquet")
tspec=[]  # (mol_id, pmz, spectrum)
for _,r in test.iterrows():
    s=mkspec(r["ms2_mzs"],r["ms2_normalized_intensities"],r["precursor_mz"])
    if s is not None: tspec.append((r["molecule_id"], float(r["precursor_mz"]), s))
tspec.sort(key=lambda x:x[1])
tmass=np.array([x[1] for x in tspec])
print(f"test: {len(tspec)} usable spectra / {test['molecule_id'].nunique()} molecules")

best={}  # mol_id -> {smiles: score}
pf=pq.ParquetFile("train.parquet")
cols=["normalized_smiles","precursor_mz","ms2_mzs","ms2_normalized_intensities"]
seen=0; cmp=0
for b in pf.iter_batches(batch_size=100000, columns=cols):
    d=b.to_pydict(); pm=np.asarray(d["precursor_mz"],float); n=len(pm); seen+=n
    for k in range(n):
        m=pm[k]; w=m*PPM/1e6
        lo=np.searchsorted(tmass,m-w); hi=np.searchsorted(tmass,m+w)
        if hi<=lo: continue
        ts=mkspec(d["ms2_mzs"][k], d["ms2_normalized_intensities"][k], m)
        if ts is None: continue
        smi=d["normalized_smiles"][k]
        for idx in range(lo,hi):
            mol_id,_,qs=tspec[idx]
            try: r=mc.pair(qs,ts)
            except Exception: continue
            cmp+=1
            if int(r["matches"])>=MINPK:
                sc=float(r["score"]); dd=best.setdefault(mol_id,{})
                if sc>dd.get(smi,0.0): dd[smi]=sc
    if seen % 500000 < 100000:
        print(f"  scanned {seen:,}/2,539,608 | matched molecules {len(best)} | pairs {cmp:,} | {time.time()-t0:.0f}s")

# build submission
rows=[]
for mol_id in test["molecule_id"].unique():
    dd=best.get(mol_id,{})
    ranked=sorted(dd,key=dd.get,reverse=True)[:25]
    rows.append((mol_id, ";".join(ranked) if ranked else "C"))
sub=pd.DataFrame(rows,columns=["molecule_id","smiles"])
sub.to_csv("submission_analog.csv",index=False)
cov=sum(1 for m in test["molecule_id"].unique() if best.get(m))
print(f"\nDONE {time.time()-t0:.0f}s | {cmp:,} pairs | analog found candidates for "
      f"{cov}/{test['molecule_id'].nunique()} test molecules | wrote submission_analog.csv")

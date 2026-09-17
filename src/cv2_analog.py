"""Proper two-pass train CV: pre-load 400 query spectra, THEN stream full train as library
(query rows excluded). Mirrors streaming_analog's architecture -> trustworthy MRR@25."""
import pyarrow.parquet as pq, numpy as np, random, time
from matchms import Spectrum
from matchms.filtering import normalize_intensities
from matchms.similarity import ModifiedCosineGreedy
import warnings; warnings.filterwarnings("ignore")
PPM=20.0; MINPK=3; NQ=400
mc=ModifiedCosineGreedy(tolerance=0.02); rng=random.Random(0)
def mkspec(mz,it,pmz):
    mz=np.asarray(mz,float); it=np.asarray(it,float)
    if len(mz)<MINPK: return None
    o=np.argsort(mz); return normalize_intensities(Spectrum(mz=mz[o],intensities=it[o],
        metadata={"precursor_mz":float(pmz)},metadata_harmonization=False))
t0=time.time(); pf=pq.ParquetFile("train.parquet"); N=pf.metadata.num_rows
npk=[]
for b in pf.iter_batches(batch_size=300000, columns=["num_peaks"]): npk+=b.column(0).to_pylist()
elig=np.where(np.array(npk)>=5)[0]; qidx=set(rng.sample(list(elig),NQ))
print(f"{N:,} rows; {len(qidx)} queries; {time.time()-t0:.0f}s")
cols=["inchikey14","precursor_mz","ms2_mzs","ms2_normalized_intensities"]
# PASS A: extract query spectra
Q=[]  # (pmz, spec, true_ik14)
gi=0
for b in pf.iter_batches(batch_size=100000, columns=cols):
    d=b.to_pydict(); n=len(d["precursor_mz"]); pm=np.asarray(d["precursor_mz"],float)
    for k in range(n):
        if gi+k in qidx:
            s=mkspec(d["ms2_mzs"][k],d["ms2_normalized_intensities"][k],pm[k])
            if s is not None: Q.append((pm[k],s,d["inchikey14"][k]))
    gi+=n
qmass=np.array([q[0] for q in Q]); srt=np.argsort(qmass); qmass=qmass[srt]; Q=[Q[i] for i in srt]
print(f"extracted {len(Q)} query spectra; {time.time()-t0:.0f}s")
# PASS B: full library stream
best=[dict() for _ in Q]; gi=0; cmp=0
for b in pf.iter_batches(batch_size=100000, columns=cols):
    d=b.to_pydict(); n=len(d["precursor_mz"]); pm=np.asarray(d["precursor_mz"],float)
    for k in range(n):
        if gi+k in qidx: continue
        m=pm[k]; w=m*PPM/1e6
        lo=np.searchsorted(qmass,m-w); hi=np.searchsorted(qmass,m+w)
        if hi<=lo: continue
        ts=mkspec(d["ms2_mzs"][k],d["ms2_normalized_intensities"][k],m)
        if ts is None: continue
        ik=d["inchikey14"][k]
        for j in range(lo,hi):
            try: r=mc.pair(Q[j][1],ts)
            except Exception: continue
            cmp+=1
            if int(r["matches"])>=MINPK:
                sc=float(r["score"])
                if sc>best[j].get(ik,0.0): best[j][ik]=sc
    gi+=n
    if gi % 800000 < 100000: print(f"  lib {gi:,}/{N:,} | pairs {cmp:,} | {time.time()-t0:.0f}s")
rr=[]; found=0
for j,(_,_,true) in enumerate(Q):
    ranked=sorted(best[j],key=best[j].get,reverse=True)[:25]
    if true in ranked: rr.append(1.0/(ranked.index(true)+1)); found+=1
    else: rr.append(0.0)
rr=np.array(rr)
print(f"\nCV {len(rr)} queries | true structure in top25: {found} ({found/len(rr)*100:.0f}%) | pairs {cmp:,}")
print(f"MRR@25 (train CV, analog prong alone): {rr.mean():.3f}   [public SOTA mixed test ~0.341]")
print(f"{time.time()-t0:.0f}s")

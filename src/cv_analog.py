"""Train-internal CV for the analog prong. Pick N query spectra; stream the rest as library;
MRR@25 via train inchikey14. Single pass -> LOWER BOUND (query only sees siblings streamed after it)."""
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
t0=time.time()
pf=pq.ParquetFile("train.parquet"); N=pf.metadata.num_rows
# scalar pass: pick query indices with enough peaks
npk=[]; 
for b in pf.iter_batches(batch_size=200000, columns=["num_peaks"]): npk+=b.column(0).to_pylist()
npk=np.array(npk); elig=np.where(npk>=5)[0]
qidx=set(rng.sample(list(elig), NQ)); print(f"train {N:,} rows; picked {len(qidx)} queries; {time.time()-t0:.0f}s")
# main pass
queries={}  # idx -> (pmz, spec, true_ik14)
qmass=np.array([]); qids=[]
best={}     # idx -> {ik14: score}
cols=["inchikey14","precursor_mz","ms2_mzs","ms2_normalized_intensities"]
gi=0; cmp=0
for b in pf.iter_batches(batch_size=100000, columns=cols):
    d=b.to_pydict(); n=len(d["precursor_mz"]); pm=np.asarray(d["precursor_mz"],float)
    for k in range(n):
        idx=gi+k
        if idx in qidx:
            s=mkspec(d["ms2_mzs"][k],d["ms2_normalized_intensities"][k],pm[k])
            if s is not None:
                queries[idx]=(pm[k],s,d["inchikey14"][k]); qids.append(idx)
                qmass=np.append(qmass, pm[k])
        elif len(qmass):
            m=pm[k]; w=m*PPM/1e6
            lo=np.searchsorted(qmass,m-w); hi=np.searchsorted(qmass,m+w)
            if hi<=lo: continue
            order=np.argsort(qmass)  # keep qmass sorted view
            ts=mkspec(d["ms2_mzs"][k],d["ms2_normalized_intensities"][k],m)
            if ts is None: continue
            ik=d["inchikey14"][k]
            # compare to queries whose mass in window
            for j in np.where(np.abs(qmass-m)<=w)[0]:
                qi=qids[j]; _,qs,_=queries[qi]
                try: r=mc.pair(qs,ts)
                except Exception: continue
                cmp+=1
                if int(r["matches"])>=MINPK:
                    sc=float(r["score"]); dd=best.setdefault(qi,{})
                    if sc>dd.get(ik,0.0): dd[ik]=sc
    gi+=n
    if gi % 700000 < 100000: print(f"  {gi:,}/{N:,} | queries {len(queries)} | pairs {cmp:,} | {time.time()-t0:.0f}s")
# MRR@25
rr=[]; found=0
for qi in queries:
    true=queries[qi][2]; dd=best.get(qi,{})
    ranked=sorted(dd,key=dd.get,reverse=True)[:25]
    if true in ranked: rr.append(1.0/(ranked.index(true)+1)); found+=1
    else: rr.append(0.0)
rr=np.array(rr)
print(f"\nCV over {len(rr)} queries | analog found true structure in top25: {found} ({found/len(rr)*100:.0f}%)")
print(f"MRR@25 (LOWER BOUND, single-pass, train inchikey14): {rr.mean():.3f}")
print(f"(public SOTA on the real mixed test ~0.341)  |  {time.time()-t0:.0f}s")

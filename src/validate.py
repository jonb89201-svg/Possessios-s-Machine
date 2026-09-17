import os, glob, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from massbank import parse
from pipeline import identify, ik14

# pick a spread of CHNOPS natural products (moderate size for speed)
WANT = ['Baicalein','Tetrahydroalstonine','Feruloyltyramine','Feruloylputrescine',
        'Demethoxycurcumin','Aloxistatin']
recs=[]
for f in glob.glob(os.path.join(os.path.dirname(__file__),'..','data','mb','*.txt')):
    s=parse(open(f).read())
    if any(w.lower() in s.name.lower() for w in WANT) and s.precursor_mz and len(s.peaks)>=6:
        recs.append(s)
seen=set(); uniq=[]
for s in recs:
    if s.name in seen: continue
    seen.add(s.name); uniq.append(s)

print(f"{'compound':24}{'formula':12}{'adduct':8}{'#cand':>6}{'rank':>6}{'top1?':>7}  time")
ranks=[]
for s in uniq[:6]:
    t0=time.time()
    truth=ik14(s.smiles)
    top=identify(s.precursor_mz, s.adduct, s.ion_mode, s.peaks,
                 ppm_tol=5.0, n_formulas=4, per_formula=120, topk=25)
    keys=[c['inchikey'][:14] for c in top]
    rank = keys.index(truth)+1 if truth in keys else -1
    ranks.append(rank)
    print(f"{s.name[:24]:24}{s.formula:12}{s.adduct:8}{len(top):6d}{rank:6d}{str(rank==1):>7}  {time.time()-t0:4.1f}s")
import numpy as np
r=np.array(ranks)
print(f"\nn={len(r)}  top1={np.mean(r==1):.2f}  top5={np.mean((r>=1)&(r<=5)):.2f}  top25(recall)={np.mean(r>=1):.2f}")

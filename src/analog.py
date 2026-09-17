"""Analog propagation (class-1 lever): rank library spectra by modified-cosine to the query,
propose their structures. Validated with the exact competition metric (MRR@25 on InChIKey14)."""
import os, glob, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from massbank import parse
from chem import canon_ik14
from matchms import Spectrum
from matchms.filtering import normalize_intensities, select_by_relative_intensity
from matchms.similarity import ModifiedCosineGreedy
import warnings; warnings.filterwarnings('ignore')

def to_ms(sp):
    if not sp.peaks or not sp.precursor_mz: return None
    mz=np.array([p[0] for p in sp.peaks],float); it=np.array([p[1] for p in sp.peaks],float)
    order=np.argsort(mz); mz,it=mz[order],it[order]
    m=Spectrum(mz=mz, intensities=it, metadata={'precursor_mz':float(sp.precursor_mz)},
               metadata_harmonization=False)
    return normalize_intensities(m)

def load_pool(paths):
    pool=[]
    for f in paths:
        sp=parse(open(f).read())
        ms=to_ms(sp)
        if ms is None or not sp.smiles: continue
        ik=canon_ik14(sp.smiles)
        if not ik: continue
        pool.append({'name':sp.name,'ik14':ik,'ms':ms,'adduct':sp.adduct,'file':os.path.basename(f)})
    return pool

def propagate(pool, tol=0.02, min_match=3, min_score=0.05, topk=25):
    """Leave-one-out: for each query, rank OTHER spectra by modified cosine, dedup structures, MRR@25."""
    mc=ModifiedCosineGreedy(tolerance=tol)
    rr=[]; details=[]
    for i,q in enumerate(pool):
        scored=[]
        for j,l in enumerate(pool):
            if i==j: continue
            try: r=mc.pair(q['ms'], l['ms'])
            except Exception: continue
            s=float(r['score']); n=int(r['matches'])
            if n>=min_match and s>=min_score: scored.append((s,l['ik14']))
        scored.sort(reverse=True)
        seen=set(); ranked=[]
        for s,ik in scored:
            if ik in seen: continue
            seen.add(ik); ranked.append(ik)
            if len(ranked)>=topk: break
        rank = ranked.index(q['ik14'])+1 if q['ik14'] in ranked else -1
        rr.append(1.0/rank if rank>0 else 0.0)
        details.append((q['name'][:24], rank, len(ranked)))
    return np.array(rr), details

if __name__=='__main__':
    paths=glob.glob('data/mb/*.txt')+glob.glob('data/MSBNK*.txt')
    pool=load_pool(paths)
    # how many compounds have >=1 same-structure neighbor (i.e., class-1 is even possible)?
    from collections import Counter
    c=Counter(p['ik14'] for p in pool)
    with_nbr=sum(1 for p in pool if c[p['ik14']]>1)
    print(f"pool: {len(pool)} spectra, {len(c)} unique structures, {with_nbr} spectra have a same-structure neighbor")
    rr,details=propagate(pool)
    print(f"\nAnalog-propagation MRR@25 (whole pool):      {rr.mean():.3f}")
    # subset where a same-structure neighbor exists (the reachable class-1 cases)
    idx=[k for k,p in enumerate(pool) if c[p['ik14']]>1]
    if idx:
        print(f"MRR@25 on class-1-reachable subset (n={len(idx)}): {rr[idx].mean():.3f}")
    hits=[d for d in details if d[1]>0]
    print(f"exact hits in top-25: {len(hits)}/{len(pool)}")
    for name,rank,nc in sorted(hits,key=lambda x:x[1])[:8]:
        print(f"   rank {rank:>2}  {name}")

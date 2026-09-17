"""End-to-end: MS/MS spectrum -> ranked top-25 candidate 2D structures (SMILES).
formula prediction (recall) -> PubChem retrieval -> fragmentation rerank (precision)."""
import sys, time
sys.path.insert(0, __import__('os').path.dirname(__file__))
from formula import predict_formulas, CHNOPS
from retrieve import retrieve
from fragment import score
from rdkit import Chem
from rdkit import RDLogger; RDLogger.DisableLog('rdApp.*')

def ik14(smiles):
    m=Chem.MolFromSmiles(smiles)
    return Chem.MolToInchiKey(m)[:14] if m else None

def identify(precursor_mz, adduct, ion_mode, peaks, elements=CHNOPS,
             ppm_tol=5.0, n_formulas=6, per_formula=150, topk=25, verbose=False):
    t0=time.time()
    formulas = predict_formulas(precursor_mz, adduct, ppm_tol=ppm_tol, elements=elements)[:n_formulas]
    if verbose: print(f"[formulas] {[f.formula for f in formulas]}")
    seen=set(); cands=[]
    for fc in formulas:
        for st in retrieve(fc.formula, per_formula):
            k=(st.get('inchikey') or '')[:14]
            if not k or k in seen: continue
            seen.add(k); st['formula']=fc.formula; cands.append(st)
    if verbose: print(f"[retrieve] {len(cands)} unique candidates in {time.time()-t0:.1f}s")
    scored=[]
    for st in cands:
        frac,n = score(st['smiles'], peaks, ion_mode)
        scored.append({**st,'score':frac,'npk':n})
    scored.sort(key=lambda x:x['score'], reverse=True)
    if verbose: print(f"[rerank] done in {time.time()-t0:.1f}s")
    return scored[:topk]

if __name__=='__main__':
    from massbank import parse
    import os
    rec=os.path.join(os.path.dirname(__file__),'..','data','MSBNK-Eawag-EA028811.txt')
    s=parse(open(rec).read())
    truth=ik14(s.smiles)
    print(f"TARGET {s.name} {s.formula} prec={s.precursor_mz} {s.adduct} | truth IK14={truth}")
    # Atrazine has Cl -> enable halogens (real pipeline: gate via isotope pattern)
    els=('C','H','N','O','P','S','Cl')
    top=identify(s.precursor_mz, s.adduct, s.ion_mode, s.peaks, elements=els, verbose=True)
    ranks=[i for i,c in enumerate(top,1) if c['inchikey'][:14]==truth]
    print(f"\nTRUE structure rank in top-25: {ranks[0] if ranks else 'NOT FOUND'}  (of {len(top)})")
    print(f"{'rank':>4} {'score':>6} {'npk':>3} {'IK14':16} smiles")
    for i,c in enumerate(top[:10],1):
        mark='  <== TRUE' if c['inchikey'][:14]==truth else ''
        print(f"{i:>4} {c['score']:6.3f} {c['npk']:>3} {c['inchikey'][:14]:16} {c['smiles'][:38]}{mark}")

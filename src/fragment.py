"""MetFrag-style fragmentation reranker with ring cleavage.
Kekulize -> break single bonds (chain AND ring) up to 2 -> match fragment ions to peaks.
Pure RDKit + CPU."""
from itertools import combinations
from rdkit import Chem
from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')
PT = Chem.GetPeriodicTable()
H = 1.0078250319; E = 0.00054858

def _atom_mass(a):
    return PT.GetMostCommonIsotopeMass(a.GetAtomicNum()) + a.GetTotalNumHs()*H

def fragment_masses(smiles, max_break=2):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None: return None
    try:
        Chem.Kekulize(mol, clearAromaticFlags=True)   # aromatic -> explicit single/double
    except Exception:
        pass
    atom_mass = {a.GetIdx(): _atom_mass(a) for a in mol.GetAtoms()}
    intact = sum(atom_mass.values())
    masses = {intact}
    # breakable = single bonds, including ring bonds (ring opens when 2 in same ring are cut)
    breakable = [b.GetIdx() for b in mol.GetBonds() if b.GetBondType()==Chem.BondType.SINGLE]
    for k in (1,2):
        if k>max_break: break
        for combo in combinations(breakable, k):
            try:
                fm = Chem.FragmentOnBonds(mol, list(combo), addDummies=False)
            except Exception:
                continue
            for fr in Chem.GetMolFrags(fm, asMols=False):
                if len(fr)==mol.GetNumAtoms(): continue
                masses.add(sum(atom_mass[i] for i in fr))
    return masses

def score(smiles, peaks, ion_mode='POSITIVE', tol_da=0.005, h_shifts=(-1,0,1),
          intensity_pow=0.5):
    """Explained-intensity score. tol tightened, H-shifts realistic, intensity sqrt-weighted
    so a few high-intensity matches beat many tiny coincidental ones."""
    fm = fragment_masses(smiles)
    if not fm: return 0.0, 0
    sign = +1 if ion_mode.upper().startswith('P') else -1
    ms = sorted(fm)
    matched=0.0; n=0
    for mz, inten in peaks:
        w = inten**intensity_pow
        hit=False
        for s in h_shifts:
            target = mz + sign*E - s*H     # neutral fragment mass implied by this ion & shift
            # binary-ish search
            for f in ms:
                d=f-target
                if d < -tol_da: continue
                if d > tol_da: break
                hit=True; break
            if hit: break
        if hit: matched += w; n+=1
    total = sum((i**intensity_pow) for _,i in peaks) or 1.0
    return matched/total, n

if __name__=='__main__':
    import os
    from massbank import parse
    rec=os.path.join(os.path.dirname(__file__),'..','data','MSBNK-Eawag-EA028811.txt')
    s=parse(open(rec).read())
    cands={'TRUE Atrazine':s.smiles,'decoy simazine':'CCNc1nc(Cl)nc(NCC)n1',
           'decoy caffeine':'Cn1cnc2c1c(=O)n(C)c(=O)n2C','decoy propranolol':'CC(C)NCC(COc1cccc2ccccc12)O'}
    res=sorted(((score(v,s.peaks,s.ion_mode),k) for k,v in cands.items()),reverse=True)
    print(f"target {s.name} {s.formula}, {len(s.peaks)} peaks")
    for (frac,n),name in res: print(f"  {frac:6.3f} {n:>3}pk  {name}")

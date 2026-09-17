"""Molecular formula prediction from precursor m/z + adduct.
Monoisotopic decomposition + chemistry priors. Recall-optimized (true formula in set);
downstream fragmentation does precision. No network, no GPU."""
from dataclasses import dataclass

MASS = {'C':12.0,'H':1.0078250319,'N':14.0030740052,'O':15.9949146221,
        'P':30.97376151,'S':31.97207069,'F':18.99840322,'Cl':34.96885271,'Br':78.9183376}
ELECTRON=0.00054858; PROTON=1.0072764666
ADDUCTS={'[M+H]+':(PROTON,+1),'[M+NH4]+':(18.033823-ELECTRON,+1),
         '[M-H2O+H]+':(PROTON-18.0105646,+1),'[M-2H2O+H]+':(PROTON-2*18.0105646,+1),
         '[M+Na]+':(22.9897692809-ELECTRON,+1),'[M+K]+':(38.9637064864-ELECTRON,+1),
         '[M-H]-':(-PROTON,-1),'[M-H2O-H]-':(-PROTON-18.0105646,-1),
         '[M+CH2O2-H]-':(46.00548-PROTON-0.0,-1),'[M+Cl]-':(34.96885271+ELECTRON,-1),
         '[M+HCOO]-':(44.99820285+ELECTRON,-1)}
VALENCE={'C':4,'H':1,'N':3,'O':2,'P':3,'S':2,'F':1,'Cl':1,'Br':1}
CHNOPS=('C','H','N','O','P','S')

def neutral_mass(mz,adduct): return mz-ADDUCTS[adduct][0]
def rdbe(c): return 1.0+sum(n*(VALENCE[e]-2)/2.0 for e,n in c.items())

def passes(c):
    C=c.get('C',0); H=c.get('H',0)
    if C==0: return False
    r=rdbe(c)
    if r<0 or (r*2)%1!=0: return False
    if H/C>3.1 or H/C<0.1: return False
    for e,lim in (('N',1.3),('O',1.3),('P',0.4),('S',0.8),('F',1.5),('Cl',0.8),('Br',0.8)):
        if c.get(e,0) and c[e]/C>lim: return False
    return True

def plausibility(c,ppm):
    # lower = better. |ppm| dominant; gentle penalties for heteroatom richness & extreme RDBE.
    C=c.get('C',1); r=rdbe(c)
    het=c.get('N',0)+c.get('P',0)+c.get('S',0)+c.get('F',0)+c.get('Cl',0)+c.get('Br',0)
    pen=0.15*max(0,het/C-0.6)*10 + 0.05*abs(r-(C/2.0))  # soft priors
    return abs(ppm)+pen

@dataclass
class Cand:
    formula:str; counts:dict; mass:float; ppm:float; rdbe:float; score:float

def fstr(c):
    order=['C','H','N','O','P','S','F','Cl','Br']
    return ''.join((e if c[e]==1 else f"{e}{c[e]}") for e in order if c.get(e,0)>0)

def predict_formulas(mz,adduct='[M+H]+',ppm_tol=5.0,elements=CHNOPS,max_results=100):
    M=neutral_mass(mz,adduct); tol=M*ppm_tol/1e6
    heavy=[e for e in elements if e!='H']
    caps={'C':90,'N':25,'O':35,'P':6,'S':8,'F':15,'Cl':10,'Br':6}
    maxc={e:min(int((M+tol)//MASS[e]),caps.get(e,30)) for e in heavy}
    out=[]
    def rec(i,ms,counts):
        if ms-tol>M: return
        if i==len(heavy):
            h=round((M-ms)/MASS['H'])
            if h<0: return
            m=ms+h*MASS['H']; err=m-M
            if abs(err)<=tol:
                c={k:v for k,v in counts.items() if v>0}; c['H']=h
                if passes(c):
                    ppm=err/M*1e6
                    out.append(Cand(fstr(c),c,m,ppm,rdbe(c),plausibility(c,ppm)))
            return
        el=heavy[i]; mel=MASS[el]; n=0
        while ms+n*mel-tol<=M and n<=maxc[el]:
            c2=dict(counts)
            if n>0: c2[el]=n
            rec(i+1,ms+n*mel,c2); n+=1
    rec(0,0.0,{})
    out.sort(key=lambda c:c.score)
    return out[:max_results]

if __name__=='__main__':
    tests=[('caffeine',195.087652,'[M+H]+','C8H10N4O2'),
           ('glucose',181.070665,'[M+H]+','C6H12O6'),
           ('tryptophan',205.097154,'[M+H]+','C11H12N2O2'),
           ('sucrose',365.105850,'[M+H]+','C12H22O11'),
           ('ibuprofen',205.122900,'[M-H]-','C13H18O2'),
           ('reserpine',609.280657,'[M+H]+','C33H40N2O9')]
    for ppm in (5.0,3.0):
        print(f"\n=== ppm_tol={ppm}, elements=CHNOPS ===")
        print(f"{'compound':12}{'true':14}{'#cand':>6}{'rank':>6}{'top1':>14}")
        hit=0
        for name,mz,add,tf in tests:
            cs=predict_formulas(mz,add,ppm_tol=ppm); fs=[c.formula for c in cs]
            rank=fs.index(tf)+1 if tf in fs else -1
            hit+= rank!=-1
            print(f"{name:12}{tf:14}{len(cs):6d}{rank:6d}{(fs[0] if fs else '-'):>14}")
        print(f"recall@set: {hit}/{len(tests)}")

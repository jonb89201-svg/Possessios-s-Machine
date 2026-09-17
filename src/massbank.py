"""Minimal MassBank record parser -> Spectrum."""
import re
from dataclasses import dataclass, field

@dataclass
class Spectrum:
    accession:str=''; name:str=''; formula:str=''; smiles:str=''; inchikey:str=''
    precursor_mz:float=0.0; adduct:str=''; ion_mode:str=''
    peaks:list=field(default_factory=list)  # [(mz, rel_int)]

def parse(text):
    s=Spectrum(); text=text.replace('\r','')
    for line in text.splitlines():
        if line.startswith('ACCESSION:'): s.accession=line.split(':',1)[1].strip()
        elif line.startswith('CH$NAME:') and not s.name: s.name=line.split(':',1)[1].strip()
        elif line.startswith('CH$FORMULA:'): s.formula=line.split(':',1)[1].strip()
        elif line.startswith('CH$SMILES:'): s.smiles=line.split(':',1)[1].strip()
        elif line.startswith('CH$LINK: INCHIKEY'): s.inchikey=line.split('INCHIKEY',1)[1].strip()
        elif 'PRECURSOR_M/Z' in line: 
            m=re.search(r'[-\d.]+', line.split('PRECURSOR_M/Z')[1]); 
            if m: s.precursor_mz=float(m.group())
        elif 'PRECURSOR_TYPE' in line: s.adduct=line.split('PRECURSOR_TYPE',1)[1].strip()
        elif 'ION_MODE' in line: s.ion_mode=line.split('ION_MODE',1)[1].strip()
    # peaks
    inpk=False
    for line in text.splitlines():
        if line.startswith('PK$PEAK'): inpk=True; continue
        if inpk:
            if line.startswith('//') or not line.strip(): break
            p=line.split()
            if len(p)>=3:
                try: s.peaks.append((float(p[0]), float(p[2])))
                except: pass
    return s

if __name__=='__main__':
    import glob
    for f in sorted(glob.glob('data/MSBNK*.txt')):
        s=parse(open(f).read())
        print(f"{s.accession} | {s.name[:24]:24} | {s.formula:12} | {s.adduct:8} | prec {s.precursor_mz} | {len(s.peaks)} peaks")

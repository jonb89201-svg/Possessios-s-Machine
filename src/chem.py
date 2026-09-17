"""Competition-exact structure matching: tautomer-canonical InChIKey14."""
from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit import RDLogger; RDLogger.DisableLog('rdApp.*')
_TE = rdMolStandardize.TautomerEnumerator()
def canon_ik14(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None: return None
    try: m = _TE.Canonicalize(m)
    except Exception: pass
    try: return Chem.MolToInchiKey(m)[:14]
    except Exception: return None

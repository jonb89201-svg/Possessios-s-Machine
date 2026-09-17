"""casmi_run — end-to-end CASMI submission harness. Reads train/test parquet (competition schema),
runs the analog-propagation prong (matchms modified-cosine), emits a valid submission.csv.
The moment the real data lands: `python src/casmi_run.py --train train.parquet --test test.parquet`.

Walls baked: predict PER molecule_id (aggregate its spectra); every molecule_id exactly once;
<=25 ';'-joined SMILES, no nulls (fallback guess if empty); mz arrays sorted for matchms.
FRONTIER (v2): 2.5M train needs embedding/blocking not brute force; add formula-retrieval + de-novo prongs;
merge prongs into one ranked 25; dedup by tautomer-canonical InChIKey14 (chem.canon_ik14)."""
import os, sys, argparse
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from matchms import Spectrum
from matchms.filtering import normalize_intensities
from matchms.similarity import ModifiedCosineGreedy
import warnings; warnings.filterwarnings("ignore")

def _spec(row):
    mz=np.asarray(row["ms2_mzs"],float); it=np.asarray(row["ms2_normalized_intensities"],float)
    o=np.argsort(mz)
    return normalize_intensities(Spectrum(mz=mz[o], intensities=it[o],
        metadata={"precursor_mz":float(row["precursor_mz"])}, metadata_harmonization=False))

def predict(test_df, train_df, topk=25, tol=0.02, min_match=3, fallback="C"):
    mc=ModifiedCosineGreedy(tolerance=tol)
    train=[(_spec(r), r["normalized_smiles"]) for _,r in train_df.iterrows()]
    out=[]
    for mol_id, grp in test_df.groupby("molecule_id"):
        qs=[_spec(r) for _,r in grp.iterrows()]
        best={}
        for q in qs:
            for tspec,smi in train:
                try: r=mc.pair(q,tspec)
                except Exception: continue
                s=float(r["score"]); n=int(r["matches"])
                if n>=min_match and s>best.get(smi,0.0): best[smi]=s
        ranked=sorted(best, key=best.get, reverse=True)[:topk]
        out.append((mol_id, ";".join(ranked) if ranked else fallback))
    return pd.DataFrame(out, columns=["molecule_id","smiles"])

def validate(sub, test_df):
    ids=set(test_df["molecule_id"].unique())
    assert set(sub["molecule_id"])==ids, "every molecule_id exactly once"
    assert sub["molecule_id"].is_unique, "no repeated molecule_id"
    assert sub["smiles"].notna().all() and (sub["smiles"].str.len()>0).all(), "no null/empty smiles"
    assert (sub["smiles"].str.split(";").map(len)<=25).all(), "<=25 guesses"
    return True

def _selftest():
    from massbank import parse
    import glob
    rows=[]
    for f in glob.glob(os.path.join(os.path.dirname(__file__),"..","data","massbank_samples","*.txt")):
        s=parse(open(f).read())
        if not s.peaks or not s.precursor_mz or not s.smiles: continue
        mz=[p[0] for p in s.peaks]; it=[p[1] for p in s.peaks]; m=max(it) or 1
        rows.append(dict(accession=s.accession, molecule_id=s.smiles, precursor_mz=s.precursor_mz,
            adduct=s.adduct, ms2_mzs=mz, ms2_normalized_intensities=[x/m for x in it],
            normalized_smiles=s.smiles, inchikey14=(s.inchikey or "")[:14]))
    df=pd.DataFrame(rows)
    # hold out one spectrum of any compound that appears >=2x -> a class-1-reachable test case
    dup=df["molecule_id"].value_counts(); dup=dup[dup>=2].index.tolist()
    test=df[df["molecule_id"].isin(dup)].groupby("molecule_id").head(1).copy()
    test["molecule_id"]=["m_%04d"%i for i in range(len(test))]  # anonymize like the real test set
    train=df.drop(index=test.index if False else df[df["molecule_id"].isin(dup)].groupby("molecule_id").head(1).index)
    # parquet round-trip to prove the real IO path
    os.makedirs("data/selftest",exist_ok=True)
    train.to_parquet("data/selftest/train.parquet"); test.to_parquet("data/selftest/test.parquet")
    tr=pd.read_parquet("data/selftest/train.parquet"); te=pd.read_parquet("data/selftest/test.parquet")
    # map anonymized test back to true smiles for scoring
    truth=dict(zip(test["molecule_id"], test["normalized_smiles"]))
    sub=predict(te, tr); validate(sub, te); sub.to_csv("data/selftest/submission.csv",index=False)
    hits=0
    for _,r in sub.iterrows():
        guesses=r["smiles"].split(";")
        # reachable iff the true compound had a train neighbor
        if truth.get(r["molecule_id"]) in guesses: hits+=1
    print(f"[selftest] {len(te)} test molecules, {len(tr)} train spectra")
    print(f"[selftest] submission.csv valid: format OK; exact structure recovered: {hits}/{len(sub)}")
    print(sub.to_string(index=False, max_colwidth=44))
    return hits, len(sub)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--train"); ap.add_argument("--test"); ap.add_argument("--out",default="submission.csv")
    ap.add_argument("--selftest",action="store_true")
    a=ap.parse_args()
    if a.selftest: _selftest()
    else:
        tr=pd.read_parquet(a.train); te=pd.read_parquet(a.test)
        sub=predict(te,tr); validate(sub,te); sub.to_csv(a.out,index=False)
        print(f"wrote {a.out}: {len(sub)} molecules")

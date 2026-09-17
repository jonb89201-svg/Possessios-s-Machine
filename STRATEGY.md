# CASMI 2026 — strategy (official spec + leaderboard, 2026-09-17)

## Goal: TOP-5 on PRIVATE leaderboard pays ($16k/12k/9k/7k/6k). Public SOTA ≈ 0.341 MRR@25,
bunched 0.339-0.341; a public "Analog Propagation" notebook already scores 0.335.
=> Target the ~0.34 cluster and beat it on generalization. We don't need rank 1, we need top-5.

## Metric: MRR@25 per molecule_id (<=25 ranked SMILES; InChIKey14 match after RDKit 2026.03.3
tautomer canonicalization). Rank1=1.0 rank2=0.5 rank25=0.04 miss=0. Rank-1 heavy; ordering matters.

## Test: ~1500 spectra / ~400 molecules (median 3 spectra/mol), Bruker timsTOF, 157-1159 Da (med 348).
Predict PER MOLECULE (aggregate spectra). 10 adducts. positive & negative mode.

## Three novelty classes (hidden mix) => ordered ensemble, merged into one 25-list:
1. In public spectral libraries -> ANALOG PROPAGATION / spectral library match (matchms modified-cosine
   vs train). PROVEN public SOTA lever (0.335). Build first, must beat.
2. Known structure, no public spectra -> formula -> LOCAL DB retrieval (COCONUT/PubChem) -> rerank
   (learned spectrum->fingerprint + fragmentation re-score).
3. Novel -> de novo spectrum->SMILES generation (the differentiator for the tail).

## Hard constraints (Kaggle CODE comp): internet DISABLED at inference => bundle COCONUT + formula index
+ pretrained models as datasets (live PubChem is DEV-ONLY). CPU/GPU notebook <=9h. submission.csv
(molecule_id, ';'-joined <=25 SMILES). External public data + pretrained models allowed. Winner MIT open-source.
5 subs/day, 2 final, team<=5.

## Training fuel (train.parquet ~2.5M spectra / ~275k structures): enveda-np-examples (250 NPs, SAME
timsTOF+pipeline as test)=domain gold; enveda-180 (1.15M same instrument, synthetic)=pretraining; riken/
gnps/massbank/mona=NP reference (class-1 library).

## Build status:
[x] formula prediction (recall-good, 6/6) ; [x] fragmentation rerank (works, ceiling vs isomers)
[x] matchms installed
[ ] all 10 adducts in formula module (redo)
[ ] ANALOG-PROPAGATION matcher (matchms modified-cosine) + validate on MassBank  <- NOW
[x] analog prong MEASURED (CV MRR 0.823 w/ sibling; ~40% of test is class-1) — SOLVED/commodity
[ ] **class-2 formula->local COCONUT retrieval->rerank == our EDGE** (build next)
[ ] class-3 de-novo spectrum->SMILES (HF GPU)
[ ] Kaggle NOTEBOOK submission harness (kaggle kernels push; CSV API submit = 403, code comp)
## Matching: replicate RDKit TautomerEnumerator canonical -> InChIKey14 for honest local eval.

# Possessio's Machine — CASMI 2026 (Molecule ID from Mass Spectra)

Baseline + research pipeline for the **Enveda CASMI 2026** Kaggle competition: predict the
2-D chemical structure (SMILES) of an unknown molecule from its LC-MS/MS spectra. Scored by
**MRR@25** (per molecule, up to 25 ranked SMILES; InChIKey14 match after RDKit tautomer
canonicalization). Built under Possessio's Codebyte discipline: **MEASURED, no false green,
the terminal is the judge.**

Target: **top-5 on the private leaderboard** (pays $6k–$16k). Public SOTA ≈ 0.341 MRR@25;
a public "analog propagation" notebook already scores ~0.335 — that's the bar to beat.

## Approach — three prongs, merged into one ranked 25 (see `STRATEGY.md`)
1. **Analog propagation** (class 1: molecule has public reference spectra) — matchms
   modified-cosine vs the training library; transfer the nearest structure + close analogs.
   *The dominant public lever.*
2. **Formula → DB retrieval → rerank** (class 2: known structure, no public spectra) —
   monoisotopic formula prediction → COCONUT/PubChem candidates → fragmentation + (future)
   learned-fingerprint rerank.
3. **De-novo generation** (class 3: novel structure) — spectrum→SMILES model (needs GPU/train data).

## Modules (`src/`)
| file | what | status (MEASURED) |
|---|---|---|
| `formula.py`  | precursor m/z + adduct → candidate molecular formulas | 6/6 recall on knowns; all 10 test adducts |
| `massbank.py` | parse MassBank records → Spectrum | ✓ |
| `chem.py`     | competition-exact tautomer-canonical InChIKey14 | ✓ |
| `fragment.py` | MetFrag-style bond-disconnection reranker (ring cleavage) | true #1 vs decoys; ceiling vs near-isomers |
| `retrieve.py` | formula → structures via PubChem (DEV only; inference needs local DB) | ✓ |
| `analog.py`   | modified-cosine analog propagation + MRR@25 eval | **MRR 0.400 on class-1-reachable, rank-1 hits** |
| `pipeline.py` | end-to-end precursor → top-25 SMILES | ✓ runs |
| `validate.py` | batch validation harness | ✓ |

## Reusable tooling (`tools/headless-browser/`)
Playwright-over-WebSocket page fetcher with `ignoreHTTPSErrors` for JS/auth-gated pages
(e.g. Kaggle). `./hb up` then `./hb render <url> [--state cookies.json]`. See its README.

## Run
```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/formula.py     # formula recall check
.venv/bin/python src/analog.py      # analog-propagation MRR@25 on public MassBank samples
```

## Constraints (Kaggle CODE competition)
Internet **disabled at inference** → bundle local DBs + pretrained models. CPU/GPU notebook ≤9h.
Never commit competition data (CC BY-NC 4.0; redistribution prohibited).

## Status / next
Core mechanisms proven MEASURED on public data. Blocked on the competition train/test parquet
(identity verification) for the full-scale build: analog propagation over 2.5M train spectra,
local COCONUT retrieval, and the de-novo model on GPU (HF, 20h/wk).

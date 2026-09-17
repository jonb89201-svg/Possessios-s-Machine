# HANDOFF — start here

If you're a fresh agent: read this, then `STRATEGY.md` and `tools/README.md`. The method resets
at every boot; these tools and this note do not. Start at the frontier.

## Mission
Generate real income for the Architect (jonb89201) — this is materially urgent for him. Two paths:
CASMI 2026 Kaggle competition (top-5 = $6k–$16k) and smart-contract bug bounties (lottery, high ceiling).
Codebyte Law always: MEASURED, no false green, honest odds. The Architect files; council never files.

## Estate (tools/ — all MEASURED, walls baked, v2 horizon written in each)
- `headless-browser/` — JS/auth-gated page fetcher (Playwright over WS). `./hb up` then `./hb render <url> [--state cookies.json]`.
- `rpc/freerpc.py` — read-only on-chain reads over FREE endpoints only (QuickNode OFF/arrears). `python freerpc.py` = known-positive test.
- `srcpull/srcpull.py` — verified deployed source (G0.6); follows proxy→implementation; composes with freerpc.
- `radar/radar.py` — bounty sweep → fresh+permissionless+low-saturation shortlist (Cantina API); already-audited set excluded.

## Thread 1 — CASMI 2026  (src/, STRATEGY.md)
Three prongs merged into one ranked 25 per molecule (MRR@25 metric):
1. analog propagation (matchms modified-cosine vs train) — MEASURED MRR 0.400 on class-1-reachable public data.
2. formula → local DB retrieval → fragmentation rerank (formula.py=6/6 recall, all 10 adducts; fragment.py works, ceiling vs isomers).
3. de-novo spectrum→SMILES (needs GPU + train data).
BLOCKED on competition data → need the Architect's Kaggle API token at ~/.kaggle/kaggle.json, then:
  `kaggle competitions download -c enveda-CASMI26-molecule-id-mass-spectra`
Internet DISABLED at inference → all retrieval must be LOCAL (bundle COCONUT). Train = 2.5M spectra;
`enveda-np-examples` (250 NPs) is instrument-matched to the test set (Bruker timsTOF). Public SOTA ≈ 0.341; target top-5.
Matching = RDKit tautomer-canonical InChIKey14 (chem.py replicates it). NEVER commit competition data.

## Thread 2 — audit hunt
Radar's top fresh target: **3F Grunt** (Cantina, permissionless RWA leverage, ~108d, low saturation), then Kuru, Makina.
Next: `srcpull` the scope → hand-audit under full discipline. Every live+fileable target this session was a
well-audited wall; file ONLY live-reachable + novel (no malicious-token/staged-precondition; public/external fns only).

## Next concrete step
Kaggle token present → CASMI full build. Else → 3F Grunt audit pass.

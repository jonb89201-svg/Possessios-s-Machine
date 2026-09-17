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

## UPDATE 2026-09-17 — real data in hand, real-scale engine proven
Kaggle token worked. Data (EPHEMERAL, never commit): test.parquet (1213 spectra/400 mols),
train.parquet (2,539,608 spectra / ~275k structures, 3.03GB). Schema matches spec; harness reads it.
Test adducts: [M+H]+ 959, [M-H]- 193, [M+CH2O2-H]- 31, [M+Na]+ 22, rest few. Modes: pos 987 / neg 226.

- `src/streaming_analog.py` — MEASURED: streams all 2.5M train, blocks by 20ppm precursor, memory-bounded
  (never hold train; OOM'd at 0.02Da-absolute + list accumulation — walls baked), 277s, found candidates
  for 400/400 test molecules, emits submission.csv. This is the real-scale analog prong.
- WALL: `kaggle competitions submit` (CSV via API) -> 403 Forbidden. This is a CODE competition:
  scoring is NOTEBOOK-ONLY (and identity verification may also gate it). To actually score/submit:
  push a Kaggle Notebook (`kaggle kernels push`) that attaches the competition data, runs with internet
  OFF, writes submission.csv. That's the real submission path — build it (v2).
- Local scoring impossible (test labels hidden) -> use TRAIN-internal CV for a real MRR number.

### Next concrete steps (in priority)
1. Train-CV MRR (hold out train molecules w/ siblings, analog vs rest) -> real number vs public SOTA 0.341.
2. Notebook submission harness (kaggle kernels push) — the only path to a leaderboard score.
3. Add formula→local-COCONUT retrieval (class 2) + de-novo (class 3); merge prongs; dedup by canon_ik14.

## UPDATE 2026-09-17 (b) — analog prong MEASURED; the real edge is class-2/3
Train CV (src/cv2_analog.py, proper 2-pass: pre-load 400 queries, stream full library):
- **MRR@25 = 0.823, true structure in top-25 for 96% (382/400)** — analog prong alone.
- CRITICAL: this OVERESTIMATES the real test. Train ≈ 9 spectra/structure, so ~all CV queries are
  class-1 (a sibling exists) → analog trivially wins. The real TEST is a hidden 3-class mix
  (1: has ref spectra / 2: known structure no spectra / 3: novel). Public SOTA = 0.341.
- DERIVED: if class-1 ~0.82 and rest ~0, then 0.341 ⟹ class-1 ≈ 40% of test; class-2/3 ≈ 60%.
- STRATEGIC PIVOT: analog is solved + a commodity everyone has. The leaderboard is WON on:
  * class 2 → molecular-formula prediction → LOCAL COCONUT/PubChem retrieval → rerank (this is our edge)
  * class 3 → de-novo spectrum→SMILES generation (HF GPU; the hard tail)
  Build those next. cv_analog.py (single-pass) is a NEGATIVE result: it undercounts (0.100) due to
  ordering bias — kept as the wall (pre-load queries before streaming the library, like cv2/streaming).

## UPDATE 2026-09-17 (c) — submission kernel CONFIRMED end-to-end
kernel/casmi_kernel.py run on real data: valid submission (400/400 molecules, <=25, no nulls),
**100.0% top-1 agreement with the matchms reference** -> the numpy reimplementation is ranking-exact
(the ~1e-4 greedy-tie-break residual changes no rankings). Runtime 21min (fine for Kaggle 9h; numba
speedup = v2). The kernel is submission-ready; only the notebook push + identity verification remain.

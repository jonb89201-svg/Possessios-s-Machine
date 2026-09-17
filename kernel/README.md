# Kaggle submission kernel (the ONLY path that scores — CSV API submit = 403)

`casmi_kernel.py` is self-contained: numpy/pandas/pyarrow only (no matchms/rdkit), so it runs
with **internet OFF** on Kaggle. Its modified-cosine was verified against matchms (mean diff 5e-7,
max 1e-4 = greedy tie-break, ranking-equivalent). It streams the attached competition train set,
blocks by precursor ppm, and writes `submission.csv`. Analog prong only (class-1); v2 adds class-2/3.

## To submit (once identity verification clears — that may be the 403's real cause)
1. Put your Kaggle username in `kernel-metadata.json` (`id` field).
2. `kaggle kernels push -p kernel/`   (attaches the competition data, internet off)
3. On Kaggle: open the kernel, "Submit to Competition" from its output.
5 submissions/day; select up to 2 final.

# Technical Work

Technical research manuscripts, explicit assumptions and reproducible checks.

## CTR_DRBG with AES-256 and DRG.3

The article is organized as an algorithmic conformity argument: the SP800-90A construction, DRG.3 obligations, AIS describing tuples, proofs of the individual properties, and conclusions with remaining assessment questions. The request tuple retains f,g,Sreq=S and phiA/phiB from the cited antecedent. The prose and proof order follow the AIS Hash_DRBG argument. Product comparisons are outside the manuscript.

- [Article PDF](CTR_DRBG/article_ais/main.pdf), [LaTeX](CTR_DRBG/article_ais/main.tex) and [bibliography](CTR_DRBG/article_ais/references.bib).
- [Jordi review edition](CTR_DRBG/article_ais/review-jordi.pdf), with25 contextual notes suppressed in the ordinary edition.
- [Comparison with the rigor of AIS Hash_DRBG](CTR_DRBG/article_ais/RIGOR_REVIEW.md), including critique of tuple conventions and proof obligations.
- [Fixed notation](CTR_DRBG/article_ais/NOTATION.md), [requirement matrix](CTR_DRBG/article_ais/requirements.csv), [proof ledger](CTR_DRBG/article_ais/proof-ledger.csv) and [critical-review history](CTR_DRBG/article_ais/REVIEW.md).
- [Reproduction instructions](CTR_DRBG/article_ais/LEEME.md) and [remaining mathematical tasks](CTR_DRBG/NEXT_STEPS.md).

The analyzed profile uses AES-256 without DF, full128-bit counter increments, fresh conditionally uniform384-bit seed input, and up to2^48 requests per reseed interval. The written bounds are classical ideal-permutation results. Source admissibility is assumed. Concrete-primitive assessment, the additional AIS214 evaluation and extensions to other initialization distributions are distinguished from the derived bounds.

## Reproduce

With Python3.12 and Tectonic, from CTR_DRBG/article_ais:

```text
python verify.py
python verify_local.py
python build.py
python build.py --review-jordi
```

Pass --compiler to select a Tectonic executable. The mathematical checks use exact arithmetic and reduced finite models, need no third-party packages or network, and do not replace the written proofs. Optional PDF rendering uses PyMuPDF and Pillow.

## History and Git workflow

The previous [P64 article](CTR_DRBG/article_v2/main.pdf) is historical and superseded by article_ais. Use codex/ branches and reviewable PRs; do not rewrite published history without instructions. Original third-party documents, downloaded tools, compiler logs and QA renders are not tracked. Source URLs and hashes are recorded without asserting redistribution rights.

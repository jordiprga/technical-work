# Technical Work

Technical research manuscripts, explicit assumptions and reproducible checks.

## CTR_DRBG and AIS 20/31 DRG.3

The current manuscript follows the AIS Hash_DRBG example: the request 9-tuple and two seeding 4-tuples come first, followed by primitive hypotheses and the requirement arguments. XDRBG is a presentation reference only.

- [Current PDF](CTR_DRBG/article_ais/main.pdf), [LaTeX](CTR_DRBG/article_ais/main.tex) and [bibliography](CTR_DRBG/article_ais/references.bib).
- [Requirement matrix](CTR_DRBG/article_ais/requirements.csv), [proof ledger](CTR_DRBG/article_ais/proof-ledger.csv) and [critical review](CTR_DRBG/article_ais/REVIEW.md).
- [Reproduction instructions](CTR_DRBG/article_ais/LEEME.md) and [next mathematical tasks](CTR_DRBG/NEXT_STEPS.md).

For AES-256 without DF and with fresh uniform 384-bit seeding, the new partial-permutation argument covers the full NIST interval of 2^48 requests, public adaptive additional input and terminal-state disclosure. It retains shared-key dependencies and removes the earlier artificial 64-request restriction. Numerical claims are exact ideal-permutation results for ordinary primitive computations, not unconditional concrete-AES theorems.

The manuscript explicitly leaves open the complete adaptive-profile infeasibility condition of AIS214 beyond ordinary computation, and the separate DF seeding entropy implication. These are not counterexamples to CTR_DRBG. The theorem does not claim unrestricted DRG.3 conformity. Source admissibility/sufficiency and output release/erasure remain explicit conditions, as in the AIS evaluation method.

## Reproduce

With Python 3.12 and Tectonic, from `CTR_DRBG/article_ais`:

```text
python verify.py
python build.py
```

The mathematical checker needs no third-party packages or network. Pass `--compiler` to build.py for another Tectonic executable. [verification.json](CTR_DRBG/article_ais/verification.json) records exact arithmetic and reduced-model checks; these do not replace the written probability argument or expert review.

## History and Git workflow

The previous [P64 manuscript](CTR_DRBG/article_v2/main.pdf) is retained as history and superseded by article_ais. Use `codex/` branches and reviewable PRs. Never rewrite published history without instructions.

Original third-party documents, downloaded tools and QA renders stay outside Git. Sanitized source URLs and SHA256 values are tracked. No blanket redistribution license for third-party documents is asserted.

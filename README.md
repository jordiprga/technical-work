# Technical Work

Technical research manuscripts, explicit assumptions and reproducible checks.

## CTR_DRBG and AIS 20/31 DRG.3

The first work studies algorithmic DRG.3 conformity of CTR_DRBG with AES-256. Source sufficiency is an explicit hypothesis. The current manuscript develops an ideal-cipher argument for a bounded profile P64; it does not establish the full SP 800-90A parameter range or unconditional concrete-AES security.

- [Current PDF](CTR_DRBG/article_v2/main.pdf)
- [LaTeX source](CTR_DRBG/article_v2/main.tex) and [bibliography](CTR_DRBG/article_v2/references.bib)
- [Requirement matrix](CTR_DRBG/article_v2/requirements.csv), [proof ledger](CTR_DRBG/article_v2/proof-ledger.csv) and [critical review](CTR_DRBG/article_v2/REVIEW.md)
- [Reproduction instructions](CTR_DRBG/article_v2/LEEME.md)
- [Next mathematical tasks](CTR_DRBG/NEXT_STEPS.md)

P64 uses one evaluated instance, at most 64 total calls with fixed public lengths, a 128-bit counter, no derivation function or Generate additional input, an independent uniform 384-bit seed, release after Update and temporary-state erasure. The manuscript keeps these restrictions visible and separates classical and quantum-query bounds. The target remains a justified argument comparable in depth to the AIS Hash_DRBG example; the conservative 64-call limit is not a demonstrated flaw in CTR_DRBG.

## Checks

With Python 3.12, from `CTR_DRBG/article_v2`:

```text
python -m pip install -r requirements-dev.txt
python verify_chain.py
python verify.py
python build.py
```

The build requires Tectonic on PATH. Pass `--compiler` to build.py for another executable path. PDF generation and numerical checks do not replace the written probability proof or a critical mathematical review.

## Git workflow

Use `codex/` branches and focused commits. Push a branch and review its pull request before merging. Keep assumptions, scope and unresolved generalizations in the commit and PR descriptions.

Original third-party documents, historical local drafts, compiler caches and QA renders stay in the local research library. The repository contains sanitized source URLs and SHA256 values. No blanket redistribution license for third-party documents is asserted.

# CTR_DRBG / DRG.3

Current manuscript: [article and PDF](article_v 2/main.pdf), [LaTeX](article_v 2/main.tex), [bibliography](article_v 2/references.bib).

This is a conditional ideal-cipher argument for P64, not a certificate or a proof for every SP800-90A configuration. The source has sufficient entropy by assumption. P64 uses no DF or Generate additional input, a 128-bit counter, an independent uniform 384-bit seed and at most 64 total requests in a single evaluated instance, with fixed public lengths, output release after Update and temporary-state erasure.

See [reproduction](article_v 2/LEEME.md), [requirements](article_v 2/requirements.csv), [proof ledger](article_v 2/proof-ledger.csv), [critical review](article_v 2/REVIEW.md) and [next mathematical tasks](NEXT_STEPS.md).

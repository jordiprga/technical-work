# CTR_DRBG conformity research

The current work is [article_ais/main.pdf](article_ais/main.pdf), with [LaTeX](article_ais/main.tex), [review record](article_ais/REVIEW.md), [mathematical ledger](article_ais/proof-ledger.csv) and [reproduction instructions](article_ais/LEEME.md).

It introduces the AIS properties, explains the AES key-size exclusions, defines the secrecy and function requirements, and develops the tuples into prediction and inversion arguments. The detailed composition proof is in the appendices. The full-interval ordinary-computation proof replaces the earlier P64 bound; public adaptive additional input is included. Source sufficiency is assumed explicitly. Read the theorem's exact model and the remaining AIS214/DF obligations before inferring conformity. There is no claimed general nonconformity result.

The previous article_v2 is retained as a historical version. The local source library and compiler are not redistributed through Git.

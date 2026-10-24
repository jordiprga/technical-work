# Remaining mathematical work

Completed in article_ais: exact AIS tuple reconstruction; no-DF source translation; full2^48-request ordinary-computation partial-table coupling; derived/repeated key dependencies; public adaptive additional input; terminal-state output protection; any-preimage alignment including adaptive stopping; exact numerical verification and separate critical review.

1. Close the AIS214 nonclassical infeasibility requirement for the complete adaptive profile. Classical transcript factorization does not automatically prove coherent-access composition. The earlier fixed-schedule argument cannot silently be generalized. A primitive hypothesis that simply assumes historical secrecy would be circular. The main article keeps this limitation brief and does not turn the conformity paper into a separate oracle-security paper.
2. If extending to the DF profile, justify the exact effective-key entropy implication of NIST's384-bit Block_Cipher_df invocation under the chosen seed premise/model. SP800-90B's AES256 tabled output is256 bits; changing requested output length changes the BCC input. A mere computational-indistinguishability statement does not establish min-entropy. Alternatively state an adequate postconditioning premise explicitly, without claiming it follows automatically from raw seed entropy.
3. Obtain human cryptographic review of the full mathematical argument and an implementation-specific assessment of source admissibility, conceptual atomicity, erasure and primitive adequacy. Agent review is not certification.

None of these open obligations is a demonstrated attack on compliant CTR_DRBG. The paper gives concrete counterexamples only to an insufficient seed-entropy inference and to releasing output before the evaluated atomic boundary.

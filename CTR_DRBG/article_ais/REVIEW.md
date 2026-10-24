# Review of the AIS-structured rewrite

This record distinguishes mathematical derivations, finite checks, independent agent review and the expert/certification judgment that is still required. Agent agreement is not expert certification.

The manuscript follows AIS paragraphs 1013–1075: request tuple, seeding tuples, initial/effective state, primitive hypotheses, observation reduction, directional secrecy, enhanced backward secrecy, remaining requirements and summary. XDRBG provides presentation examples only.

## Objections resolved

1. **Artificial 64-request limit.** The previous proof charged every key repetition. The new proof retains repeated keys with compatible disjoint entries and charges input/output overlap instead. The complete NIST interval is included; no general CTR_DRBG weakness was inferred from the old proof's limitation.
2. **False independent-transition model.** Three consecutive AES outputs are not an independent random function of key/counter. Their shared blocks remain intact. Private batches are a counting construction coupled to the real shared-key permutation family.
3. **Adjacent batch dependence.** A row's final outputs determine the next key. Input overlaps use a conditional state count; output overlaps condition immediately before the fresh next private permutation. No independence between a row and its next state is asserted.
4. **Final compatible tables are insufficient.** A sequential partial-table coupling is supplied, with the correct uniform marginal. Shared sampling stops at the first conflict; the calculations then continue separately according to their own laws.
5. **Future and past external computations.** Conditioning the whole public transcript and the independent external tables leaves the historical hidden triples factorized. The edge count includes computations that precede a future conflicting row.
6. **Additional-input masks.** Nonempty input causes a zero-output pre-update batch and an output/post-update batch using the same public mask. XOR is a bijection; it need not be a modular translation. At most two batches per request are counted.
7. **Adaptive terminal stopping.** The final update triple is not asserted to be marginally independent of the external cipher. Explicit density domination introduces Gamma=(N)_3/(N-b)_3 as a multiplicative search correction.
8. **Any preimage versus original state.** The inverse-triple alignment count covers every predecessor. Three verification evaluations are appended; six with a pre-update. Whole table grants are used only to bound the private search, never in the partial-table coupling.
9. **Public parameters of inversion.** The actual additional input and length are fixed and disclosed, as AIS212 specifies. Returning a different additional input after observing the target is a different inversion question and is not claimed secure.
10. **Partial target disclosure and application leakage.** Prediction uses global joint density domination over every public request, permitting partial-block disclosure and online target selection. A reviewer found a counterexample to the stronger local factor: after seeing block prefixes, select two equal prefixes and use their distinct final bits. The global factor covers this selection, even if only one final bit is predicted; verify.py retains the exact finite counterexample as a regression check. Subsequent public choices cannot inspect withheld target bits; an application that publishes those bits through later inputs has itself leaked them. No historical Update-triple disclosure is added to the coupling interface.
11. **Initial source premise.** The main composition proof uses fresh perfect conditional uniform384. The separate368/378 seed-entropy bounds prove only the initial entropy projection and are not claimed to extend the main theorem.
12. **AIS tuple exactness.** Corrected the order to S,Sreq,R,A,I and the phi0 domain to Sreq×A; reseed has old state first.
13. **Conditional entropy notation.** Both sides of the DF fibre inequality condition on the same fixed history.
14. **SP800-90B conditioning.** Table1 lists AES256 Block_Cipher_df with256-bit output. CTR_DRBG requests384; the requested length changes the BCC input. The vetted listing alone does not establish the precise entropy implication in this other map. Computational indistinguishability is not silently substituted for min-entropy.

## Validation boundaries

The arithmetic and reduced models are checked by verify.py. The symbolic probability argument is written and independently reviewed, not machine-formalized in a proof assistant. The publication-style manuscript still requires human cryptographic review. No source certification, product certification, side-channel resistance or universal claim for all CTR_DRBG parameter choices is inferred.

## Remaining mathematical condition, not silently certified

AIS214 also requires successful nonclassical attacks to remain infeasible. The new full adaptive partial-table theorem proves ordinary-computation bounds. The prior fixed-schedule analysis cannot automatically be generalized to adaptive coherent computation; a classical conditional factorization is insufficient to do so. An adaptive-reprogramming theorem was investigated, but its fresh-point premise does not directly cover labels derived from a preceding hidden permutation table. No claimed application was inserted without proving that intermediate step. The theorem and abstract now explicitly retain this limit, rather than asserting complete DRG.3 conformity.

The mathematical and critical reviewers accepted the corrected classical core with these scope limits. Human cryptographic review remains necessary.

# Review of the AIS-structured rewrite

This record distinguishes mathematical derivations, finite checks, independent agent review and the expert/certification judgment that is still required. Agent agreement is not expert certification.

The manuscript follows AIS paragraphs 1013–1075: request tuple, seeding tuples, initial/effective state, primitive hypotheses, observation reduction, directional secrecy, enhanced backward secrecy, remaining requirements and summary.

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

## Expository revision, 25 October 2026

The manuscript now supplies the AIS/90A context, the effective-state exclusion of AES-128 and AES-192, and the BSI browser and Woodage–Shumow antecedents. Each claimed property is defined before use, including the observer's information and the granularity/compromise boundary. The request maps lead to the two concrete questions: predicting output and finding a predecessor of the final Update.

Normative review checked the property definitions and source anchors. Mathematical review checked preservation of the global prediction bound, Update order, inverse alignment and full-interval constants. Critical review checked the narrative and retained scope. Corrections included the computational meaning of effective state, the full strength requirement for controlled input, definitions of all symbols before use, and the distinction between a working-state preimage of the final Update and a predecessor of the complete transition.

The complete partial-table proof and adaptive-stopping argument remain in appendices. No result was strengthened by the reorganization. The general conformity theorem was removed; the final discussion maps the mathematical results to the requirements with the same premises and limits. Production history and verification workflow are kept outside the article. The bibliography contains only the technical sources used by its argument.

## Mathematical-development revision, 25 October 2026

The introduction and definitions were condensed without dropping the properties or changing the profile. The main text now derives the exact private block/triple laws, the masked state and key distributions, counter-interval intersection equivalence, pair conflict bounds, public multiplicity and the per-external-edge decomposition. These are combined before the prediction argument rather than presented only as an appendix result.

Successor and predecessor cases are explicit for positions within a request and across its boundary. A separate local count treats fixed observed and target positions and bit projections; the global density argument remains mandatory for adaptive selection. The candidate last output is reconstructed algebraically from the first revealed Update value under a candidate old key.

Separate mathematical and critical review checked these identities. Corrections fixed both sets of positions before the local count and replaced a random sum over adaptive lengths in the statistical-distance display with a deterministic worst-case bound. Normative review restored the explicit computational hardness in the one-wayness definition, defined the pre-request view, and excluded the nonexistent predecessor of the first output. The global model/source limits remain unchanged; no theorem states general DRG.3 conformity.

`verify_local.py` checks 6,630 projection cases, 44,032 masked-key marginals, 576 interval equivalences and 322,560 inverse-counter cases in reduced spaces. These finite checks support the written derivations and are not formalization of the full generator. The full-size rational bounds still pass `verify.py`.

## Requirement traceability and browser comparison, 25 October 2026

The abstract now identifies the algorithmic DRG.3 conformity objective. Each substantive proof closes with its requirement, actual target, supporting results and conditional conclusion. The final table and requirements.csv give explicit result identifiers and distinguish source premises, exact specification conditions, classical model results and assessment obligations. No mathematical result or source premise was strengthened.

The NIST-to-tuple bridge identifies Update, Instantiate, Reseed and Generate section numbers. The BSI comparison separates representation from configuration: removing an unchanged public request counter from Sreq is justified by a commuting projection and induction over emitted blocks; adding the configuration singleton and exhausted-state guard changes no successful output. The no-DF f/g maps and seeding algebra match the BoringSSL tuple on common parameters/domains.

A substantive scope correction is explicit: the browser study increments only64 low counter bits in Corecrypto and32 in BoringSSL, whereas the present proof uses all128. Corecrypto uses DF, byte-aligned requests capped at2^15 bits and no Generate auxiliary input in Safari's wrapper. BoringSSL uses noDF with an operational2^12-request reseed policy and a separate core2^48 guard. Thus neither implementation is claimed covered by substituting its name into the present full-counter theorem. Extending the modular-intersection argument to its counter convention requires a separate check. The previous broad statement that the tuples were simply identical would be incorrect.

Independent normative and mathematical review is required for these correspondences and conclusions; final review outcomes are recorded below. The revision does not claim a result for DF or close the complete AIS214 assessment.

The mathematical reviewer corrected the composition typing by fixing actual public parameters a,p before composing phiA and phiB. The explicit state embedding iota appends theta; the projection identities are now typed on the common configuration/domain. The normative reviewer independently confirmed the NIST section numbers, BSI no-DF f/g and seed/reseed maps, and the operating/core distinction in reseed limits. The critical reviewer also distinguished Corecrypto's2^15-bit wrapper/tuple cap from the2^16-bit core rejection guard reproduced in the study.

A substantive statistical-scope objection was accepted: an output-only test need not imply that the public input controller made no primitive computations. The distance bound now includes epsilon(Qc), yielding2^-57+Qc*2^-253, where Qc counts controller computations;2^-57 alone is stated only for Qc=0. The requirement table, CSV and proof ledger were corrected accordingly. This strengthens traceability by exposing the necessary budget instead of silently imposing a zero-query controller.

The reduced-domain checker additionally passes133120 same-parameter tuple-projection/Generate comparisons, including nonempty zero masks and restricted/full counter widths on their respective identical configurations. It deliberately does not establish a security result for those restricted counter widths. The general projection is proved by the commuting equations and loop induction, not inferred from enumeration.

Final review: mathematical and critical reviewers accepted the corrected tuple typing, same-parameter projection, requirement conclusions and controller-budget statistical bound without a remaining blocking objection in this revision. Full-size exact rational checks and the reduced-domain checks pass. The final18-page PDF was rendered and visually inspected, including the parameter and requirement tables; no undefined references, overfull boxes or margin violations were found. This is agent review and local verification, not external cryptographic approval or a proof-assistant formalization.

## Temporary author-review edition requested by Jordi

Added25 contextual Spanish review notes, visibly marked Solo Jordi and keyed to the adjacent argument. They identify goals, AIS/BSI origins, representation/configuration differences, conditional distributions, adaptive selection, terminal compromise, any-preimage inversion, controller queries and remaining obligations. They introduce no new mathematical result. The wrapper review-jordi.tex enables them; the ordinary main edition suppresses them. This temporary review layer follows the user's explicit instruction and is not publication text.

Independent critical review of the notes corrected three explanations: the overlap bound conservatively charges some compatible coincidences too; inverse alignment characterizes working-state preimages of final Update, while an old state must also pass pre-Update; and the DF note identifies an undeveloped entropy justification rather than suggesting that a primitive modeling hypothesis must be proved as an identity. The article body with notes removed and the extracted clean-PDF text were compared against the previous commit and are unchanged.

Delivery validation: the annotated PDF has21 pages and all25 review notes; its equation, proposition, lemma, definition and section numbers match the clean edition. Every final review page was rendered and visually inspected, including the revised inverse explanation. No unresolved references, overfull boxes or margin violations were found. Mathematical tests were not rerun for this annotation-only change: the article body after stripping the review layer and the extracted18-page clean PDF were checked identical to the preceding commit.

## BSI describing tuple adopted as the primary formulation

At the user's request, the primary definition now retains BSI's f/g, Sreq=S and phiA/phiB composition, with explicit function domains. The earlier reduced tuple was behaviorally equivalent but unnecessarily obscured continuity with the BSI/AIS exposition. The fixed configuration theta is external and the full state is (K,V,c). The exhausted-counter convention remains. Seeding/reseeding return the corresponding full triple.

Projected cryptographic pairs are now denoted sigma_i in the probability argument, explicitly derived from the full tuple; they do not replace it. The full-state inverse includes a deterministic public-counter consistency check that only restricts candidates. The input functions follow the BSI no-DF padding modification, not its Corecrypto DF configuration; counter width and other profile differences remain explicit. No prediction or inversion bound is strengthened.

Normative and mathematical reviewers independently checked this reformulation and identified the checks retained in the edit: no free request length in phireq, no double advancement of the working counter in phiB, totalized public-counter update, and unchanged primitive evaluations and compromise information. Critical review and final compilation results follow below.

Final independent mathematical and critical reviews found no new typing/equivalence error: phireq has no free p; phiB receives the post-phiA state and does not double-count output-loop increments; the full public counter is preserved in temporary steps and incremented once in phiB. The fixed theta symbol was clarified as a profile label, not a variable external parameter. The verifier checks the full triple and f/g composition against procedural Generate, including empty/nonempty-zero inputs.

Both exact checkers pass, including133120 tuple/Generate cases. The probability-proof text was compared against the preceding commit and is unchanged after undoing the declared sigma pair notation and removing the explanatory projection/public-counter sentences. The clean19-page and annotated22-page PDFs were rendered and visually inspected, with matching result numbers and no unresolved references, overfull boxes or margin violations. The requirement CSV has10 valid rows and all mathematical identifiers resolve. These checks preserve the existing model/source limits.

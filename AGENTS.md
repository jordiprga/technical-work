# Technical Work

This repository contains technical research manuscripts, their explicit assumptions, source provenance and reproducible checks. It is independent of the surrounding AIS knowledge-base extraction and the separate ESV dataset.

- Read README.md and the relevant manuscript before changing an argument.
- Distinguish normative statements, primitive-model assumptions, mathematical results and evaluator judgments. Source sufficiency may be assumed explicitly when proving algorithmic properties.
- Do not label an unproved result, failed proof strategy, or reduced-model experiment a general conformity/nonconformity theorem.
- Every nontrivial mathematical step needs a derivation or applicable exact reference and separate critical review. Record counterexamples, objections and resolutions in the work's review log. Use separate agents for normative interpretation, proof development and critical review when investigating a proof.
- State which steps are machine checked and which are manually reviewed. Tests and agent agreement do not establish a theorem.
- For CTR_DRBG, article_ais is the current manuscript; article_v2 is historical. Follow the AIS Hash_DRBG order: tuples, primitive hypotheses, derivations and requirement summary. XDRBG supplies format only. The current ordinary-computation proof covers the full NIST interval without DF and includes public adaptive additional input. Keep the uniform384/ideal-permutation premises, AIS214 adaptive nonclassical gap and DF seeding obligation explicit; do not label the result unrestricted DRG.3 conformity.
- Keep originals, downloaded compiler/packages, local notes, QA renders and compiler logs outside Git. Track bibliography, sanitized URLs/hashes, proof sources, the deliverable PDF and small verification records. Never commit credentials, machine paths or private correspondence.
- Use codex/ branches, focused commits and reviewable PRs. Never rewrite published history without instructions.
- Run the standalone checks for mathematical changes, compile and visually inspect the PDF for manuscript changes, and check the staged diff before pushing. Do not regenerate the surrounding AIS/ESV datasets for this research.

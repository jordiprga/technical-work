# Technical Work

This repository contains technical research manuscripts, their explicit assumptions, source provenance and reproducible checks. It is independent of the surrounding AIS knowledge-base extraction and the separate ESV dataset.

- Read README.md and the relevant manuscript before changing an argument.
- Distinguish normative statements, primitive-model assumptions, mathematical results and evaluator judgments. Source sufficiency may be assumed explicitly when proving algorithmic properties.
- Do not label an unproved result, failed proof strategy, or reduced-model experiment a general conformity/nonconformity theorem.
- Every nontrivial mathematical step needs a derivation or applicable exact reference and separate critical review. Record counterexamples, objections and resolutions in the work's review log. Use separate agents for normative interpretation, proof development and critical review when investigating a proof.
- State which steps are machine checked and which are manually reviewed. Tests and agent agreement do not establish a theorem.
- For CTR_DRBG, article_v2 is the current manuscript. Keep P64/ideal-cipher restrictions visible until an explicitly reviewed argument extends them. The goal is a justified algorithmic DRG.3 proof at the level of the Hash_DRBG example in AIS20/31 v3.0.
- Keep originals, downloaded compiler/packages, local notes, QA renders and compiler logs outside Git. Track bibliography, sanitized URLs/hashes, proof sources, the deliverable PDF and small verification records. Never commit credentials, machine paths or private correspondence.
- Use codex/ branches, focused commits and reviewable PRs. Never rewrite published history without instructions.
- Run the standalone checks for mathematical changes, compile and visually inspect the PDF for manuscript changes, and check the staged diff before pushing. Do not regenerate the surrounding AIS/ESV datasets for this research.

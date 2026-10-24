# Revision 2: critical review

Normative reconstruction, derivation and critical review were separate agent passes. They are not external expert approval. The sources and the actual assembled manuscript were read by the critical reviewer; no indispensable mathematical objection remained after corrections.

Resolved objections:
1. Output-derived keys are not independently assumed uniform: the private-permutation batch law proves their conditional distribution.
2. Entire old-output protection is proved, not inferred merely from whole-state inversion difficulty.
3. Any preimage is covered: candidate-table inverse alignment is counted separately from the planted predecessor.
4. Queries made before future key labels are chosen are included in BAD.
5. Terminal key collisions are counted; the finite-volume restriction is explicit.
6. Target bits cannot leak through adaptive request length/metadata. Quantum profile fixes the length schedule; the interactive hybrid retains online disclosure/target choice under the non-leakage condition.
7. r known blocks must be complete blocks. Other bits of the same target blocks cannot be given as side information.
8. Quantum inversion success uses a predicate depending on the queried oracle. Three verification queries were appended before the hybrid comparison.
9. Quantum marking simulation uses two selection-bit queries per primitive query; its search term includes this factor.
10. Numerical inversion coefficient includes both historical-label queries and nonhistorical aligned-preimage search.

All finite inequalities were rerun with exact fractions. Four SMT identities from the earlier verification remain available. The full probability and quantum proof is written and manually reviewed, not formalized end-to-end in a proof assistant. The toy enumeration checks9216 virtual trajectories, not the real AES domain. No full DRBG implementation, AES test vectors or statistics battery is offered as a substitute for a proof.

Remaining scope: the source is assumed sufficient; accepting idealcipher modeling for AES is explicit. The proof concludes only for P64: one evaluatedinstance, at most64calls, fixed length schedule, ctr128, noDF/noadditional, release after Update, erase temporary state, terminal compromise. FullNIST volume, DF, hostileadditional and multiple-instance/lifetime accumulation are not claimed. Quantum adaptive request lengths are not claimed. For the fullvolume the current key-repeat loss is about2^-161; that is a proof-bound limitation, not a demonstrated attack.

# Next mathematical work

The objective is a justified algorithmic DRG.3 argument comparable in depth and explicit assumptions to the AIS Hash_DRBG example, with source sufficiency assumed. The P64 manuscript is a bounded-profile result and the starting point, not the agreed endpoint for the unrestricted algorithm.

1. Replace the proof's blanket BAD event for repeated keys by a shared-table analysis that distinguishes key equality from counter/input overlaps. Preserve all dependencies introduced by output-derived keys.
2. Prove quantitative lifetime prediction and any-preimage bounds for that refined experiment. Evaluate the full NIST request range; a key-repeat union bound near 2^-161 is a limitation of the current method, not an attack.
3. Extend the primitive model to Block_Cipher_df and adversarial additional input with explicit hypotheses, or construct a precise counterexample for an identified configuration. Do not transfer the no-input result automatically.
4. Reconcile each derived lemma with DRG.3.5--.10, the exact secrecy granularities and AIS's modeling/evaluator assumptions. Keep source/entropy hypotheses separate from these algorithmic tasks.

Each extension needs a written derivation, counterexample search, separate review and reproducible checks of the exact obligations that a tool can verify. Mathematical failure to close an argument is recorded as such, not promoted to nonconformity.

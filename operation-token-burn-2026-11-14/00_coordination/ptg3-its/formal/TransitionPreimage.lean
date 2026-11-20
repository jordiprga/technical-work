import CTRProfile
import Reduction

/-! Connect the actual SP 800-90A state transition to the finite uniform-target
    bound, including the finite, ordinary PRP candidate verifier. -/
namespace PTG3.TransitionPreimage

open CTRProfile PTG3.Reduction

abbrev Triple := Word × Word × Word
abbrev KeyCounter := Key × Word

def unpack (s : State) : Triple := (s.key.1, s.key.2, s.counter)
def pack (z : Triple) : State := ⟨(z.1, z.2.1), z.2.2⟩

def candidatePoint (c : Cipher) (s : State) (d : Option State) : KeyCounter :=
  let pre := tupleRequest c s d
  (pre.key, inc pre.counter)

def fingerprint (c : Cipher) (kv : KeyCounter) : Triple :=
  triple inc (c.encrypt kv.1) kv.2

def emitChallenge (d : Option State) (z : Triple) : State :=
  xorState (pack z) (d.getD zeroState)

theorem accept_iff_triple (c : Cipher) (d : Option State) (old : State) (z : Triple) :
    (nistGenerate c old d).2 = emitChallenge d z ↔
      fingerprint c (candidatePoint c old d) = z := by
  have hh := exposed_triple c old d
  constructor
  · intro eq
    rw [eq, emitChallenge, mask_cancels] at hh
    exact congrArg unpack hh.symm
  · intro eq
    have he : rawTriple c ⟨(tupleRequest c old d).key, inc (tupleRequest c old d).counter⟩ =
        pack z := congrArg pack eq
    rw [he] at hh
    simpa only [mask_cancels, emitChallenge] using
      congrArg (fun s => xorState s (d.getD zeroState)) hh

def lifted (c : Cipher) (d : Option State) (inv : State → Option State)
    (z : Triple) : Option KeyCounter :=
  (inv (emitChallenge d z)).map (fun old => candidatePoint c old d)

def transitionWin (c : Cipher) (d : Option State) (inv : State → Option State)
    (z : Triple) : Nat :=
  match inv (emitChallenge d z) with
  | none => 0
  | some old => if (nistGenerate c old d).2 = emitChallenge d z then 1 else 0

theorem checker_equals_inversion (c : Cipher) (d : Option State)
    (inv : State → Option State) (z : Triple) :
    transitionWin c d inv z = inverted (fingerprint c) (lifted c d inv) z := by
  cases hi : inv (emitChallenge d z) with
  | none => simp [transitionWin, lifted, inverted, hi]
  | some old => simp [transitionWin, lifted, inverted, hi, accept_iff_triple]

def checks (v : Word) : List Word :=
  let v₃ := inc (inc (inc v))
  [inc v₃, inc (inc v₃), inc (inc (inc v₃))]

theorem six_points_fresh (v : Word) :
    ([inc v, inc (inc v), inc (inc (inc v))] ++ checks v).Nodup := by
  simp only [checks, List.cons_append, List.nil_append, List.nodup_cons,
    List.mem_cons, List.not_mem_nil, or_false, List.nodup_nil, and_true]
  unfold inc
  bv_decide

/-- Both counts use exactly the same enc, increment, input, state checker and
    verifier at the CTR word sizes. Hidden history and coins are held fixed
    by the supplied inverter; they can then be averaged. -/
theorem uniform_transition_le_aes_verifier (c : Cipher) (d : Option State)
    (inv : State → Option State) (keys : List KeyCounter) (targets : List Triple)
    (hk : keys.Nodup) (ht : targets.Nodup)
    (allK : ∀ k, k ∈ keys) (allT : ∀ t, t ∈ targets) :
    total targets (transitionWin c d inv) ≤ total keys (fun kv =>
      accepts inc c.encrypt (lifted c d inv) checks (c.encrypt kv.1) kv.2) := by
  calc
    _ = total targets (inverted (fingerprint c) (lifted c d inv)) :=
      total_congr targets (checker_equals_inversion c d inv)
    _ ≤ _ := uniform_target_le_actual_verifier inc c.encrypt (lifted c d inv) checks
      keys targets hk ht allK allT

end PTG3.TransitionPreimage

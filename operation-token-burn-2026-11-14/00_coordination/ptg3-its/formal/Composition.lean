import AISProfile
import CTRProfile
import ITS
import CQ

namespace PTG.Composition
open PTGITS

/-- Run exactly the reported transitions; updating the state is part of execution. -/
def referenceRun (step : S → B → B × S) : (n : Nat) → S → Word B n → Word B n
  | 0, _, _ => ()
  | n+1, s, (a, tail) =>
    let (y,t) := step s a
    (y, referenceRun step n t tail)

theorem runAgrees (m : Machine S B) (step : S → B → B × S)
    (same : ∀ s a, step s a = ((m.emit s).enc a, m.next s a))
    (n : Nat) (s : S) (xs : Word B n) :
    referenceRun step n s xs = encode m n s xs := by
  induction n generalizing s with
  | zero => rfl
  | succ n ih =>
    rcases xs with ⟨a, tail⟩
    simp only [referenceRun, encode, same, ih]

def ais (c : AISProfile.Primitives) (p : AISProfile.Block) :
    Machine AISProfile.Key AISProfile.Block where
  emit s := ⟨fun a => (AISProfile.tupleStep c p s (.present a)).1,
    AISProfile.inverseOutput c p s, AISProfile.leftInverse c p s, AISProfile.rightInverse c p s⟩
  next s a := (AISProfile.tupleStep c p s (.present a)).2

def ctr (c : CTRProfile.Cipher) : Machine CTRProfile.State CTRProfile.Word where
  emit s := ⟨CTRProfile.encode c s, CTRProfile.recover c s,
    CTRProfile.recover_encode c s, CTRProfile.encode_recover c s⟩
  next s a := (CTRProfile.nistGenerate c s (some (CTRProfile.physical a))).2

theorem aisRun (c : AISProfile.Primitives) (p : AISProfile.Block) (n : Nat)
    (s : AISProfile.Key) (xs : Word AISProfile.Block n) :
    referenceRun (fun k a => AISProfile.reference c p k 128 a) n s xs =
      ((causalPermutation (ais c p) n s).enc xs) :=
  runAgrees _ _ (fun k a => AISProfile.referencePresent c p k a) n s xs

theorem ctrRun (c : CTRProfile.Cipher) (n : Nat) (s : CTRProfile.State)
    (xs : Word CTRProfile.Word n) :
    referenceRun (fun k a => CTRProfile.nistGenerate c k (some (CTRProfile.physical a))) n s xs =
      ((causalPermutation (ctr c) n s).enc xs) := by
  apply runAgrees
  intro k a
  apply Prod.ext
  · exact CTRProfile.physical_output c k a
  · rfl

theorem aisITS (c : AISProfile.Primitives) (p : AISProfile.Block) (n : Nat)
    [DecidableEq (Word AISProfile.Block n)] (w : Weights W) (alphabet : Alphabet (Word AISProfile.Block n))
    (views : List E) (start : E → AISProfile.Key) (law : E → Word AISProfile.Block n → W) :
    let out := pushRows (fun e => causalPermutation (ais c p) n (start e)) law
    tvUniform w alphabet views out = tvUniform w alphabet views law ∧
    pGuess w alphabet views out = pGuess w alphabet views law :=
  sequence_its (ais c p) n w alphabet views start law

theorem ctrITS (c : CTRProfile.Cipher) (n : Nat)
    [DecidableEq (Word CTRProfile.Word n)] (w : Weights W) (alphabet : Alphabet (Word CTRProfile.Word n))
    (views : List E) (start : E → CTRProfile.State) (law : E → Word CTRProfile.Word n → W) :
    let out := pushRows (fun e => causalPermutation (ctr c) n (start e)) law
    tvUniform w alphabet views out = tvUniform w alphabet views law ∧
    pGuess w alphabet views out = pGuess w alphabet views law :=
  sequence_its (ctr c) n w alphabet views start law

/-- Quantum side information and a classical view that includes the initial
    state. Both concrete machines above can instantiate this statement. -/
def quantumPreserved (machine : Machine S B) (n : Nat) [DecidableEq (Word B n)]
    (m : PTGCQ.Model O R) (alphabet : Alphabet (Word B n)) (tags : List C)
    (joint : PTGCQ.DirectSum m alphabet tags) (rho : C → Word B n → O)
    (initial : C → S) (supremum : (R → Prop) → R) : Prop :=
  let out := pushRows (fun c => causalPermutation machine n (initial c)) rho
  PTGCQ.distance m alphabet tags joint out = PTGCQ.distance m alphabet tags joint rho ∧
  supremum (PTGCQ.attainable m alphabet tags out) = supremum (PTGCQ.attainable m alphabet tags rho)

theorem aisCQ (cipher : AISProfile.Primitives) (p : AISProfile.Block) (n : Nat)
    [DecidableEq (Word AISProfile.Block n)] (m : PTGCQ.Model O R)
    (alphabet : Alphabet (Word AISProfile.Block n)) (tags : List C)
    (joint : PTGCQ.DirectSum m alphabet tags) (rho : C → Word AISProfile.Block n → O)
    (initial : C → AISProfile.Key) (supremum : (R → Prop) → R) :
    quantumPreserved (ais cipher p) n m alphabet tags joint rho initial supremum :=
  PTGCQ.sequence_cq _ _ _ _ _ _ _ _ _

theorem ctrCQ (cipher : CTRProfile.Cipher) (n : Nat)
    [DecidableEq (Word CTRProfile.Word n)] (m : PTGCQ.Model O R)
    (alphabet : Alphabet (Word CTRProfile.Word n)) (tags : List C)
    (joint : PTGCQ.DirectSum m alphabet tags) (rho : C → Word CTRProfile.Word n → O)
    (initial : C → CTRProfile.State) (supremum : (R → Prop) → R) :
    quantumPreserved (ctr cipher) n m alphabet tags joint rho initial supremum :=
  PTGCQ.sequence_cq _ _ _ _ _ _ _ _ _

/-- A public call schedule and fixed reseed material can be folded into a
    causal state update. refresh is identity on ordinary calls. -/
def scheduled (m : Machine S B) (refresh : Nat → S → S) : Machine (Nat × S) B where
  emit t := m.emit (refresh t.1 t.2)
  next t a := (t.1 + 1, m.next (refresh t.1 t.2) a)

theorem scheduledRun (m : Machine S B) (refresh : Nat → S → S)
    (n i : Nat) (s : S) (xs : Word B n) :
    decode (scheduled m refresh) n (i,s) (encode (scheduled m refresh) n (i,s) xs) = xs :=
  decode_encode _ _ _ _

end PTG.Composition

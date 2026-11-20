import CTRProfile
set_option exponentiation.threshold 1024
set_option maxRecDepth 8192

/-! Distinct observable behaviors for the physical additional-input profile.
    Probability calculations in the independent ideal-cipher model use finite
    counts. No security or independence property of concrete AES is postulated
    in the proofs. -/
namespace EffectiveCTR

open CTRProfile

def point (offset input : Word) : Word := inc (offset ^^^ input)

theorem pointInjective (offset a b : Word) (h : point offset a = point offset b) : a = b := by
  have back := congrArg (fun x => offset ^^^ dec x) h
  simpa [point, inv_inc, undo_word_mask] using back

def inputs : List Word := [0, 1, 2, 3, 4]

theorem inputsDistinct : inputs.Nodup := by decide

def signature (c : Cipher) (s : State) : List Word :=
  inputs.map (fun a => (nistGenerate c s (some (physical a))).1)

theorem signatureUnderDerivedKey (c : Cipher) (s : State) :
    signature c s =
      inputs.map (fun a => c.encrypt (rawTriple c s).key (point (rawTriple c s).counter a)) := by
  simp [signature, physical_output, encode, point]

/-- Separation using first responses to admissible inputs implies separation
    of full transition systems, which would have to agree on those responses. -/
theorem separateClasses (c : Cipher) (represent : Fin (2^246) → State)
    (distinct : ∀ i j, signature c (represent i) = signature c (represent j) → i = j)
    (i j : Fin (2^246))
    (same : ∀ a, (nistGenerate c (represent i) (some (physical a))).1 =
                 (nistGenerate c (represent j) (some (physical a))).1) : i = j := by
  apply distinct
  exact List.map_congr_left (fun x _ => same x)

/-- Count the paths along which no fresh admissible key has yet been found.
    'children' lists only failing continuations, possibly depending on the
    whole preceding history. The statement does not assume independent
    selections within or between completed groups. -/
def failingPaths (children : History → List History) : Nat → History → Nat
  | 0, _ => 1
  | n+1, h => ((children h).map (failingPaths children n)).sum

private theorem sumAtMost (xs : List α) (f : α → Nat) (b : Nat) (bound : ∀ x, f x ≤ b) :
    (xs.map f).sum ≤ xs.length * b := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    rw [List.map_cons, List.sum_cons, List.length_cons, Nat.succ_mul, Nat.add_comm _ b]
    exact Nat.add_le_add (bound x) ih

theorem groupFailureCount (children : History → List History) (bad : Nat)
    (bound : ∀ h, (children h).length ≤ bad) (n : Nat) (h : History) :
    failingPaths children n h ≤ bad^n := by
  induction n generalizing h with
  | zero => simp [failingPaths]
  | succ n ih =>
    calc
      _ ≤ (children h).length * bad^n := sumAtMost _ _ _ ih
      _ ≤ bad * bad^n := Nat.mul_le_mul_right _ (bound h)
      _ = _ := by rw [Nat.pow_succ, Nat.mul_comm]

def M : Nat := 2^128
def groups : Nat := 2^246
def orderedPairs : Nat := M*(M-1)
def permutations5 : Nat := orderedPairs*(M-2)*(M-3)*(M-4)

/-- All low old keys partition into this many disjoint groups. -/
theorem partitionSize : groups * 512 = 2^255 := by decide

/-- Half of all ordered pairs have a high first word. Excluding at most one
    previously selected high derived key per group leaves at most 9H/16 bad
    pairs in the H ordered pairs. -/
theorem halfHighCount : (M / 2)*(M-1)*2 = orderedPairs := by decide

theorem badFraction : 16 * (orderedPairs/2 + groups) ≤ 9 * orderedPairs := by decide

theorem scaledGroupFailure (children : History → List History) (h : History)
    (bound : ∀ u, (children u).length ≤ orderedPairs/2 + groups) :
    16^512 * failingPaths children 512 h ≤ 9^512 * orderedPairs^512 := by
  have first := Nat.mul_le_mul_left (16^512) (groupFailureCount children _ bound 512 h)
  have second := Nat.pow_le_pow_left badFraction 512
  rw [Nat.mul_pow, Nat.mul_pow] at second
  exact Nat.le_trans first second

def permutationCount : Nat → Nat
  | 0 => 1
  | n+1 => (n+1) * permutationCount n

/-- Each permutation with five prescribed distinct domain/image pairs has
    exactly n! completions among (n+5)! permutations on the whole alphabet. -/
theorem fiveFactors (n : Nat) :
    permutationCount (n+5) =
      (n+5)*(n+4)*(n+3)*(n+2)*(n+1)*permutationCount n := by
  simp [permutationCount, Nat.mul_assoc]

/-- A union of group failures and signature collisions is below 2^-148.
    The inequality is exact integer arithmetic on the common denominator:
    2^148 · [groups·9^512/16^512 + groups(groups-1)/(2·permutations5)] < 1. -/
theorem totalFailure :
    2^148 * (groups * 9^512 * (2*permutations5) +
       groups*(groups-1)*16^512) < 16^512 * (2*permutations5) := by decide

end EffectiveCTR

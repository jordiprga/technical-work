import HealthGate

namespace CryptoSure

/- Representación finita: C+1 valores, de 0 a C incluidos. -/
structure SatState (cutoff : Nat) where
  last : Option Bool
  run : Fin (cutoff + 1)
  failed : Bool
  deriving Repr, DecidableEq

def saturate (cutoff : Nat) (s : RCTState) : SatState cutoff :=
  ⟨s.last, ⟨min cutoff s.run, Nat.lt_succ_of_le (Nat.min_le_left _ _)⟩, s.failed⟩

def satStep (cutoff : Nat) (s : SatState cutoff) (x : Bool) : SatState cutoff :=
  let count := if s.last = some x then s.run.val + 1 else 1
  ⟨some x, ⟨min cutoff count, Nat.lt_succ_of_le (Nat.min_le_left _ _)⟩,
    s.failed || decide (cutoff ≤ count)⟩

theorem min_increment (c n : Nat) : min c (min c n + 1) = min c (n + 1) := by
  omega

theorem threshold_min_increment (c n : Nat) :
    c ≤ min c n + 1 ↔ c ≤ n + 1 := by
  omega

theorem saturating_step_refines (c : Nat) (s : RCTState) (x : Bool) :
    satStep c (saturate c s) x = saturate c (step c s x) := by
  by_cases h : s.last = some x
  · simp only [satStep, saturate, step, h, if_true]
    simp only [min_increment, threshold_min_increment]
  · simp [satStep, saturate, step, h]

def satAdvance (cutoff : Nat) (s : SatState cutoff) : List Bool → SatState cutoff
  | [] => s
  | x :: xs => satAdvance cutoff (satStep cutoff s x) xs

theorem saturating_trace_refines (c : Nat) (s : RCTState) (xs : List Bool) :
    satAdvance c (saturate c s) xs = saturate c (advance c s xs) := by
  induction xs generalizing s with
  | nil => rfl
  | cons x xs ih =>
      simp only [satAdvance, advance, saturating_step_refines]
      exact ih (step c s x)

theorem finite_counter_bound (c : Nat) (s : SatState c) : s.run.val ≤ c := by
  exact Nat.le_of_lt_succ s.run.isLt

/- El incremento sólo se evalúa si el contador todavía es menor que C. -/
def guardedIncrement (c n : Nat) : Nat := if n < c then n + 1 else c

theorem guarded_increment_eq (c n : Nat) :
    guardedIncrement c n = min c (n + 1) := by
  unfold guardedIncrement
  split <;> omega

theorem guarded_increment_fits (width c n : Nat)
    (hc : c < 2 ^ width) (hguard : n < c) : n + 1 < 2 ^ width := by
  omega

def guardedStep (c : Nat) (s : SatState c) (x : Bool) : SatState c :=
  let count := if s.last = some x then guardedIncrement c s.run.val else min c 1
  have hb : count ≤ c := by
    dsimp [count]
    split
    · rw [guarded_increment_eq]
      exact Nat.min_le_left _ _
    · exact Nat.min_le_left _ _
  ⟨some x, ⟨count, Nat.lt_succ_of_le hb⟩,
    s.failed || decide (c ≤ count)⟩

theorem threshold_min (c n : Nat) : c ≤ min c n ↔ c ≤ n := by omega

theorem guarded_step_equivalent (c : Nat) (s : SatState c) (x : Bool) :
    guardedStep c s x = satStep c s x := by
  by_cases h : s.last = some x
  · simp [guardedStep, satStep, h, guarded_increment_eq, threshold_min]
  · simp [guardedStep, satStep, h, threshold_min]

theorem saturated_detection (c : Nat) (x : Bool) (n : Nat)
    (hn : 0 < n) (hc : c ≤ n) :
    (satAdvance c (saturate c initial) (List.replicate n x)).failed = true := by
  rw [saturating_trace_refines]
  exact identical_samples_detected c x n hn hc

#print axioms saturating_step_refines
#print axioms saturating_trace_refines
#print axioms finite_counter_bound
#print axioms guarded_increment_fits
#print axioms guarded_step_equivalent
#print axioms saturated_detection

end CryptoSure

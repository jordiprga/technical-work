import Std

set_option exponentiation.threshold 512

namespace PTG.SourceBudget

/-- For q calls, the square of q * 2^((m-k)/2) / 2 is at most 2^(-2t).
    Cross multiplication leaves precisely this natural-number inequality. -/
def meetsLhlBudget (q m k t : Nat) : Prop :=
  q ^ 2 * 2 ^ (m + 2 * t) ≤ 4 * 2 ^ k

instance (q m k t : Nat) : Decidable (meetsLhlBudget q m k t) :=
  inferInstanceAs (Decidable (_ ≤ _))

theorem exactThreshold (k : Nat) :
    meetsLhlBudget (2^32) 128 k 64 ↔ 318 ≤ k := by
  change 2^320 ≤ 4 * 2^k ↔ _
  rw [show 4 * 2^k = 2^(k+2) by rw [Nat.pow_add]; exact Nat.mul_comm _ _]
  rw [Nat.pow_le_pow_iff_right (by decide : 1 < 2)]
  omega

theorem idealMargin : meetsLhlBudget (2^32) 128 324 67 := by decide

/-- Common denominator 2^99: LHL costs 1 unit per call, the replacement
    of a selector at distance 2^-98 costs 4 units per call. -/
theorem imperfectSelectorBudget :
    (2^32 : Nat) * (1 + 2 * 2) * 2^64 ≤ 2^99 := by decide

abbrev Raw := Bool × Bool × Bool

def allRaw : List Raw := [false, true].flatMap fun a =>
  [false, true].flatMap fun b => [false, true].map fun c => (a,b,c)

def toeplitzRow (u r : Raw) : Bool :=
  ((u.1 && r.1) ^^ (u.2.1 && r.2.1)) ^^ (u.2.2 && r.2.2)

def kernelRows (u : Raw) : List Raw := allRaw.filter fun r => !(toeplitzRow u r)

theorem allRowsAreUnique : allRaw.Nodup := by decide
theorem allRowsCovered (r : Raw) : r ∈ allRaw := by
  rcases r with ⟨a,b,c⟩
  cases a <;> cases b <;> cases c <;> decide

theorem kernelSize (u : Raw) :
    (kernelRows u).length = if u = (false,false,false) then 8 else 4 := by
  rcases u with ⟨a,b,c⟩
  cases a <;> cases b <;> cases c <;> decide

theorem dependentSourceConstant {u r : Raw} (hr : r ∈ kernelRows u) :
    toeplitzRow u r = false := by
  have hc := (List.mem_filter.mp hr).2
  simpa using hc

/-- The flat distribution on a 126-dimensional subspace of 128-bit words has 126 uniform free bits.
    PTG.2's numerical rate 0.98 alone permits this uncertainty. -/
theorem flatSourceRate : 98 * 128 ≤ 100 * 126 := by decide

/-- A uniform reference gives mass 3/4 to the complement of this support. -/
theorem missingMass : (2^128 - 2^126 : Nat) * 4 = 3 * 2^128 := by decide

end PTG.SourceBudget

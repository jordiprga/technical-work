import HealthGate

namespace CryptoSure

/- Política: descartar todas las muestras de startup; no se modela reset. -/
structure StartupState where
  remaining : Nat
  rct : RCTState
  deriving Repr, DecidableEq

def startupStep (c : Nat) (s : StartupState) (x : Bool) : StartupState :=
  ⟨s.remaining - 1, step c s.rct x⟩

def startupEmit (c : Nat) (s : StartupState) (x : Bool) : Option Bool :=
  if s.remaining = 0 then emit c s.rct x else none

def startupAdvance (c : Nat) (s : StartupState) : List Bool → StartupState
  | [] => s
  | x :: xs => startupAdvance c (startupStep c s x) xs

def startupOutputs (c : Nat) (s : StartupState) : List Bool → List (Option Bool)
  | [] => []
  | x :: xs => startupEmit c s x :: startupOutputs c (startupStep c s x) xs

theorem startup_count_exact (c : Nat) (s : StartupState) (xs : List Bool) :
    (startupAdvance c s xs).remaining = s.remaining - xs.length := by
  induction xs generalizing s with
  | nil => rfl
  | cons x xs ih =>
      simp only [startupAdvance, ih, startupStep, List.length_cons]
      omega

theorem startup_no_release (c : Nat) (s : StartupState) (xs : List Bool)
    (h : xs.length ≤ s.remaining) :
    startupOutputs c s xs = List.replicate xs.length none := by
  induction xs generalizing s with
  | nil => rfl
  | cons x xs ih =>
      have hp : s.remaining ≠ 0 := by simp only [List.length_cons] at h; omega
      have hs : xs.length ≤ (startupStep c s x).remaining := by
        simp only [startupStep, List.length_cons] at *
        omega
      simp only [startupOutputs, startupEmit, hp, if_false]
      rw [ih (startupStep c s x) hs]
      simp [List.replicate_succ]

theorem startup_preserves_health (c : Nat) (s : StartupState) (xs : List Bool) :
    (startupAdvance c s xs).rct = advance c s.rct xs := by
  induction xs generalizing s with
  | nil => rfl
  | cons x xs ih => exact ih (startupStep c s x)

theorem startup_fault_no_release (c : Nat) (s : StartupState) (xs : List Bool)
    (h : s.rct.failed = true) :
    startupOutputs c s xs = List.replicate xs.length none := by
  induction xs generalizing s with
  | nil => rfl
  | cons x xs ih =>
      have hs := failure_sticky_step c s.rct x h
      have hem : emit c s.rct x = none := by simp [emit, hs]
      simp only [startupOutputs, startupEmit, hem]
      rw [ih (startupStep c s x) hs]
      simp [List.replicate_succ]

theorem startup_accept_iff (c : Nat) (s : StartupState) (x : Bool) :
    startupEmit c s x = some x ↔
      s.remaining = 0 ∧ (step c s.rct x).failed = false := by
  by_cases hready : s.remaining = 0
  · cases hf : (step c s.rct x).failed <;> simp [startupEmit, emit, hready, hf]
  · simp [startupEmit, hready]

theorem startup_eventually_ready (c : Nat) (s : StartupState) (xs : List Bool)
    (h : s.remaining ≤ xs.length) : (startupAdvance c s xs).remaining = 0 := by
  rw [startup_count_exact]
  omega

theorem startup_conditional_progress (c : Nat) (s : StartupState)
    (xs : List Bool) (x : Bool) (hcount : s.remaining ≤ xs.length)
    (hhealth : (step c (advance c s.rct xs) x).failed = false) :
    startupEmit c (startupAdvance c s xs) x = some x := by
  apply (startup_accept_iff c (startupAdvance c s xs) x).mpr
  constructor
  · exact startup_eventually_ready c s xs hcount
  · rw [startup_preserves_health]
    exact hhealth

/- La muestra 1024 también se descarta; la 1025 puede salir si el RCT no falla. -/
example : startupEmit 4 ⟨1, ⟨some false, 1, false⟩⟩ true = none := by decide
example : startupEmit 4 ⟨0, ⟨some false, 1, false⟩⟩ true = some true := by decide

#print axioms startup_count_exact
#print axioms startup_no_release
#print axioms startup_preserves_health
#print axioms startup_fault_no_release
#print axioms startup_accept_iff
#print axioms startup_eventually_ready
#print axioms startup_conditional_progress

end CryptoSure

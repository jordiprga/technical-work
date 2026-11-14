import Std

/-
  Modelo original y genérico. No es una implementación certificada de SP 800-90B.
  Nat no modela overflow. No hay reset: el fallo es persistente durante una época.
  El primer símbolo cuenta como 1. El símbolo que dispara el fallo no se entrega.
-/
namespace CryptoSure

structure RCTState where
  last : Option Bool
  run : Nat
  failed : Bool
  deriving Repr, DecidableEq

def initial : RCTState := ⟨none, 0, false⟩

def step (cutoff : Nat) (s : RCTState) (x : Bool) : RCTState :=
  let count := if s.last = some x then s.run + 1 else 1
  ⟨some x, count, s.failed || decide (cutoff ≤ count)⟩

def advance (cutoff : Nat) (s : RCTState) : List Bool → RCTState
  | [] => s
  | x :: xs => advance cutoff (step cutoff s x) xs

def emit (cutoff : Nat) (s : RCTState) (x : Bool) : Option Bool :=
  if (step cutoff s x).failed then none else some x

def outputs (cutoff : Nat) (s : RCTState) : List Bool → List (Option Bool)
  | [] => []
  | x :: xs => emit cutoff s x :: outputs cutoff (step cutoff s x) xs

theorem step_last (cutoff : Nat) (s : RCTState) (x : Bool) :
    (step cutoff s x).last = some x := by
  rfl

theorem failure_sticky_step (cutoff : Nat) (s : RCTState) (x : Bool)
    (h : s.failed = true) : (step cutoff s x).failed = true := by
  simp [step, h]

theorem failure_sticky_trace (cutoff : Nat) (s : RCTState) (xs : List Bool)
    (h : s.failed = true) : (advance cutoff s xs).failed = true := by
  induction xs generalizing s with
  | nil => exact h
  | cons x xs ih =>
      exact ih (step cutoff s x) (failure_sticky_step cutoff s x h)

theorem no_output_after_failure (cutoff : Nat) (s : RCTState) (xs : List Bool)
    (h : s.failed = true) :
    outputs cutoff s xs = List.replicate xs.length none := by
  induction xs generalizing s with
  | nil => rfl
  | cons x xs ih =>
      have hs := failure_sticky_step cutoff s x h
      simp [outputs, emit, hs, ih (step cutoff s x) hs, List.replicate_succ]

/- Procesar bloques conservando estado equivale a procesar la concatenación. -/
theorem block_composition (cutoff : Nat) (s : RCTState) (a b : List Bool) :
    advance cutoff s (a ++ b) = advance cutoff (advance cutoff s a) b := by
  induction a generalizing s with
  | nil => rfl
  | cons x xs ih => exact ih (step cutoff s x)

theorem outputs_composition (cutoff : Nat) (s : RCTState) (a b : List Bool) :
    outputs cutoff s (a ++ b) =
      outputs cutoff s a ++ outputs cutoff (advance cutoff s a) b := by
  induction a generalizing s with
  | nil => rfl
  | cons x xs ih =>
      simp only [List.cons_append, outputs, advance]
      rw [ih (step cutoff s x)]

theorem repeated_run (cutoff : Nat) (s : RCTState) (x : Bool) (n : Nat)
    (h : s.last = some x) :
    (advance cutoff s (List.replicate n x)).run = s.run + n := by
  induction n generalizing s with
  | zero => simp [advance]
  | succ n ih =>
      simp only [List.replicate_succ, advance]
      rw [ih (step cutoff s x) (step_last cutoff s x)]
      simp [step, h, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]

/- Invariante: un contador que ya alcanza el umbral implica fallo latched. -/
def Safe (cutoff : Nat) (s : RCTState) : Prop := cutoff ≤ s.run → s.failed = true

theorem step_safe (cutoff : Nat) (s : RCTState) (x : Bool) :
    Safe cutoff (step cutoff s x) := by
  unfold Safe step
  dsimp
  intro h
  simp [h]

theorem safe_trace (cutoff : Nat) (s : RCTState) (xs : List Bool)
    (h : Safe cutoff s) : Safe cutoff (advance cutoff s xs) := by
  induction xs generalizing s with
  | nil => exact h
  | cons x xs ih => exact ih (step cutoff s x) (step_safe cutoff s x)

theorem identical_samples_detected (cutoff : Nat) (x : Bool) (n : Nat)
    (hn : 0 < n) (hc : cutoff ≤ n) :
    (advance cutoff initial (List.replicate n x)).failed = true := by
  cases n with
  | zero => omega
  | succ n =>
      simp only [List.replicate_succ, advance]
      have hr := repeated_run cutoff (step cutoff initial x) x n
        (step_last cutoff initial x)
      have hs := safe_trace cutoff (step cutoff initial x) (List.replicate n x)
        (step_safe cutoff initial x)
      apply hs
      rw [hr]
      simpa [step, initial, Nat.add_comm] using hc

/- Después de C símbolos iguales, cualquier sufijo carece de salida. -/
theorem stuck_source_shutdown (cutoff : Nat) (x : Bool) (tail : List Bool)
    (hc : 0 < cutoff) :
    outputs cutoff (advance cutoff initial (List.replicate cutoff x)) tail =
      List.replicate tail.length none := by
  exact no_output_after_failure cutoff _ tail
    (identical_samples_detected cutoff x cutoff hc (Nat.le_refl cutoff))

/- El latch no inventa alarmas: es OR exacto del estado inicial y cruces de umbral. -/
def crossings (cutoff : Nat) (s : RCTState) : List Bool → Bool
  | [] => false
  | x :: xs => decide (cutoff ≤ (step cutoff s x).run) ||
      crossings cutoff (step cutoff s x) xs

theorem failure_exact (cutoff : Nat) (s : RCTState) (xs : List Bool) :
    (advance cutoff s xs).failed = (s.failed || crossings cutoff s xs) := by
  induction xs generalizing s with
  | nil => simp [advance, crossings]
  | cons x xs ih =>
      simp only [advance, crossings, ih]
      simp [step, Bool.or_assoc]

theorem no_false_alarm (cutoff : Nat) (s : RCTState) (xs : List Bool)
    (hi : s.failed = false) (hn : crossings cutoff s xs = false) :
    (advance cutoff s xs).failed = false := by
  rw [failure_exact, hi, hn]
  rfl

theorem threshold_sample_suppressed (cutoff : Nat) (s : RCTState) (x : Bool)
    (h : cutoff ≤ (step cutoff s x).run) : emit cutoff s x = none := by
  have hf := step_safe cutoff s x h
  simp [emit, hf]

/- Contraejemplo certificado por reducción kernel: reset en frontera de bloque. -/
example : (advance 4 initial [true, true, true, true]).failed = true := by decide
example : (advance 4 initial [true, true]).failed = false := by decide

/- Contraejemplo: un gate que mira el estado anterior libera el símbolo de fallo. -/
def badEmit (_cutoff : Nat) (s : RCTState) (x : Bool) : Option Bool :=
  if s.failed then none else some x

example : emit 4 ⟨some true, 3, false⟩ true = none := by decide
example : badEmit 4 ⟨some true, 3, false⟩ true = some true := by decide

#print axioms failure_sticky_trace
#print axioms no_output_after_failure
#print axioms block_composition
#print axioms outputs_composition
#print axioms repeated_run
#print axioms identical_samples_detected
#print axioms stuck_source_shutdown
#print axioms failure_exact
#print axioms no_false_alarm
#print axioms threshold_sample_suppressed

end CryptoSure

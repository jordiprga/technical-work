import HealthGate

namespace CryptoSure

/- Referencia independiente: historial en orden más reciente primero.
   Cuenta por inspección de lista; no usa el contador del autómata.
-/
def leading (x : Bool) : List Bool → Nat
  | [] => 0
  | y :: ys => if x = y then leading x ys + 1 else 0

def historyRun : List Bool → Nat
  | [] => 0
  | x :: xs => leading x xs + 1

def historyAlarm (c : Nat) : List Bool → Bool
  | [] => false
  | x :: xs => decide (c ≤ historyRun (x :: xs)) || historyAlarm c xs

def Represents (c : Nat) (s : RCTState) (history : List Bool) : Prop :=
  s.last = history.head? ∧ s.run = historyRun history ∧ s.failed = historyAlarm c history

theorem history_run_step (x : Bool) (history : List Bool) :
    historyRun (x :: history) =
      if history.head? = some x then historyRun history + 1 else 1 := by
  cases history with
  | nil => simp [historyRun, leading]
  | cons y ys =>
      by_cases h : x = y
      · subst y
        simp [historyRun, leading]
      · have hy : y ≠ x := Ne.symm h
        simp [historyRun, leading, h, hy]

theorem initial_represents (c : Nat) : Represents c initial [] := by
  simp [Represents, initial, historyRun, historyAlarm]

theorem step_represents (c : Nat) (s : RCTState) (x : Bool) (history : List Bool)
    (h : Represents c s history) : Represents c (step c s x) (x :: history) := by
  rcases h with ⟨hl, hr, hf⟩
  have count_eq : (step c s x).run = historyRun (x :: history) := by
    rw [history_run_step]
    simp [step, hl, hr]
  refine ⟨rfl, count_eq, ?_⟩
  change (s.failed || decide (c ≤ (step c s x).run)) = historyAlarm c (x :: history)
  rw [count_eq, hf]
  simp [historyAlarm, Bool.or_comm]

theorem trace_represents (c : Nat) (s : RCTState) (xs history : List Bool)
    (h : Represents c s history) :
    Represents c (advance c s xs) (xs.reverse ++ history) := by
  induction xs generalizing s history with
  | nil => simpa [advance] using h
  | cons x xs ih =>
      have ht := ih (step c s x) (x :: history) (step_represents c s x history h)
      simpa [advance, List.reverse_cons, List.append_assoc] using ht

theorem detector_exact_from_history (c : Nat) (xs : List Bool) :
    (advance c initial xs).failed = historyAlarm c xs.reverse := by
  have h := trace_represents c initial xs [] (initial_represents c)
  simpa [Represents] using h.2.2

theorem run_exact_from_history (c : Nat) (xs : List Bool) :
    (advance c initial xs).run = historyRun xs.reverse := by
  have h := trace_represents c initial xs [] (initial_represents c)
  simpa [Represents] using h.2.1

#print axioms step_represents
#print axioms trace_represents
#print axioms detector_exact_from_history
#print axioms run_exact_from_history

end CryptoSure

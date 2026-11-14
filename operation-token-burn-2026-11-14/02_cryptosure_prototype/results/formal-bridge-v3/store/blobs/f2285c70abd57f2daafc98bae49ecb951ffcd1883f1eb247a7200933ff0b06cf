import Std

namespace CryptoSure

/- Valores enteros: la identidad vale también para bits, sin IID ni probabilidad. -/
def windowSum (samples : Nat → Int) : Nat → Nat → Int
  | 0, _ => 0
  | width + 1, start => windowSum samples width start + samples (start + width)

theorem rolling_difference (samples : Nat → Int) (width start : Nat) :
    windowSum samples width (start + 1) - windowSum samples width start =
      samples (start + width) - samples start := by
  induction width with
  | zero => simp [windowSum]
  | succ width ih =>
      simp only [windowSum]
      have hindex : start + 1 + width = start + (width + 1) := by omega
      rw [hindex]
      omega

theorem reconstruct_next (samples : Nat → Int) (width start : Nat) :
    samples (start + width) =
      windowSum samples width (start + 1) - windowSum samples width start + samples start := by
  have h := rolling_difference samples width start
  omega

/- Inyectividad: prefijo de W y transcript completo fijan toda la secuencia. -/
theorem rolling_transcript_injective (a b : Nat → Int) (width : Nat)
    (hw : 0 < width)
    (hprefix : ∀ i, i < width → a i = b i)
    (counts : ∀ start, windowSum a width start = windowSum b width start) :
    ∀ i, a i = b i := by
  intro i
  induction i using Nat.strongRecOn with
  | ind i ih =>
      by_cases hsmall : i < width
      · exact hprefix i hsmall
      · have hprevious : i - width < i := by omega
        have hprev := ih (i - width) hprevious
        have ha := reconstruct_next a width (i - width)
        have hb := reconstruct_next b width (i - width)
        have hindex : i - width + width = i := by omega
        rw [hindex] at ha hb
        rw [counts, counts, hprev] at ha
        exact ha.trans hb.symm

/- Versión finita: sólo requiere ventanas completamente contenidas en n muestras. -/
theorem finite_rolling_transcript_injective (a b : Nat → Int) (width n : Nat)
    (hw : 0 < width)
    (hprefix : ∀ i, i < width → i < n → a i = b i)
    (counts : ∀ start, start + width ≤ n →
      windowSum a width start = windowSum b width start) :
    ∀ i, i < n → a i = b i := by
  intro i
  induction i using Nat.strongRecOn with
  | ind i ih =>
      intro hin
      by_cases hsmall : i < width
      · exact hprefix i hsmall hin
      · have hprevious : i - width < i := by omega
        have hprev := ih (i - width) hprevious (by omega)
        have ha := reconstruct_next a width (i - width)
        have hb := reconstruct_next b width (i - width)
        have hindex : i - width + width = i := by omega
        rw [hindex] at ha hb
        rw [counts (i - width + 1) (by omega), counts (i - width) (by omega), hprev] at ha
        exact ha.trans hb.symm

/- Ventana 1: no prefijo secreto hace falta; cada conteo ES la muestra. -/
theorem width_one_reveals (samples : Nat → Int) (start : Nat) :
    windowSum samples 1 start = samples start := by simp [windowSum]

#print axioms rolling_difference
#print axioms reconstruct_next
#print axioms rolling_transcript_injective
#print axioms finite_rolling_transcript_injective
#print axioms width_one_reveals

end CryptoSure

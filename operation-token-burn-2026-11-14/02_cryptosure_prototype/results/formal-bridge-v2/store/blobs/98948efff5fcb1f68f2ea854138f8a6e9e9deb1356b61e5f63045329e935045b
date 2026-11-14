import Std

namespace CryptoSure

/- Sin estructura probabilística: soporte dentro de una fibra implica salida constante. -/
theorem fiber_constant {X Y : Type} (f : X → Y) (support : X → Prop) (y : Y)
    (hfiber : ∀ x, support x → f x = y) (x : X) (hx : support x) :
    f x = y := hfiber x hx

/- Elección adaptada a semilla: cualquier selector de una fibra rompe extracción. -/
theorem seed_adapted_constant {S X Y : Type}
    (extract : S → X → Y) (choose : S → X) (y : Y)
    (hfiber : ∀ s, extract s (choose s) = y) :
    ∀ s, extract s (choose s) = y := hfiber

/- Repetir entrada y semilla repite salida para TODO extractor determinista. -/
theorem repeated_input_repeated_output {S X Y : Type}
    (extract : S → X → Y) (s : S) (x1 x2 : X) (h : x2 = x1) :
    extract s x2 = extract s x1 := by rw [h]

/- Una familia lineal minúscula: f_s(x1,x2)=s1*x1 XOR s2*x2.
   Para cada semilla, la entrada (s2,s1) pertenece al núcleo.
   No afirma nada sobre entropía del selector: aísla la dependencia prohibida.
-/
def hash2 (s x : Bool × Bool) : Bool :=
  Bool.xor (s.1 && x.1) (s.2 && x.2)

def kernelChoice (s : Bool × Bool) : Bool × Bool := (s.2, s.1)

theorem linear_seed_adapted_zero (s : Bool × Bool) :
    hash2 s (kernelChoice s) = false := by
  rcases s with ⟨a, b⟩
  cases a <;> cases b <;> decide

/- Con semilla fija (1,0), el bit libre x2 no cambia la salida. -/
theorem fixed_seed_one_bit_lost (b : Bool) :
    hash2 (true, false) (false, b) = false := by
  cases b <;> decide

#print axioms repeated_input_repeated_output
#print axioms linear_seed_adapted_zero
#print axioms fixed_seed_one_bit_lost

end CryptoSure

import Std

/-!
Finite classical information-theoretic preservation. No independence or
distribution assumption is made about the sequence. Weight arithmetic is a
parameter so the reindexing theorem works for real masses as well as exact
counts. It never enumerates the 128-bit alphabet during proof checking.
-/
namespace PTGITS

structure BlockPerm (B : Type) where
  enc : B → B
  dec : B → B
  dec_enc : ∀ x, dec (enc x) = x
  enc_dec : ∀ y, enc (dec y) = y

def BlockPerm.inverse (f : BlockPerm B) : BlockPerm B :=
  ⟨f.dec, f.enc, f.enc_dec, f.dec_enc⟩

structure Machine (S B : Type) where
  emit : S → BlockPerm B
  next : S → B → S

/-- An exact-length transcript; no length information can leak. -/
def Word (B : Type) : Nat → Type
  | 0 => Unit
  | n + 1 => B × Word B n

def encode (m : Machine S B) : (n : Nat) → S → Word B n → Word B n
  | 0, _, _ => ()
  | n + 1, s, (a, tail) => ((m.emit s).enc a, encode m n (m.next s a) tail)

def decode (m : Machine S B) : (n : Nat) → S → Word B n → Word B n
  | 0, _, _ => ()
  | n + 1, s, (y, tail) =>
    let a := (m.emit s).dec y
    (a, decode m n (m.next s a) tail)

theorem decode_encode (m : Machine S B) (n : Nat) (s : S) (xs : Word B n) :
    decode m n s (encode m n s xs) = xs := by
  induction n generalizing s with
  | zero => cases xs; rfl
  | succ n ih =>
    rcases xs with ⟨a, tail⟩
    simp only [encode, decode, BlockPerm.dec_enc, ih]

theorem encode_decode (m : Machine S B) (n : Nat) (s : S) (ys : Word B n) :
    encode m n s (decode m n s ys) = ys := by
  induction n generalizing s with
  | zero => cases ys; rfl
  | succ n ih =>
    rcases ys with ⟨y, tail⟩
    simp only [encode, decode, BlockPerm.enc_dec, ih]

def causalPermutation (m : Machine S B) (n : Nat) (s : S) : BlockPerm (Word B n) :=
  ⟨encode m n s, decode m n s, decode_encode m n s, encode_decode m n s⟩

/-- A finite alphabet enumerated exactly once, in any order. -/
structure Alphabet (B : Type) [DecidableEq B] where
  cells : List B
  count_once : ∀ b, cells.count b = 1

theorem count_reindex [DecidableEq B] (f : BlockPerm B) (cells : List B) (b : B) :
    (cells.map f.enc).count b = cells.count (f.dec b) := by
  induction cells with
  | nil => simp
  | cons a tail ih =>
    by_cases h : a = f.dec b
    · subst a
      simp [f.enc_dec, ih]
    · have h' : f.enc a ≠ b := by
        intro eq
        apply h
        rw [← eq, f.dec_enc]
      simp [List.count_cons_of_ne h, List.count_cons_of_ne h', ih]

theorem reindex_list [DecidableEq B] (alph : Alphabet B) (f : BlockPerm B) :
    (alph.cells.map f.enc).Perm alph.cells := by
  apply List.perm_iff_count.mpr
  intro b
  rw [count_reindex, alph.count_once, alph.count_once]

/-- A finite sum or maximum, including a neutral starting value. -/
def reduceCells (combine : W → W → W) (start : W) (cells : List B) (mass : B → W) : W :=
  (cells.map mass).foldr combine start

theorem reduce_reindex [DecidableEq B] (alph : Alphabet B) (f : BlockPerm B)
    (combine : W → W → W) (comm : ∀ a b z, combine b (combine a z) = combine a (combine b z))
    (start : W) (mass : B → W) :
    reduceCells combine start alph.cells (fun y => mass (f.dec y)) =
      reduceCells combine start alph.cells mass := by
  have p := (reindex_list alph f.inverse).map mass
  have h := p.foldr_eq' (f := combine) (by
    intro a _ b _ z
    exact comm a b z) start
  simpa only [reduceCells, List.map_map, Function.comp_def, BlockPerm.inverse] using h

/-- The only scalar laws needed for an equality under reordering.
    gap computes absolute deviation. share divides a row's mass equally
    across the block alphabet. half divides the total absolute deviation by two. -/
structure Weights (W : Type) where
  zero : W
  add : W → W → W
  high : W → W → W
  gap : W → W → W
  share : W → Nat → W
  half : W → W
  add_swap : ∀ a b z, add b (add a z) = add a (add b z)
  high_swap : ∀ a b z, high b (high a z) = high a (high b z)

def pushRows (f : E → BlockPerm B) (mass : E → B → W) (e : E) (y : B) : W :=
  mass e ((f e).dec y)

def tvUniform [DecidableEq B] (w : Weights W) (alph : Alphabet B)
    (views : List E) (mass : E → B → W) : W :=
  w.half (reduceCells w.add w.zero views (fun e =>
    let target := w.share (reduceCells w.add w.zero alph.cells (mass e)) alph.cells.length
    reduceCells w.add w.zero alph.cells (fun y => w.gap (mass e y) target)))

def pGuess [DecidableEq B] (w : Weights W) (alph : Alphabet B)
    (views : List E) (mass : E → B → W) : W :=
  reduceCells w.add w.zero views (fun e => reduceCells w.high w.zero alph.cells (mass e))

theorem tv_preserved [DecidableEq B] (w : Weights W) (alph : Alphabet B)
    (views : List E) (mass : E → B → W) (f : E → BlockPerm B) :
    tvUniform w alph views (pushRows f mass) = tvUniform w alph views mass := by
  unfold tvUniform pushRows
  congr 2
  funext e
  dsimp only
  rw [reduce_reindex alph (f e) w.add w.add_swap w.zero (mass e)]
  exact reduce_reindex alph (f e) w.add w.add_swap w.zero
    (fun y => w.gap (mass e y) _)

theorem guessing_preserved [DecidableEq B] (w : Weights W) (alph : Alphabet B)
    (views : List E) (mass : E → B → W) (f : E → BlockPerm B) :
    pGuess w alph views (pushRows f mass) = pGuess w alph views mass := by
  unfold pGuess pushRows
  congr 1
  funext e
  exact reduce_reindex alph (f e) w.high w.high_swap w.zero (mass e)

/-- Instantiate the row view with e = (initial state, side information).
    The initial state may be correlated with the input and the side information. -/
theorem sequence_its (m : Machine S B) (n : Nat) [DecidableEq (Word B n)]
    (w : Weights W) (alph : Alphabet (Word B n)) (views : List E)
    (initial : E → S) (mass : E → Word B n → W) :
    let moved := pushRows (fun e => causalPermutation m n (initial e)) mass
    tvUniform w alph views moved = tvUniform w alph views mass ∧
    pGuess w alph views moved = pGuess w alph views mass :=
  ⟨tv_preserved w alph views mass _, guessing_preserved w alph views mass _⟩

/-- Telescoping estimates for hybrids. The error metric obeys its triangle
    inequality and each adjacent replacement has its own certified budget. -/
structure ErrorScale (R : Type) where
  zero : R
  plus : R → R → R
  le : R → R → Prop
  trans : ∀ {a b c}, le a b → le b c → le a c
  add_mono : ∀ {a b c d}, le a b → le c d → le (plus a c) (plus b d)

def budget (sc : ErrorScale R) (eps : Nat → R) : Nat → R
  | 0 => sc.zero
  | n+1 => sc.plus (budget sc eps n) (eps n)

theorem hybrid_budget (sc : ErrorScale R) (d : P → P → R) (h : Nat → P)
    (eps : Nat → R) (n : Nat) (diagonal : sc.le (d (h 0) (h 0)) sc.zero)
    (triangle : ∀ a b c, sc.le (d a c) (sc.plus (d a b) (d b c)))
    (step : ∀ i, i < n → sc.le (d (h i) (h (i+1))) (eps i)) :
    sc.le (d (h 0) (h n)) (budget sc eps n) := by
  induction n with
  | zero => exact diagonal
  | succ n ih =>
    exact sc.trans (triangle (h 0) (h n) (h (n+1)))
      (sc.add_mono (ih (fun i hi => step i (by omega))) (step n (by omega)))

/-- Exact distances for finite laws encoded as integer weights with a common
    denominator. This is twice TV multiplied by alphabet size and total weight. -/
def gapCount (a b : Nat) : Nat := (a - b) + (b - a)

def countTV [DecidableEq B] (alph : Alphabet B) (views : List E)
    (mass : E → B → Nat) : Nat :=
  reduceCells Nat.add 0 views (fun e =>
    let total := reduceCells Nat.add 0 alph.cells (mass e)
    reduceCells Nat.add 0 alph.cells (fun y => gapCount (alph.cells.length * mass e y) total))

def countGuess [DecidableEq B] (alph : Alphabet B) (views : List E)
    (mass : E → B → Nat) : Nat :=
  reduceCells Nat.add 0 views (fun e => reduceCells Nat.max 0 alph.cells (mass e))

theorem count_tv_preserved [DecidableEq B] (alph : Alphabet B) (views : List E)
    (mass : E → B → Nat) (f : E → BlockPerm B) :
    countTV alph views (pushRows f mass) = countTV alph views mass := by
  unfold countTV pushRows
  congr 1
  funext e
  dsimp only
  rw [reduce_reindex alph (f e) Nat.add (fun _ _ _ => Nat.add_left_comm ..) 0 (mass e)]
  exact reduce_reindex alph (f e) Nat.add (fun _ _ _ => Nat.add_left_comm ..) 0
    (fun y => gapCount (alph.cells.length * mass e y) _)

theorem count_guess_preserved [DecidableEq B] (alph : Alphabet B) (views : List E)
    (mass : E → B → Nat) (f : E → BlockPerm B) :
    countGuess alph views (pushRows f mass) = countGuess alph views mass := by
  unfold countGuess pushRows
  congr 1
  funext e
  exact reduce_reindex alph (f e) Nat.max (by intro a b z; change max b (max a z) = max a (max b z); omega) 0 (mass e)

/-- Fiber counting for a deterministic observation of a uniform input.
    A mask is the membership predicate of one fiber in the enumerated alphabet. -/
def hits : List Bool → Nat
  | [] => 0
  | true :: rest => hits rest + 1
  | false :: rest => hits rest

def weightedFiber (yes no : Nat) : List Bool → Nat
  | [] => 0
  | true :: rest => yes + weightedFiber yes no rest
  | false :: rest => no + weightedFiber yes no rest

theorem hits_le_size (mask : List Bool) : hits mask ≤ mask.length := by
  induction mask with
  | nil => decide
  | cons x xs ih => cases x <;> simp [hits] <;> omega

theorem fiber_count (mask : List Bool) (yes no : Nat) :
    weightedFiber yes no mask = hits mask * yes + (mask.length - hits mask) * no := by
  induction mask with
  | nil => simp [weightedFiber, hits]
  | cons x xs ih =>
    have bounded := hits_le_size xs
    cases x with
    | false =>
      have h : xs.length + 1 - hits xs = xs.length - hits xs + 1 := by omega
      simp [weightedFiber, hits, h, Nat.succ_mul, ih]
      omega
    | true =>
      simp [weightedFiber, hits, Nat.succ_mul, ih]
      omega

theorem fiber_deviation (mask : List Bool) :
    let m := mask.length
    let n := hits mask
    weightedFiber (gapCount m n) (gapCount 0 n) mask = 2 * (n * (m-n)) := by
  dsimp only
  have h := hits_le_size mask
  have z : hits mask - mask.length = 0 := by omega
  rw [fiber_count]
  simp only [gapCount, z, Nat.add_zero, Nat.zero_sub, Nat.sub_zero, Nat.zero_add]
  rw [Nat.mul_comm (mask.length - hits mask) (hits mask)]
  omega

def bestGuess : List Bool → Nat
  | [] => 0
  | x :: rest => max (if x then 1 else 0) (bestGuess rest)

theorem fiber_guess (mask : List Bool) : bestGuess mask = if hits mask = 0 then 0 else 1 := by
  induction mask with
  | nil => rfl
  | cons x xs ih =>
    cases x <;> simp [hits, bestGuess, ih] <;> split <;> decide

/-- Sum over fibers; the statement uses integer numerators, with no quotient
    rounding. In a partition the sizes sum to m, so dividing by m^2 gives
    TV + sum_t Pr[t]^2 = 1. -/
theorem fiber_collision (counts : List Nat) (m : Nat) (bounded : ∀ n ∈ counts, n ≤ m) :
    (counts.map (fun n => n * (m - n))).sum + (counts.map (fun n => n * n)).sum =
      counts.sum * m := by
  induction counts with
  | nil => simp
  | cons n ns ih =>
    have hn := bounded n (by simp)
    have htail := ih (fun x hx => bounded x (by simp [hx]))
    have term : n * (m-n) + n * n = n * m := by
      rw [← Nat.mul_add, Nat.sub_add_cancel hn]
    simp only [List.map_cons, List.sum_cons, Nat.add_mul]
    omega

/-- Independent suffixes multiply both common-denominator L1 numerators and
    total weights by the same factor. This proves the cancellation used in the
    hybrid argument without any independence assumption on the real prefixes. -/
def l1 (cells : List B) (p q : B → Nat) : Nat :=
  (cells.map (fun x => gapCount (p x) (q x))).sum

theorem gap_scale (a b k : Nat) : gapCount (a*k) (b*k) = gapCount a b * k := by
  simp only [gapCount, Nat.mul_sub_right_distrib, Nat.add_mul]

theorem l1_triangle (cells : List B) (p q r : B → Nat) :
    l1 cells p r ≤ l1 cells p q + l1 cells q r := by
  induction cells with
  | nil => simp [l1]
  | cons x xs ih =>
    have point : gapCount (p x) (r x) ≤ gapCount (p x) (q x) + gapCount (q x) (r x) := by
      unfold gapCount; omega
    simp only [l1, List.map_cons, List.sum_cons] at *
    omega

theorem suffix_row_sum (suffix : List D) (weights : D → Nat) (a b : Nat) :
    l1 suffix (fun j => a * weights j) (fun j => b * weights j) =
    gapCount a b * (suffix.map weights).sum := by
  induction suffix with
  | nil => simp [l1]
  | cons x xs ih =>
    simp only [l1, List.map_cons, List.sum_cons] at *
    rw [gap_scale, ih, Nat.mul_add]

theorem independent_suffix (heads : List B) (suffix : List D) (p q : B → Nat)
    (weights : D → Nat) :
    (heads.map (fun x => l1 suffix (fun j => p x * weights j)
                                   (fun j => q x * weights j))).sum =
    l1 heads p q * (suffix.map weights).sum := by
  induction heads with
  | nil => simp [l1]
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons]
    change _ = (gapCount (p x) (q x) + l1 xs p q) * (suffix.map weights).sum
    rw [ih, suffix_row_sum, Nat.add_mul]

/-- Explicit finite alphabets establish that the row-enumeration assumption
    used by the probability theorem is inhabited at physical block widths. -/
theorem map_count_injective [DecidableEq A] [DecidableEq B]
    (f : A → B) (injective : ∀ {a b}, f a = f b → a = b) (xs : List A) (a : A) :
    (xs.map f).count (f a) = xs.count a := by
  induction xs with
  | nil => rfl
  | cons b xs ih =>
    by_cases h : b = a
    · subst b; simp [ih]
    · have hn : f b ≠ f a := fun eq => h (injective eq)
      simp [List.count_cons_of_ne h, List.count_cons_of_ne hn, ih]

theorem map_count_missing [DecidableEq B] (f : A → B) (xs : List A) (b : B)
    (missing : ∀ a, f a ≠ b) : (xs.map f).count b = 0 := by
  induction xs with
  | nil => rfl
  | cons a xs ih => simp [List.count_cons_of_ne (missing a), ih]

theorem fin_count_once (n : Nat) (x : Fin n) : (List.finRange n).count x = 1 := by
  induction n with
  | zero => exact Fin.elim0 x
  | succ n ih =>
    rw [List.finRange_succ]
    refine Fin.cases ?_ (fun k => ?_) x
    · rw [List.count_cons_self, map_count_missing _ _ _ Fin.succ_ne_zero]
    · rw [List.count_cons_of_ne (Ne.symm (Fin.succ_ne_zero k)),
        map_count_injective Fin.succ (fun h => Fin.succ_inj.mp h), ih]

def bitAlphabet (n : Nat) : Alphabet (BitVec n) where
  cells := (List.finRange (2^n)).map BitVec.ofFin
  count_once b := by
    cases b with
    | ofFin k =>
      rw [map_count_injective BitVec.ofFin (fun h => congrArg BitVec.toFin h), fin_count_once]

local instance (priority := high) pairEquality [DecidableEq A] [DecidableEq B] : BEq (A × B) :=
  instBEqOfDecidableEq

theorem rectangle_count [DecidableEq A] [DecidableEq B] (xs : List A) (ys : List B)
    (a : A) (b : B) :
    (xs.flatMap (fun x => ys.map (Prod.mk x))).count (a,b) = xs.count a * ys.count b := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [List.flatMap_cons, List.count_append, ih]
    by_cases h : x = a
    · subst x
      rw [map_count_injective (Prod.mk a) (fun h => congrArg Prod.snd h) ys b,
        List.count_cons_self, Nat.add_mul, Nat.one_mul, Nat.add_comm]
    · rw [map_count_missing (Prod.mk x) ys (a,b) (fun _ eq => h (congrArg Prod.fst eq)),
        List.count_cons_of_ne h, Nat.zero_add]

def productAlphabet [DecidableEq A] [DecidableEq B] (a : Alphabet A) (b : Alphabet B) :
    Alphabet (A × B) where
  cells := a.cells.flatMap fun x => b.cells.map (Prod.mk x)
  count_once c := by rcases c with ⟨x,y⟩; rw [rectangle_count, a.count_once, b.count_once]

def wordDecEq [DecidableEq B] : (n : Nat) → DecidableEq (Word B n)
  | 0 => inferInstanceAs (DecidableEq Unit)
  | n+1 => @instDecidableEqProd B (Word B n) _ (wordDecEq n)

def wordAlphabet [DecidableEq B] (base : Alphabet B) :
    (n : Nat) → @Alphabet (Word B n) (wordDecEq n)
  | 0 => @Alphabet.mk Unit (inferInstanceAs (DecidableEq Unit)) [()] (fun u => by cases u; rfl)
  | n+1 => @productAlphabet B (Word B n) _ (wordDecEq n) base (wordAlphabet base n)

end PTGITS

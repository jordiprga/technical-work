import Std

/-! The AIS 20/31 v3 §§996–998 profile. AES and SHA are parameters.
    The only algebraic laws on AES are its two inverse identities. -/
namespace AISProfile

abbrev Block := BitVec 128
abbrev Key := BitVec 256

structure Primitives where
  encrypt : Key → Block → Block
  decrypt : Key → Block → Block
  decryptEncrypt : ∀ k a, decrypt k (encrypt k a) = a
  encryptDecrypt : ∀ k a, encrypt k (decrypt k a) = a
  digest : BitVec 384 → Key

/-- The reference accepts 0…128 input bits; pad with zeros on the right. -/
def refPad (w : Nat) (a : BitVec w) : Block :=
  (a.setWidth 128) <<< (128 - w)

/-- Read directly from §§996–997 (one complete output per request). -/
def reference (c : Primitives) (p : Block) (s : Key)
    (w : Fin 129) (a : BitVec w.val) : Block × Key :=
  (c.encrypt s (p ^^^ refPad w.val a),
   c.digest (s ++ (p ^^^ refPad w.val a)))

inductive Input where
  | absent
  | present (a : Block)

def encode : Input → Block
  | .absent => 0
  | .present a => a

def request (s : Key) (a : Input) : Key × Block := (s, encode a)
def perWord (z : Key × Block) := z
def output (c : Primitives) (p : Block) (z : Key × Block) : Block :=
  c.encrypt z.1 (p ^^^ z.2)
def transition (c : Primitives) (p : Block) (s : Key) (a : Input) : Key :=
  c.digest (s ++ (p ^^^ encode a))

def tupleStep (c : Primitives) (p : Block) (s : Key) (a : Input) : Block × Key :=
  (output c p (perWord (request s a)), transition c p s a)

theorem referencePresent (c : Primitives) (p : Block) (s : Key) (a : Block) :
    reference c p s 128 a = tupleStep c p s (.present a) := by
  change (c.encrypt s (p ^^^ (a.setWidth 128 <<< 0)), c.digest (s ++ (p ^^^ (a.setWidth 128 <<< 0)))) = _
  simp [tupleStep, perWord, request, encode, transition, output]

theorem referenceAbsent (c : Primitives) (p : Block) (s : Key) :
    reference c p s 0 (0#0) = tupleStep c p s .absent := by
  rfl

theorem allZeroIsAutonomous (c : Primitives) (p : Block) (s : Key) :
    tupleStep c p s (.present 0) = tupleStep c p s .absent := rfl

def inverseOutput (c : Primitives) (p : Block) (s : Key) (y : Block) :=
  p ^^^ c.decrypt s y

theorem leftInverse (c : Primitives) (p : Block) (s : Key) (a : Block) :
    inverseOutput c p s (tupleStep c p s (.present a)).1 = a := by
  simp [inverseOutput, tupleStep, perWord, request, output, encode, c.decryptEncrypt,
    ← BitVec.xor_assoc]

theorem rightInverse (c : Primitives) (p : Block) (s : Key) (y : Block) :
    (tupleStep c p s (.present (inverseOutput c p s y))).1 = y := by
  simp [inverseOutput, tupleStep, perWord, request, output, encode, c.encryptDecrypt,
    ← BitVec.xor_assoc]

/-- Algorithmic 4-tuples have SM=Key, PS=Unit, S=Key.
    The physical delivery encodes two successive, distinct allocations as sm. -/
def packSeed (first second : Block) : Key := first ++ second
def seed (sm : Key) (_personalization : Unit) : Key := sm
def reseed (s sm : Key) (_personalization : Unit) : Key := s ^^^ sm

theorem seedReachable (s : Key) : seed s () = s := rfl

theorem reseedInverse (s sm : Key) : reseed s (reseed s sm ()) () = sm := by
  simp [reseed, ← BitVec.xor_assoc]

def plant (s : BitVec 246) : Key := s.setWidth 256

theorem plantInjective (x y : BitVec 246) (h : plant x = plant y) : x = y := by
  have h' := congrArg (BitVec.setWidth 246) h
  simpa [plant, BitVec.setWidth_setWidth_of_le] using h'

/-- If all allowed first inputs give equal outputs at s,t, any finite
    signature made of such outputs coincides, even when operational cloning
    is prohibited. Signature separation is a property of the keyed primitive. -/
theorem distinguishSignatures (c : Primitives) (p : Block) (bs : List Block)
    (s t : Key)
    (h : ∀ a, (tupleStep c p s (.present a)).1 =
               (tupleStep c p t (.present a)).1) :
    bs.map (c.encrypt s) = bs.map (c.encrypt t) := by
  have eqb (b : Block) : c.encrypt s b = c.encrypt t b := by
    have eq := h (p ^^^ b)
    simpa [tupleStep, output, request, perWord, encode, ← BitVec.xor_assoc] using eq
  exact List.map_congr_left (fun b _ => eqb b)

theorem effectiveClasses (c : Primitives) (p : Block) (bs : List Block)
    (separated : ∀ x y : BitVec 246,
      bs.map (c.encrypt (plant x)) = bs.map (c.encrypt (plant y)) → x = y)
    (x y : BitVec 246)
    (sameBehavior : ∀ a, (tupleStep c p (plant x) (.present a)).1 =
                           (tupleStep c p (plant y) (.present a)).1) : x = y :=
  separated x y (distinguishSignatures c p bs _ _ sameBehavior)

/-- An actual noise source may have admissible seeds on a different subset
    from the zero-extension image. Any supported injection is sufficient. -/
theorem effectiveSupported (c : Primitives) (p : Block) (bs : List Block)
    (code : BitVec 246 → Key)
    (injective : ∀ x y, code x = code y → x = y)
    (separated : ∀ s t, bs.map (c.encrypt s) = bs.map (c.encrypt t) → s = t)
    (x y : BitVec 246)
    (sameBehavior : ∀ a, (tupleStep c p (code x) (.present a)).1 =
                           (tupleStep c p (code y) (.present a)).1) : x = y :=
  injective x y (separated _ _ (distinguishSignatures c p bs _ _ sameBehavior))

theorem seedProfileThreshold : 246 * 100 < 256 * 98 := by decide

theorem requestBound : 128 ≤ 2 ^ 19 := by decide
theorem signatureCollisionScale :
    (2^256 * (2^256 - 1) / 2) * 2^128 <
      2^128 * (2^128-1) * (2^128-2) * (2^128-3) * (2^128-4) := by decide

/-- Finite enumerations and integer numerators avoid numerical approximation.
    Keys/outputs are uniform over the supplied enumerations, with one entry per
    word when instantiated with the entire key/block spaces. -/
def tally (xs : List α) (f : α → Nat) : Nat :=
  (xs.map f).sum

private theorem tally_add (xs : List α) (f g : α → Nat) :
    tally xs (fun x => f x + g x) = tally xs f + tally xs g := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simpa [tally, Nat.add_assoc, Nat.add_left_comm, Nat.add_comm] using ih

private theorem tally_const (xs : List α) (c : Nat) :
    tally xs (fun _ => c) = xs.length * c := by
  induction xs with
  | nil => simp [tally]
  | cons x xs ih => simp [tally] at *; rw [ih, Nat.succ_mul, Nat.add_comm]

private theorem tally_mul (k : Nat) (xs : List α) (f : α → Nat) :
    tally xs (fun x => k * f x) = k * tally xs f := by
  induction xs with
  | nil => simp [tally]
  | cons x xs ih =>
    simp only [tally, List.map_cons, List.sum_cons] at *
    rw [ih, Nat.mul_add]

private theorem tally_mono (xs : List α) (f g : α → Nat)
    (h : ∀ x, f x ≤ g x) : tally xs f ≤ tally xs g := by
  induction xs with
  | nil => exact Nat.le_refl _
  | cons x xs ih => exact Nat.add_le_add (h x) ih

/-- The public input may be chosen adaptively. The predicate at the endpoint
    may look at the persistent terminal key. Pure distinguishers suffice by
    fixing independent coins, then averaging. Hist is any deterministic record
    of outputs, including the history needed for the choice of the next input. -/
structure Observer (Hist : Type) where
  choose : Hist → Input
  record : Hist → Block → Hist
  accepts : Hist → Key → Bool

def realRun (c : Primitives) (p : Block) (obs : Observer Hist) :
    Nat → Hist → Key → Bool
  | 0, h, s => obs.accepts h s
  | n+1, h, s =>
    let z := tupleStep c p s (obs.choose h)
    realRun c p obs n (obs.record h z.1) z.2

def realCount (keys : List Key) (c : Primitives) (p : Block)
    (obs : Observer Hist) (n : Nat) (h : Hist) : Nat :=
  tally keys (fun k => (realRun c p obs n h k).toNat)

def idealCount (keys : List Key) (words : List Block) (obs : Observer Hist) :
    Nat → Hist → Nat
  | 0, h => tally keys (fun k => (obs.accepts h k).toNat)
  | n+1, h => tally words (fun y => idealCount keys words obs n (obs.record h y))

/-- Numerator slack d is measured with denominator |keys|·|words|.
    The premise compares a single AES/SHA pair under one hidden uniform key
    with an independent random output and next key, on the continuation tests
    of this observer within its computation budget. -/
def PairBound (keys : List Key) (words : List Block) (c : Primitives)
    (p : Block) (obs : Observer Hist) (horizon d : Nat) : Prop :=
  ∀ n, n < horizon → ∀ h,
    words.length * realCount keys c p obs (n+1) h ≤
      tally words (fun y => realCount keys c p obs n (obs.record h y)) + d

/-- A local assumption on just one keyed AES evaluation and a SHA digest
    with the same key as secret prefix. 'allowed' specifies tests within
    the claimed time bound; it must include the continuations below. -/
def PrimitiveBound (keys : List Key) (words : List Block) (c : Primitives)
    (allowed : (Block → Key → Bool) → Prop) (d : Nat) : Prop :=
  ∀ b test, allowed test →
    words.length * tally keys (fun k =>
      (test (c.encrypt k b) (c.digest (k ++ b))).toNat) ≤
      tally words (fun y => tally keys (fun k => (test y k).toNat)) + d

theorem primitiveToPairBound (keys : List Key) (words : List Block) (c : Primitives)
    (p : Block) (obs : Observer Hist) (horizon d : Nat)
    (allowed : (Block → Key → Bool) → Prop)
    (primitive : PrimitiveBound keys words c allowed d)
    (cost : ∀ n, n < horizon → ∀ h,
      allowed (fun y k => realRun c p obs n (obs.record h y) k)) :
    PairBound keys words c p obs horizon d := by
  intro n hn h
  exact primitive (p ^^^ encode (obs.choose h)) _ (cost n hn h)

def slack (m d : Nat) : Nat → Nat
  | 0 => 0
  | n+1 => m^n * d + m * slack m d n

theorem accumulatedSlack (m d n : Nat) :
    slack m d n * m = n * d * m^n := by
  induction n with
  | zero => simp [slack]
  | succ n ih =>
    simp only [slack, Nat.add_mul]
    rw [Nat.mul_assoc m, ih, Nat.succ_mul, Nat.add_mul, Nat.pow_succ]
    simp [Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm, Nat.add_comm]

theorem adaptiveHybrid (keys : List Key) (words : List Block) (c : Primitives)
    (p : Block) (obs : Observer Hist) (horizon d : Nat)
    (localPair : PairBound keys words c p obs horizon d)
    (n : Nat) (hn : n ≤ horizon) (h : Hist) :
    words.length^n * realCount keys c p obs n h ≤
    idealCount keys words obs n h + slack words.length d n := by
  induction n generalizing h with
  | zero => simp [realCount, realRun, idealCount, slack]
  | succ n ih =>
    have step := Nat.mul_le_mul_left (words.length^n)
      (localPair n hn h)
    have rec := tally_mono words
      (fun y => words.length^n * realCount keys c p obs n (obs.record h y))
      (fun y => idealCount keys words obs n (obs.record h y) + slack words.length d n)
      (fun y => ih (Nat.le_trans (Nat.le_succ _) hn) (obs.record h y))
    rw [tally_mul, tally_add, tally_const] at rec
    rw [Nat.mul_add] at step
    calc
      _ = words.length^n *
            (words.length * realCount keys c p obs (n+1) h) := by
              rw [Nat.pow_succ, Nat.mul_assoc]
      _ ≤ _ := step
      _ ≤ _ := by
        simp only [idealCount, slack]
        omega

/-- Density bound for a non-uniform seed, applied to each declared side view.
    For mass w with total W, choose a=bounds numerator, b=denominator such that
    |keys|*b*w(k) ≤ a*W. This multiplies success on a uniform seed by a/b. -/
theorem seedMassTransfer (keys : List Key) (weight : Key → Nat)
    (accept : Key → Bool) (a b : Nat)
    (bound : ∀ k, keys.length*b*weight k ≤ a*tally keys weight) :
    keys.length*b*tally keys (fun k => weight k*(accept k).toNat) ≤
      (a*tally keys weight)*tally keys (fun k => (accept k).toNat) := by
  rw [← tally_mul, ← tally_mul]
  apply tally_mono
  intro k
  rw [← Nat.mul_assoc]
  exact Nat.mul_le_mul_right _ (bound k)

/-- Uniform-target guessing after fixing all allowed observations and coins.
    The target may itself encode a multi-block fragment. -/
theorem idealTargetCount [DecidableEq Target] (targets : List Target)
    (views : List View) (guess : View → Target)
    (once : ∀ t, targets.count t = 1) :
    tally views (fun v => targets.count (guess v)) = views.length := by
  simp only [once, tally_const, Nat.mul_one]

/-- Two snapshots: the output determines the fresh input when the pre-state
    is given. Thus the post-state can be computed from the output itself. -/
def stateFromOutput (c : Primitives) (p : Block) (s : Key) (y : Block) : Key :=
  transition c p s (.present (inverseOutput c p s y))

theorem snapshotGraph (c : Primitives) (p : Block) (s : Key) (a : Block) :
    (tupleStep c p s (.present a)).2 =
      stateFromOutput c p s (tupleStep c p s (.present a)).1 := by
  rw [stateFromOutput, leftInverse]
  rfl

/-- Verifying a candidate predecessor of this profile is precisely checking
    SHA-256 with the known 128-bit suffix for the chosen request. This lets
    an arbitrary-preimage predicate reuse that fixed-suffix assumption. -/
theorem transitionPreimage (c : Primitives) (p : Block) (s target : Key) (a : Input) :
    transition c p s a = target ↔ c.digest (s ++ (p ^^^ encode a)) = target := Iff.rfl

/-- Physical inputs traverse all hash suffixes. Non-constant dependence on
    the new block is equivalent at the two descriptions, for each old key. -/
theorem influenceAtState (c : Primitives) (p : Block) (s : Key) :
    (∃ a₀ a₁, transition c p s (.present a₀) ≠ transition c p s (.present a₁)) ↔
    (∃ b₀ b₁ : Block, c.digest (s ++ b₀) ≠ c.digest (s ++ b₁)) := by
  constructor
  · rintro ⟨a₀, a₁, h⟩
    exact ⟨p ^^^ a₀, p ^^^ a₁, h⟩
  · rintro ⟨b₀, b₁, h⟩
    refine ⟨p ^^^ b₀, p ^^^ b₁, ?_⟩
    simpa [transition, encode, ← BitVec.xor_assoc] using h

/-- A degenerate old key (all fresh blocks update identically) explicitly
    yields equal SHA digests for two different 384-bit strings. -/
theorem constantSliceCollision (c : Primitives) (p : Block) (s : Key)
    (constant : ∀ a b, transition c p s (.present a) = transition c p s (.present b)) :
    (s ++ (0#128)) ≠ (s ++ (1#128)) ∧
      c.digest (s ++ (0#128)) = c.digest (s ++ (1#128)) := by
  constructor
  · intro eq
    have diff := congrArg (fun x : BitVec 384 => x.getLsbD 0) eq
    change (s ++ (0#128)).getLsbD 0 = (s ++ (1#128)).getLsbD 0 at diff
    simp only [BitVec.getLsbD_append] at diff
    contradiction
  · have eq := constant (p ^^^ (0#128)) (p ^^^ (1#128))
    simpa [transition, encode, ← BitVec.xor_assoc] using eq

/-- When the predecessor's additional input is replaceable, its verification
    condition is preimage finding on the whole 384-bit message domain. -/
theorem alternativeInputPreimage (c : Primitives) (p : Block) (target : Key) :
    (∃ s a, transition c p s a = target) ↔
      (∃ s : Key, ∃ b : Block, c.digest (s ++ b) = target) := by
  constructor
  · rintro ⟨s, a, h⟩
    exact ⟨s, p ^^^ encode a, h⟩
  · rintro ⟨s, b, h⟩
    refine ⟨s, .present (p ^^^ b), ?_⟩
    simpa [transition, encode, ← BitVec.xor_assoc] using h

/-- With a duplicate-free key space, each proposed label hits at most one key.
Repeated queries are charged to the query budget each time. -/
private theorem labelMass (keys labels : List Key) (once : ∀ k, keys.count k = 1) :
    tally keys (fun k => labels.count k) ≤ labels.length := by
  have point (target : Key) :
      tally keys (fun k => if target = k then 1 else 0) = keys.count target := by
    clear once
    induction keys with
    | nil => rfl
    | cons k ks ih =>
      simp only [tally, List.map_cons, List.sum_cons] at *
      by_cases e : target = k
      · subst k; simp [ih, Nat.add_comm]
      · simp [e, List.count_cons_of_ne (Ne.symm e), ih]
  induction labels with
  | nil => simpa only [List.count_nil, List.length_nil, Nat.mul_zero] using Nat.le_of_eq (tally_const keys 0)
  | cons t rest ih =>
    have step (k : Key) : (t :: rest).count k =
        (if t = k then 1 else 0) + rest.count k := by
      by_cases eq : t = k
      · subst k; simp [Nat.add_comm]
      · simp [eq, List.count_cons_of_ne eq]
    simp only [step, tally_add, point, List.length_cons]
    have bound := once t
    omega

/-- Fix the ideal transcript and coins independent of the hidden uniform key.
If a coupling agrees for all keys outside its Q queried labels, the real count
can exceed the ideal count by at most Q. The oracle coupling itself is external. -/
theorem singleUseHiddenLabel (keys labels : List Key) (once : ∀ k, keys.count k = 1)
    (real ideal : Key → Bool) (agree : ∀ k, k ∉ labels → real k = ideal k) :
    tally keys (fun k => (real k).toNat) ≤
      tally keys (fun k => (ideal k).toNat) + labels.length := by
  have step (k : Key) : (real k).toNat ≤ (ideal k).toNat + labels.count k := by
    by_cases h : k ∈ labels
    · have pos := List.count_pos_iff.mpr h
      cases real k <;> cases ideal k <;> simp_all [Bool.toNat] <;> omega
    · rw [agree k h]; omega
  exact Nat.le_trans ((tally_add _ _ _) ▸ tally_mono keys _ _ step)
    (Nat.add_le_add_left (labelMass keys labels once) _)

end AISProfile

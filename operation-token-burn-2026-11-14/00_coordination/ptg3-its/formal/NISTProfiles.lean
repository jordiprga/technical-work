import Std

/-! Algebra of the last 128-bit input to NIST profiles. The two inverse laws
are the specification of a block permutation. No PRP, source or entropy
hypothesis is used by these deterministic statements. -/
namespace NISTProfiles

abbrev Block := BitVec 128
abbrev Key := BitVec 256

structure Cipher where
  enc : Key → Block → Block
  dec : Key → Block → Block
  decEnc : ∀ k x, dec k (enc k x) = x
  encDec : ∀ k x, enc k (dec k x) = x

structure State where
  key : Key
  ctr : Block

def inc (v : Block) := v + 1
def prev (v : Block) := v - 1

theorem xorUndo {n : Nat} (m x : BitVec n) : m ^^^ (m ^^^ x) = x := by
  rw [← BitVec.xor_assoc, BitVec.xor_self, BitVec.zero_xor]

theorem xorZeroBlock (x : Block) : x ^^^ (0 : Block) = x := BitVec.xor_zero

/-- 90A Update, seedlen = 384, expressed as two seed fields. -/
def update (c : Cipher) (s : State) (h : Key) (l : Block) : State :=
  let v₁ := inc s.ctr
  let v₂ := inc v₁
  let v₃ := inc v₂
  ⟨((c.enc s.key v₁) ++ (c.enc s.key v₂)) ^^^ h, (c.enc s.key v₃) ^^^ l⟩

/-- 90C RBG3(RS) for one 128-bit external request at strength 256.
No additional input at reseed or generate. Produce two blocks and advance
the counter over BOTH before post-Update. Return the leftmost block. -/
def rsStep (c : Cipher) (s : State) (h : Key) (l : Block) : Block × State :=
  let t := update c s h l
  let v₁ := inc t.ctr
  let v₂ := inc v₁
  let internal := (c.enc t.key v₁, c.enc t.key v₂)
  (internal.1, update c ⟨t.key, v₂⟩ 0 0)

def rsRecover (c : Cipher) (s : State) (h : Key) (y : Block) : Block :=
  let base := update c s h 0
  base.ctr ^^^ prev (c.dec base.key y)

theorem rsRecoversLow (c : Cipher) (s : State) (h : Key) (l : Block) :
    rsRecover c s h (rsStep c s h l).1 = l := by
  simp only [rsRecover, rsStep, update, inc, prev, xorZeroBlock, c.decEnc,
    BitVec.add_sub_cancel, xorUndo]

theorem rsProducesEveryBlock (c : Cipher) (s : State) (h : Key) (y : Block) :
    (rsStep c s h (rsRecover c s h y)).1 = y := by
  simp only [rsRecover, rsStep, update, inc, prev, xorZeroBlock, xorUndo,
    BitVec.sub_add_cancel, c.encDec]

/-- The second generated internal cipher block cannot repeat the first
for any state, even if the 128-bit counter wraps. -/
theorem consecutiveDistinct (c : Cipher) (k : Key) (v : Block) :
    c.enc k v ≠ c.enc k (inc v) := by
  intro equalOutput
  have same := congrArg (c.dec k) equalOutput
  simp only [c.decEnc, inc] at same
  have pair : v + (0 : Block) = v + 1 := by
    exact (BitVec.add_zero v).trans same
  have impossible := (BitVec.add_right_inj v).mp pair
  exact (by decide : (0 : Block) ≠ 1) impossible

/-- SP 800-38B complete two-block message. The fixed subkey is K1. The
lemma holds for every subkey, including the standardized value. -/
def cmacTwo (c : Cipher) (k : Key) (k₁ p a : Block) : Block :=
  c.enc k ((c.enc k p ^^^ k₁) ^^^ a)

def cmacUndo (c : Cipher) (k : Key) (k₁ p y : Block) : Block :=
  (c.enc k p ^^^ k₁) ^^^ c.dec k y

theorem cmacRecoversLast (c : Cipher) (k : Key) (k₁ p a : Block) :
    cmacUndo c k k₁ p (cmacTwo c k k₁ p a) = a := by
  simp only [cmacUndo, cmacTwo, c.decEnc, xorUndo]

theorem cmacProducesEveryTag (c : Cipher) (k : Key) (k₁ p y : Block) :
    cmacTwo c k k₁ p (cmacUndo c k k₁ p y) = y := by
  simp only [cmacUndo, cmacTwo, xorUndo, c.encDec]

/-- In the direct 90A profile the high 256 bits of the provided data are
zero. Only the first 128-bit output is part of this expression. -/
def directFirst (c : Cipher) (s : State) (a : Block) : Block :=
  let t := update c s 0 a
  c.enc t.key (inc t.ctr)

theorem directAndRSFirst (c : Cipher) (s : State) (a : Block) :
    directFirst c s a = (rsStep c s 0 a).1 := rfl

theorem cmacDirectRoundtrip (c : Cipher) (s : State) (k : Key) (k₁ p a : Block) :
    cmacUndo c k k₁ p (rsRecover c s 0 (directFirst c s (cmacTwo c k k₁ p a))) = a := by
  rw [directAndRSFirst, rsRecoversLow, cmacRecoversLast]

theorem cmacDirectOnto (c : Cipher) (s : State) (k : Key) (k₁ p y : Block) :
    directFirst c s (cmacTwo c k k₁ p (cmacUndo c k k₁ p (rsRecover c s 0 y))) = y := by
  rw [cmacProducesEveryTag, directAndRSFirst, rsProducesEveryBlock]

/-- The physical mask is consumed exclusively at XOR in this model.
The generate function may carry arbitrary persistent state. -/
def xorStep {S : Type} (gen : S → Block × S) (s : S) (f : Block) : Block × S :=
  let (b,t) := gen s
  (b ^^^ f, t)

theorem xorRecoversPhysical {S : Type} (gen : S → Block × S) (s : S) (f : Block) :
    (gen s).1 ^^^ (xorStep gen s f).1 = f := by
  simp only [xorStep, xorUndo]

theorem xorNextStateIndependent {S : Type} (gen : S → Block × S) (s : S) (f g : Block) :
    (xorStep gen s f).2 = (xorStep gen s g).2 := rfl

end NISTProfiles

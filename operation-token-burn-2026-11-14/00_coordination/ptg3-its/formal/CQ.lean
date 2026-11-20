import ITS

/-! Classical-quantum blocks in finite dimension. O represents operators on E
    and R real scalars. The matrix model supplies the trace, direct-sum trace-norm
    law, positive cone and elementary arithmetic. The proofs move blocks, derive
    preservation of the E marginal, and transport *every* admissible POVM.
    No hypothesis asserts security or invariance under the block permutation. -/
namespace PTGCQ
open PTGITS

structure Model (O R : Type) where
  zeroOp : O
  idOp : O
  addOp : O → O → O
  subOp : O → O → O
  mulOp : O → O → O
  positive : O → Prop
  share : O → Nat → O
  realTrace : O → R
  traceNorm : O → R
  zero : R
  one : R
  add : R → R → R
  half : R → R
  op_swap : ∀ a b z, addOp b (addOp a z) = addOp a (addOp b z)
  scalar_swap : ∀ a b z, add b (add a z) = add a (add b z)

def marginal [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (rho : C → B → O) (c : C) : O :=
  reduceCells m.addOp m.zeroOp alphabet.cells (rho c)

theorem marginal_push [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (rho : C → B → O) (f : C → BlockPerm B) (c : C) :
    marginal m alphabet (pushRows f rho) c = marginal m alphabet rho c :=
  reduce_reindex alphabet (f c) m.addOp m.op_swap m.zeroOp _

/-- Partial trace over both classical registers leaves the marginal on E. -/
def eMarginal [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (tags : List C) (rho : C → B → O) : O :=
  reduceCells m.addOp m.zeroOp tags (marginal m alphabet rho)

theorem eMarginal_push [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (tags : List C) (rho : C → B → O) (f : C → BlockPerm B) :
    eMarginal m alphabet tags (pushRows f rho) = eMarginal m alphabet tags rho := by
  unfold eMarginal
  congr 1
  funext c
  exact marginal_push ..

/-- A normalized cq state, stored as subnormalized positive blocks. -/
def IsState [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (tags : List C) (rho : C → B → O) : Prop :=
  (∀ c b, m.positive (rho c b)) ∧
  reduceCells m.add m.zero tags (fun c => m.realTrace (marginal m alphabet rho c)) = m.one

theorem state_push [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (tags : List C) (rho : C → B → O) (f : C → BlockPerm B)
    (h : IsState m alphabet tags rho) : IsState m alphabet tags (pushRows f rho) := by
  refine ⟨fun c b => h.1 c ((f c).dec b), ?_⟩
  simpa only [marginal_push] using h.2

/-- Standard operator identity: norm of a block-diagonal direct sum is the
    sum of norms of all blocks, for an arbitrary operator array. -/
structure DirectSum [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (tags : List C) where
  jointTraceNorm : (C → B → O) → R
  directSumLaw : ∀ t, jointTraceNorm t =
    reduceCells m.add m.zero tags (fun c =>
      reduceCells m.add m.zero alphabet.cells (fun b => m.traceNorm (t c b)))

def distance [DecidableEq B] (m : Model O R) (alphabet : Alphabet B) (tags : List C)
    (joint : DirectSum m alphabet tags) (rho : C → B → O) : R :=
  m.half (joint.jointTraceNorm (fun c b =>
    m.subOp (rho c b) (m.share (marginal m alphabet rho c) alphabet.cells.length)))

theorem distance_push [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (tags : List C) (joint : DirectSum m alphabet tags) (rho : C → B → O)
    (f : C → BlockPerm B) :
    distance m alphabet tags joint (pushRows f rho) = distance m alphabet tags joint rho := by
  unfold distance
  rw [joint.directSumLaw, joint.directSumLaw]
  congr 2
  funext c
  rw [marginal_push]
  exact reduce_reindex alphabet (f c) m.add m.scalar_swap m.zero
    (fun b => m.traceNorm (m.subOp (rho c b) (m.share _ _)))

/-- For each public tag, one positive effect per possible answer, adding to I. -/
def IsPOVM [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (effects : C → B → O) : Prop :=
  (∀ c b, m.positive (effects c b)) ∧ (∀ c, marginal m alphabet effects c = m.idOp)

theorem povm_push [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (effects : C → B → O) (f : C → BlockPerm B) (h : IsPOVM m alphabet effects) :
    IsPOVM m alphabet (pushRows f effects) := by
  exact ⟨fun c b => h.1 c ((f c).dec b), fun c => (marginal_push ..).trans (h.2 c)⟩

/-- The Born guessing score sums Re Tr(effect × subnormalized state block).
    For positive effects and state blocks that trace is real and nonnegative. -/
def bornScore [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (tags : List C) (rho effects : C → B → O) : R :=
  reduceCells m.add m.zero tags (fun c => reduceCells m.add m.zero alphabet.cells
    (fun b => m.realTrace (m.mulOp (effects c b) (rho c b))))

theorem born_push [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (tags : List C) (rho effects : C → B → O) (f : C → BlockPerm B) :
    bornScore m alphabet tags (pushRows f rho) (pushRows f effects) =
      bornScore m alphabet tags rho effects := by
  unfold bornScore
  congr 1
  funext c
  exact reduce_reindex alphabet (f c) m.add m.scalar_swap m.zero
    (fun b => m.realTrace (m.mulOp (effects c b) (rho c b)))

theorem reversePush (f : C → BlockPerm B) (t : C → B → O) :
    pushRows (fun c => (f c).inverse) (pushRows f t) = t := by
  funext c b
  simp only [pushRows, BlockPerm.inverse, BlockPerm.dec_enc]

/-- The full set of success probabilities obtained by admissible measurements.
    Set equality implies equality of the suprema, without an attainment premise. -/
def attainable [DecidableEq B] (m : Model O R) (alphabet : Alphabet B) (tags : List C)
    (rho : C → B → O) (r : R) : Prop :=
  ∃ effects, IsPOVM m alphabet effects ∧ bornScore m alphabet tags rho effects = r

theorem attainable_push [DecidableEq B] (m : Model O R) (alphabet : Alphabet B)
    (tags : List C) (rho : C → B → O) (f : C → BlockPerm B) :
    attainable m alphabet tags (pushRows f rho) = attainable m alphabet tags rho := by
  funext r
  apply propext
  constructor
  · rintro ⟨effects, povm, score⟩
    let g := fun c => (f c).inverse
    refine ⟨pushRows g effects, povm_push m alphabet effects g povm, ?_⟩
    have eq := born_push m alphabet tags (pushRows f rho) effects g
    rw [show pushRows g (pushRows f rho) = rho from reversePush f rho] at eq
    exact eq.trans score
  · rintro ⟨effects, povm, score⟩
    exact ⟨pushRows f effects, povm_push m alphabet effects f povm,
      (born_push m alphabet tags rho effects f).trans score⟩

theorem sequence_cq (machine : Machine S B) (n : Nat) [DecidableEq (Word B n)]
    (m : Model O R) (alphabet : Alphabet (Word B n)) (tags : List C)
    (joint : DirectSum m alphabet tags) (rho : C → Word B n → O)
    (initial : C → S) (supremum : (R → Prop) → R) :
    let moved := pushRows (fun c => causalPermutation machine n (initial c)) rho
    distance m alphabet tags joint moved = distance m alphabet tags joint rho ∧
    supremum (attainable m alphabet tags moved) = supremum (attainable m alphabet tags rho) := by
  exact ⟨distance_push .., congrArg supremum (attainable_push ..)⟩

end PTGCQ

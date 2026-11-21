import CTRProfile
import Reduction

/-! Oracle-transcript bridge specific to CTR_DRBG. Key material is excluded
from the parameter of a local test. A concrete AES segment can nevertheless
continue on a numerically known next state computed from answers. -/
namespace CTRHybrid
open CTRProfile
open PTG3.Reduction (total)

inductive Kind | prepare | returnBlock
  deriving DecidableEq

structure Four where
  first : Word
  second : Word
  third : Word
  fourth : Word
  deriving DecidableEq

/-- Four consecutive points. The extra fourth response for a prepare step is
ignored, allowing a single four-query bound for both kinds. -/
def answers (oracle : Word → Word) (v : Word) : Four :=
  ⟨oracle (inc v), oracle (inc (inc v)), oracle (inc (inc (inc v))),
    oracle (inc (inc (inc (inc v))))⟩

theorem distinct_query_points (v : Word) :
    let t := answers id v
    t.first ≠ t.second ∧ t.first ≠ t.third ∧ t.first ≠ t.fourth ∧
      t.second ≠ t.third ∧ t.second ≠ t.fourth ∧ t.third ≠ t.fourth := by
  dsimp [answers, inc]
  bv_decide

/-- The result of a segment can be computed without its secret key. -/
def finish (kind : Kind) (mask : State) (x : Four) : Option Word × State :=
  match kind with
  | .prepare => (none, xorState ⟨(x.first, x.second), x.third⟩ mask)
  | .returnBlock => (some x.first, xorState ⟨(x.second, x.third), x.fourth⟩ mask)

def segment (c : Cipher) (kind : Kind) (s mask : State) : Option Word × State :=
  finish kind mask (answers (c.encrypt s.key) s.counter)

def scheduled (c : Cipher) (s : State) (input : Option State) : Option Word × State :=
  match input with
  | none => segment c .returnBlock s zeroState
  | some mask =>
      let pre := (segment c .prepare s mask).2
      segment c .returnBlock pre mask

theorem actual_segments (c : Cipher) (s : State) (input : Option State) :
    scheduled c s input = (some (nistGenerate c s input).1, (nistGenerate c s input).2) := by
  cases input <;> rfl

/-- History is most-recent-first. The policy receives only released words;
the referee keeps the complete output and final state for scoring. -/
def execute (step : State → Option State → Option Word × State)
    (policy : List Word → Option State) (visible : Nat → Bool) :
    Nat → State → List Word → List Word × State
  | 0, s, _ => ([],s)
  | n+1, s, public =>
    let result := step s (policy public)
    let nextView := if visible n then result.1.toList ++ public else public
    let rest := execute step policy visible n result.2 nextView
    (result.1.toList ++ rest.1, rest.2)

theorem executions_refine (c : Cipher) (policy : List Word → Option State)
    (visible : Nat → Bool) (n : Nat) (s : State) (public : List Word) :
    execute (scheduled c) policy visible n s public =
      execute (fun old d => (some (nistGenerate c old d).1, (nistGenerate c old d).2))
        policy visible n s public := by
  have eq := funext fun old => funext fun d => actual_segments c old d
  rw [eq]

def segmentCount (c : Cipher) (policy : List Word → Option State) (visible : Nat → Bool) :
    Nat → State → List Word → Nat
  | 0, _, _ => 0
  | n+1, s, public =>
    let input := policy public
    let result := scheduled c s input
    (if input.isSome then 2 else 1) +
      segmentCount c policy visible n result.2
        (if visible n then result.1.toList ++ public else public)

theorem at_most_two_segments (c : Cipher) (policy : List Word → Option State)
    (visible : Nat → Bool) (n : Nat) (s : State) (public : List Word) :
    segmentCount c policy visible n s public ≤ 2*n := by
  induction n generalizing s public with
  | zero => simp [segmentCount]
  | succ n ih =>
    unfold segmentCount
    have h := ih ((scheduled c s (policy public)).2)
      (if visible n then (scheduled c s (policy public)).1.toList ++ public else public)
    cases hi : (policy public).isSome <;> simp only [hi, Bool.false_eq_true, if_false, if_true] <;> omega

/-- RF coordinates can be grouped as three independent state words and
one unexposed dummy word or a published word, depending on the segment. -/
def assemble (kind : Kind) (isolated : Word) (raw : State) : Four :=
  match kind with
  | .prepare => ⟨raw.key.1, raw.key.2, raw.counter, isolated⟩
  | .returnBlock => ⟨isolated, raw.key.1, raw.key.2, raw.counter⟩

def disassemble (kind : Kind) (a : Four) : Word × State :=
  match kind with
  | .prepare => (a.fourth, ⟨(a.first,a.second),a.third⟩)
  | .returnBlock => (a.first, ⟨(a.second,a.third),a.fourth⟩)

theorem independent_words_coordinate_bijection (kind : Kind) (w : Word) (s : State)
    (answers : Four) :
    disassemble kind (assemble kind w s) = (w,s) ∧
    assemble kind (disassemble kind answers).1 (disassemble kind answers).2 = answers := by
  cases kind <;> exact ⟨rfl,rfl⟩

theorem ideal_segment_shape (kind : Kind) (mask raw : State) (isolated : Word) :
    finish kind mask (assemble kind isolated raw) =
      ((match kind with | .prepare => none | .returnBlock => some isolated),
        xorState raw mask) := by
  cases kind <;> rfl

/-- For each value of the public result, a uniform raw triple produces one
preimage per next state. This verifies renewal at an RF prefix cut. -/
theorem ideal_renews_key (kind : Kind) (mask : State) (isolated : Word)
    (allStates : List State) (nd : allStates.Nodup) (complete : ∀ s, s ∈ allStates)
    (k : Key) (v : Word) (weight : Nat) :
    total allStates (fun raw =>
      if (finish kind mask (assemble kind isolated raw)).2 = ⟨k,v⟩ then weight else 0) =
    weight := by
  simp only [ideal_segment_shape]
  exact PTG3.Reduction.masked_target_fiber allStates nd complete
    (fun h x => xorState x h) (fun h x => xorState x h)
    (fun h x => mask_cancels x h) (fun h x => mask_cancels x h) mask ⟨k,v⟩ weight

def allDistinct (x : Four) : Bool :=
  decide (x.first ≠ x.second ∧ x.first ≠ x.third ∧ x.first ≠ x.fourth ∧
    x.second ≠ x.third ∧ x.second ≠ x.fourth ∧ x.third ≠ x.fourth)

structure Row where
  kind : Kind
  mask : State
  /-- Number of successful continuations on a fixed denominator.
  The public prefix, private test coins and side information can be carried
  by this closure, independently of the uniform segment key. -/
  continuation : Option Word × State → Nat

def score (r : Row) (t : Four) : Nat := r.continuation (finish r.kind r.mask t)

/-- Complete the *actual* pending request, then run its real suffix. This
continuation receives the known state from the oracle answers and never
receives the hidden challenge key. The referee can inspect the terminal state. -/
def realContinuation (c : Cipher) (policy : List Word → Option State) (visible : Nat → Bool)
    (n : Nat) (public : List Word) (payoff : List Word × State → Nat)
    (result : Option Word × State) : Nat :=
  let pub := if visible n then result.1.toList ++ public else public
  let rest := execute (scheduled c) policy visible n result.2 pub
  payoff (result.1.toList ++ rest.1, rest.2)

def realRequestRow (c : Cipher) (policy : List Word → Option State) (visible : Nat → Bool)
    (n : Nat) (public : List Word) (payoff : List Word × State → Nat) : Row :=
  let cont := realContinuation c policy visible n public payoff
  match policy public with
  | none => ⟨.returnBlock, zeroState, cont⟩
  | some mask => ⟨.prepare, mask,
      fun pre => cont (segment c .returnBlock pre.2 mask)⟩

/-- Local AES challenger plus the known-key suffix is exactly the full specified
experiment, for any fixed history, starting counter, payoff and secret key. -/
theorem concrete_request_test (c : Cipher) (policy : List Word → Option State)
    (visible : Nat → Bool) (n : Nat) (public : List Word) (payoff : List Word × State → Nat)
    (s : State) :
    score (realRequestRow c policy visible n public payoff)
      (answers (c.encrypt s.key) s.counter) =
    payoff (execute (scheduled c) policy visible (n+1) s public) := by
  cases h : policy public <;>
    simp [realRequestRow, h, score, realContinuation, execute, scheduled, segment]

/-- The cut just after the optional pre-update is also an ordinary local
test, with the same mask held constant through the emit-and-update step. -/
theorem concrete_post_test (c : Cipher) (mask : State) (cont : Option Word × State → Nat)
    (s : State) :
    let r : Row := ⟨.returnBlock, mask, cont⟩
    score r (answers (c.encrypt s.key) s.counter) = cont (segment c .returnBlock s mask) := by rfl

def permAtCut (tuples : List Four) (r : Row) : Nat :=
  total tuples (fun t => if allDistinct t then score r t else 0)

def rfAtCut (tuples : List Four) (r : Row) : Nat := total tuples (score r)

theorem switching_for_ctr_continuation (tuples : List Four) (r : Row) :
    permAtCut tuples r ≤ rfAtCut tuples r :=
  PTG3.Reduction.retained_success_count tuples allDistinct (score r)

private theorem sumScale (xs : List α) (f : α → Nat) (n : Nat) :
    n * total xs f = total xs (fun x => n * f x) := by
  induction xs with
  | nil => simp [total]
  | cons x xs ih => simp [total, Nat.mul_add, ih]

private theorem sumPlus (xs : List α) (f g : α → Nat) :
    total xs (fun x => f x + g x) = total xs f + total xs g := by
  induction xs with
  | nil => simp [total]
  | cons x xs ih => simp [total, ih]; omega

/- For a causally chosen sequence of a fixed number of AES segments, the
   following construction derives the counts rather than requiring cut
   identities. Both autonomous and always-present request profiles are
   specializations. Hist is a referee/observer state. Its action must only
   depend on what the selected additional-input policy is allowed to see. -/
structure SegmentObserver (Hist : Type) where
  select : Hist → Kind × State
  record : Hist → Option Word → Hist
  win : Hist → State → Bool
  omitPrepare : Hist → Bool := fun _ => false

def skipAt (obs : SegmentObserver H) (h : H) : Bool :=
  obs.omitPrepare h && decide ((obs.select h).1 = .prepare)

def concreteRun (c : Cipher) (obs : SegmentObserver Hist) : Nat → Hist → State → Bool
  | 0, hist, s => obs.win hist s
  | n+1, hist, s =>
    let cmd := obs.select hist
    let result := if skipAt obs hist then (none, s) else segment c cmd.1 s cmd.2
    concreteRun c obs n (obs.record hist result.1) result.2

def stateSum (words : List Word) (keys : List Key) (f : State → Nat) : Nat :=
  total words (fun v => total keys (fun k => f ⟨k,v⟩))

def runCount (words : List Word) (keys : List Key) (c : Cipher)
    (obs : SegmentObserver Hist) (n : Nat) (h : Hist) : Nat :=
  stateSum words keys (fun s => (concreteRun c obs n h s).toNat)

def isolatedView : Kind → Word → Option Word
  | .prepare, _ => none
  | .returnBlock, w => some w

/-- An RF segment chooses one isolated word and an independent fresh state.
The isolated word of a prepare segment is a dummy uniform word (ignored). -/
def idealCount (words : List Word) (keys : List Key) (obs : SegmentObserver Hist) :
    Nat → Hist → Nat
  | 0, hist => stateSum words keys (fun s => (obs.win hist s).toNat)
  | n+1, hist => total words (fun y => idealCount words keys obs n
      (obs.record hist (isolatedView (obs.select hist).1 y)))

def localTest (c : Cipher) (obs : SegmentObserver Hist) (n : Nat) (h : Hist) (r : Four) : Bool :=
  let cmd := obs.select h
  let out := finish cmd.1 cmd.2 r
  concreteRun c obs n (obs.record h out.1) out.2

/-- Reindex all four RF words by one isolated word and the desired new state.
Both directions are explicit even for a history-dependent known XOR mask. -/
def replyFromIdeal (kind : Kind) (mask : State) (w : Word) (newState : State) : Four :=
  assemble kind w (xorState newState mask)

def idealFromReply (kind : Kind) (mask : State) (r : Four) : Word × State :=
  let t := disassemble kind r
  (t.1, xorState t.2 mask)

theorem reply_reindex (kind : Kind) (mask newState : State) (w : Word) (r : Four) :
    idealFromReply kind mask (replyFromIdeal kind mask w newState) = (w,newState) ∧
    replyFromIdeal kind mask (idealFromReply kind mask r).1 (idealFromReply kind mask r).2 = r := by
  have left := (independent_words_coordinate_bijection kind w (xorState newState mask) r).1
  have right := (independent_words_coordinate_bijection kind w newState r).2
  constructor
  · simp [idealFromReply, replyFromIdeal, left, mask_cancels]
  · simp only [idealFromReply, replyFromIdeal, mask_cancels]; exact right

def draws (words : List Word) (keys : List Key) (kind : Kind) (mask : State)
    (f : Four → Nat) : Nat :=
  total words (fun w => stateSum words keys (fun s => f (replyFromIdeal kind mask w s)))

/-- In the numerator for a random permutation only distinct answers survive.
For full, duplicate-free lists the denominator is D=(2^128)_4. The scaling
d is D times a numerator slack with the uniform-key denominator. -/
def LocalPermutationBound (words : List Word) (keys : List Key) (c : Cipher)
    (eligible : Word → (Four → Bool) → Prop) (D d : Nat) : Prop :=
  ∀ kind mask v test, eligible v test →
    D * total keys (fun k => (test (answers (c.encrypt k) v)).toNat) ≤
    d + keys.length * draws words keys kind mask
      (fun t => if allDistinct t then (test t).toNat else 0)

private theorem draws_mono (words : List Word) (keys : List Key) (kind : Kind) (mask : State)
    (f g : Four → Nat) (le : ∀ t, f t ≤ g t) :
    draws words keys kind mask f ≤ draws words keys kind mask g := by
  apply PTG3.Reduction.total_mono; intro w
  apply PTG3.Reduction.total_mono; intro v
  apply PTG3.Reduction.total_mono; intro k
  exact le _

private theorem sumConst (xs : List α) (k : Nat) :
    total xs (fun _ => k) = xs.length * k := by
  induction xs with
  | nil => simp [total]
  | cons x xs ih => simp [total, ih, Nat.succ_mul, Nat.add_comm]

theorem ideal_reply_runs_suffix (words : List Word) (keys : List Key) (c : Cipher)
    (obs : SegmentObserver Hist) (n : Nat) (h : Hist) :
    draws words keys (obs.select h).1 (obs.select h).2 (fun t => (localTest c obs n h t).toNat) =
    total words (fun w => runCount words keys c obs n
      (obs.record h (isolatedView (obs.select h).1 w))) := by
  unfold draws runCount
  apply PTG3.Reduction.total_congr; intro w
  unfold stateSum
  apply PTG3.Reduction.total_congr; intro v
  apply PTG3.Reduction.total_congr; intro k
  simp only [localTest, replyFromIdeal, ideal_segment_shape, mask_cancels]
  cases hkind : (obs.select h).1 <;> rfl

/-- Exact one-step probability transfer for all histories. Only a PRP test
of the actual local continuation (whose eligibility is external) is used. -/
theorem derived_step (words : List Word) (keys : List Key) (c : Cipher)
    (obs : SegmentObserver Hist) (eligible : Word → (Four → Bool) → Prop) (D d n : Nat) (h : Hist)
    (prp : LocalPermutationBound words keys c eligible D d)
    (cost : ∀ v, eligible v (localTest c obs n h))
    (capacity : D ≤ words.length * keys.length * words.length) :
    D * runCount words keys c obs (n+1) h ≤
    words.length * d + (words.length * keys.length) * total words
      (fun w => runCount words keys c obs n (obs.record h (isolatedView (obs.select h).1 w))) := by
  cases omitted : skipAt obs h with
  | true =>
    have hk : (obs.select h).1 = .prepare := by
      unfold skipAt at omitted
      simp only [Bool.and_eq_true, decide_eq_true_eq] at omitted
      exact omitted.2
    have eq : runCount words keys c obs (n+1) h = runCount words keys c obs n (obs.record h none) := by
      simp only [runCount, stateSum, concreteRun, omitted, if_true]
    rw [eq]; simp only [hk, isolatedView, sumConst, ← Nat.mul_assoc]
    have hl := Nat.mul_le_mul_right (runCount words keys c obs n (obs.record h none)) capacity
    omega
  | false =>
    let kind := (obs.select h).1
    let mask := (obs.select h).2
    let test := localTest c obs n h
    let U := draws words keys kind mask (fun t => (test t).toNat)
    have restrict_le : draws words keys kind mask
        (fun t => if allDistinct t then (test t).toNat else 0) ≤ U := by
      apply draws_mono
      intro t; cases allDistinct t <;> simp
    have row (v : Word) :
        D * total keys (fun k => (test (answers (c.encrypt k) v)).toNat) ≤ d + keys.length*U :=
      Nat.le_trans (prp kind mask v test (cost v))
        (Nat.add_le_add_left (Nat.mul_le_mul_left _ restrict_le) _)
    have sum := PTG3.Reduction.total_mono words row
    rw [← sumScale, sumConst] at sum
    have ex : U = total words (fun w => runCount words keys c obs n
        (obs.record h (isolatedView (obs.select h).1 w))) :=
      ideal_reply_runs_suffix words keys c obs n h
    rw [Nat.mul_add, ← Nat.mul_assoc, ex] at sum
    simpa only [runCount, stateSum, concreteRun, omitted, Bool.false_eq_true, if_false, test, localTest, segment] using sum

/-- Counts use denominators S=|words|*|keys| for the real initial state
and S*|words|^n for n ideal isolated words and a uniform terminal state. -/
def epochSlack (D S M d : Nat) : Nat → Nat
  | 0 => 0
  | n+1 => D^n * (M*d) + S*M * epochSlack D S M d n

/-- End-to-end bound with all cuts summed constructively. No cut masses,
no inequalities about the whole generator and no trajectory accounting
identities are premises. -/
theorem direct_epoch (words : List Word) (keys : List Key) (c : Cipher)
    (obs : SegmentObserver Hist) (eligible : Word → (Four → Bool) → Prop)
    (D d horizon n : Nat) (h : Hist)
    (prp : LocalPermutationBound words keys c eligible D d)
    (cost : ∀ j, j < horizon → ∀ hist v, eligible v (localTest c obs j hist))
    (within : n ≤ horizon) (capacity : D ≤ words.length * keys.length * words.length) :
    D^n * runCount words keys c obs n h ≤
      (words.length * keys.length)^n * idealCount words keys obs n h +
      epochSlack D (words.length * keys.length) words.length d n := by
  let S := words.length * keys.length
  let M := words.length
  induction n generalizing h with
  | zero => simp [runCount, concreteRun, idealCount, epochSlack]
  | succ n ih =>
    have step := Nat.mul_le_mul_left (D^n)
      (derived_step words keys c obs eligible D d n h prp (cost n within h) capacity)
    let upd := fun w => obs.record h (isolatedView (obs.select h).1 w)
    have rec := PTG3.Reduction.total_mono words (fun w =>
      ih (upd w) (Nat.le_trans (Nat.le_succ _) within))
    rw [← sumScale, sumPlus, ← sumScale, sumConst] at rec
    rw [Nat.mul_add] at step
    change D^n * (D * runCount words keys c obs (n+1) h) ≤
      D^n * (M*d) + D^n * (S * total words (fun w => runCount words keys c obs n (upd w))) at step
    rw [Nat.mul_left_comm (D^n) S] at step
    have both := Nat.le_trans step (Nat.add_le_add_left (Nat.mul_le_mul_left S rec) _)
    change D^(n+1)*runCount words keys c obs (n+1) h ≤
      S^(n+1)*total words (fun w => idealCount words keys obs n (upd w)) +
        (D^n*(M*d) + S*M*epochSlack D S M d n)
    rw [Nat.mul_add] at both
    simp only [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm,
      Nat.add_assoc, Nat.add_comm, Nat.add_left_comm, S, M] at both ⊢
    exact both


/-- The referee records generated blocks. A hidden block can enter the
referee's final scoring state; an adaptive choice is restricted in the
concrete experiment to the public projection of that state. -/
structure RequestObserver (H : Type) where
  record : H → Word → H
  win : H → State → Bool

def nistRun (c : Cipher) (o : RequestObserver H) (choose : H → Option State) :
    Nat → H → State → Bool
  | 0, h, s => o.win h s
  | n+1, h, s =>
    let r := nistGenerate c s (choose h)
    nistRun c o choose n (o.record h r.1) r.2

def autonomousObserver (o : RequestObserver H) : SegmentObserver H where
  select _ := (.returnBlock, zeroState)
  record h out := match out with
    | none => h
    | some y => o.record h y
  win := o.win

inductive Pending (H : Type) where
  | beginRequest : H → Pending H
  | finishRequest : H → State → Pending H

def presentObserver (o : RequestObserver H) (choose : H → State) : SegmentObserver (Pending H) where
  select
    | .beginRequest old => (.prepare, choose old)
    | .finishRequest _ mask => (.returnBlock, mask)
  record h out := match h with
    | .beginRequest old => .finishRequest old (choose old)
    | .finishRequest old _ =>
      match out with
      | none => .beginRequest old
      | some y => .beginRequest (o.record old y)
  win h := match h with
    | .beginRequest old => o.win old
    | .finishRequest old _ => o.win old

theorem concrete_autonomous (c : Cipher) (o : RequestObserver H) (n : Nat) (h : H) (s : State) :
    concreteRun c (autonomousObserver o) n h s = nistRun c o (fun _ => none) n h s := by
  induction n generalizing h s with
  | zero => rfl
  | succ n ih =>
    change concreteRun c (autonomousObserver o) n
      (o.record h (nistGenerate c s none).1) (nistGenerate c s none).2 = _
    exact ih _ _

theorem concrete_present (c : Cipher) (o : RequestObserver H) (choose : H → State)
    (n : Nat) (h : H) (s : State) :
    concreteRun c (presentObserver o choose) (2*n) (.beginRequest h) s =
      nistRun c o (fun old => some (choose old)) n h s := by
  induction n generalizing h s with
  | zero => rfl
  | succ n ih =>
    rw [Nat.mul_succ]
    change concreteRun c (presentObserver o choose) (2*n)
      (.beginRequest (o.record h (nistGenerate c s (some (choose h))).1))
      (nistGenerate c s (some (choose h))).2 = _
    exact ih _ _

/-- Isolated, independent delivered outputs followed by an independent
terminal state, including tests that reveal that terminal state. -/
def independentScore (words : List Word) (keys : List Key) (o : RequestObserver H) : Nat → H → Nat
  | 0, h => stateSum words keys (fun s => (o.win h s).toNat)
  | n+1, h => total words (fun y => independentScore words keys o n (o.record h y))

theorem ideal_autonomous (words : List Word) (keys : List Key) (o : RequestObserver H)
    (n : Nat) (h : H) :
    idealCount words keys (autonomousObserver o) n h = independentScore words keys o n h := by
  induction n generalizing h with
  | zero => rfl
  | succ n ih =>
    apply PTG3.Reduction.total_congr; intro w
    exact ih _

theorem ideal_present (words : List Word) (keys : List Key) (o : RequestObserver H)
    (choose : H → State) (n : Nat) (h : H) :
    idealCount words keys (presentObserver o choose) (2*n) (.beginRequest h) =
      words.length^n * independentScore words keys o n h := by
  induction n generalizing h with
  | zero => simp [idealCount, independentScore, presentObserver]
  | succ n ih =>
    rw [Nat.mul_succ]
    change total words (fun _ => total words (fun y =>
      idealCount words keys (presentObserver o choose) (2*n) (.beginRequest (o.record h y)))) = _
    simp only [ih, ← sumScale, sumConst]
    simp [independentScore, Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

theorem autonomous_end_to_end (words : List Word) (keys : List Key) (c : Cipher)
    (o : RequestObserver H) (eligible : Word → (Four → Bool) → Prop)
    (D d N : Nat) (h : H) (prp : LocalPermutationBound words keys c eligible D d)
    (cost : ∀ j, j < N → ∀ hist v, eligible v (localTest c (autonomousObserver o) j hist)) (capacity : D ≤ words.length * keys.length * words.length) :
    D^N * stateSum words keys (fun s => (nistRun c o (fun _ => none) N h s).toNat) ≤
      (words.length * keys.length)^N * independentScore words keys o N h +
        epochSlack D (words.length * keys.length) words.length d N := by
  have b := direct_epoch words keys c (autonomousObserver o) eligible D d N N h prp cost (by omega) capacity
  simpa only [runCount, concrete_autonomous, ideal_autonomous] using b

theorem present_end_to_end (words : List Word) (keys : List Key) (c : Cipher)
    (o : RequestObserver H) (choose : H → State) (eligible : Word → (Four → Bool) → Prop)
    (D d N : Nat) (h : H) (prp : LocalPermutationBound words keys c eligible D d)
    (cost : ∀ j, j < 2*N → ∀ hist v, eligible v (localTest c (presentObserver o choose) j hist)) (capacity : D ≤ words.length * keys.length * words.length) :
    D^(2*N) * stateSum words keys (fun s => (nistRun c o (fun old => some (choose old)) N h s).toNat) ≤
      (words.length * keys.length)^(2*N) *
        (words.length^N * independentScore words keys o N h) +
        epochSlack D (words.length * keys.length) words.length d (2*N) := by
  have b := direct_epoch words keys c (presentObserver o choose) eligible D d (2*N) (2*N)
    (.beginRequest h) prp cost (by omega) capacity
  simpa only [runCount, concrete_present, ideal_present] using b

/-- Two public accounting slots per request, of which a null pre-update uses
no oracle call and preserves the entire live state. The stored mask is shared
by both halves of a present request. -/
def mixedObserver (o : RequestObserver H) (choose : H → Option State) : SegmentObserver (Pending H) :=
  { presentObserver o (fun h => (choose h).getD zeroState) with
    omitPrepare := fun stage => match stage with
      | .beginRequest h => (choose h).isNone
      | .finishRequest _ _ => false }

theorem concrete_mixed (c : Cipher) (o : RequestObserver H) (choose : H → Option State)
    (n : Nat) (h : H) (s : State) :
    concreteRun c (mixedObserver o choose) (2*n) (.beginRequest h) s = nistRun c o choose n h s := by
  induction n generalizing h s with
  | zero => rfl
  | succ n ih =>
    rw [Nat.mul_succ]
    cases eq : choose h with
    | none =>
      have same := ih (o.record h (nistGenerate c s none).1) (nistGenerate c s none).2
      conv => rhs; unfold nistRun; rw [eq]
      simpa only [concreteRun, mixedObserver, presentObserver, skipAt, eq, Option.isNone,
          Bool.true_and, Bool.false_and, decide_true, if_true, Bool.false_eq_true, if_false,
          Option.getD] using same
    | some d =>
      have same := ih (o.record h (nistGenerate c s (some d)).1) (nistGenerate c s (some d)).2
      conv => rhs; unfold nistRun; rw [eq]
      simpa only [concreteRun, mixedObserver, presentObserver, skipAt, eq, Option.isNone,
          Bool.true_and, Bool.false_and, decide_true, if_true, Bool.false_eq_true, if_false,
          Option.getD] using same

theorem ideal_mixed (words : List Word) (keys : List Key) (o : RequestObserver H)
    (choose : H → Option State) (n : Nat) (h : H) :
    idealCount words keys (mixedObserver o choose) (2*n) (.beginRequest h) =
      words.length^n * independentScore words keys o n h := by
  induction n generalizing h with
  | zero => simp [idealCount, independentScore, mixedObserver, presentObserver]
  | succ n ih =>
    rw [Nat.mul_succ]
    change total words (fun _ => total words (fun y =>
      idealCount words keys (mixedObserver o choose) (2*n) (.beginRequest (o.record h y)))) = _
    simp only [ih, ← sumScale, sumConst]
    simp [independentScore, Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

/-- Full one-block profile for N requests, with arbitrary adaptive masks and
a history-dependent choice between absent and present additional input.
A known input is represented by its observer policy; the boolean referee
may use the final state and any legitimately disclosed inputs or outputs. -/
theorem mixed_end_to_end (words : List Word) (keys : List Key) (c : Cipher)
    (o : RequestObserver H) (choose : H → Option State) (eligible : Word → (Four → Bool) → Prop)
    (D d N : Nat) (h : H) (prp : LocalPermutationBound words keys c eligible D d)
    (cost : ∀ j, j < 2*N → ∀ hist v, eligible v (localTest c (mixedObserver o choose) j hist))
    (capacity : D ≤ words.length * keys.length * words.length) :
    D^(2*N) * stateSum words keys (fun s => (nistRun c o choose N h s).toNat) ≤
      (words.length * keys.length)^(2*N) *
        (words.length^N * independentScore words keys o N h) +
        epochSlack D (words.length * keys.length) words.length d (2*N) := by
  have b := direct_epoch words keys c (mixedObserver o choose) eligible D d (2*N) (2*N)
    (.beginRequest h) prp cost (by omega) capacity
  simpa only [runCount, concrete_mixed, ideal_mixed] using b

end CTRHybrid

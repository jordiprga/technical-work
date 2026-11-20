import Std.Tactic.BVDecide

/-! One-block AES-256 CTR_DRBG without DF, with a 128-bit counter.
The independent loop and tuple descriptions share the public word representation
and a block cipher with its two inverse laws. No cryptographic hardness premise
is needed for their equivalence, recoverability, or the exclusion event. -/
namespace CTRProfile

abbrev Word := BitVec 128
abbrev Key := Word × Word

structure State where
  key : Key
  counter : Word
  deriving DecidableEq

structure Cipher where
  encrypt : Key → Word → Word
  decrypt : Key → Word → Word
  decryptEncrypt : ∀ k x, decrypt k (encrypt k x) = x
  encryptDecrypt : ∀ k y, encrypt k (decrypt k y) = y

def inc (x : Word) := x + 1
def dec (x : Word) := x - 1
def zeroState : State := ⟨(0, 0), 0⟩
def physical (a : Word) : State := ⟨(0, 0), a⟩

/-- Values are three complete words in standard high-to-low order. -/
def xorState (a b : State) : State :=
  ⟨(a.key.1 ^^^ b.key.1, a.key.2 ^^^ b.key.2), a.counter ^^^ b.counter⟩

/-- SP 800-90Ar1 §10.2.1.2 steps 1–2, also used for the generate loop.
The second component returns exactly the counter reached by that loop. -/
def encryptLoop (c : Cipher) (k : Key) (v : Word) : Nat → List Word × Word
  | 0 => ([], v)
  | n + 1 =>
    let w := inc v
    let (tail, lastCounter) := encryptLoop c k w n
    (c.encrypt k w :: tail, lastCounter)

def nistUpdate (c : Cipher) (s provided : State) : State :=
  let words := (encryptLoop c s.key s.counter 3).1
  ⟨(words[0]! ^^^ provided.key.1, words[1]! ^^^ provided.key.2),
    words[2]! ^^^ provided.counter⟩

/-- §10.2.1.5.1, already-padded 384-bit inputs and exactly 128 requested bits. -/
def nistGenerate (c : Cipher) (s : State) (input : Option State) : Word × State :=
  let pre := match input with
    | none => s
    | some d => nistUpdate c s d
  let (words, v) := encryptLoop c pre.key pre.counter 1
  (words[0]!, nistUpdate c ⟨pre.key, v⟩ (input.getD zeroState))

/-- The AIS tuple independently describes its request, output, and transition maps. -/
def rawTriple (c : Cipher) (s : State) : State :=
  ⟨(c.encrypt s.key (inc s.counter),
    c.encrypt s.key (inc (inc s.counter))),
    c.encrypt s.key (inc (inc (inc s.counter)))⟩

def tupleRequest (c : Cipher) (s : State) : Option State → State
  | none => s
  | some d => xorState (rawTriple c s) d

def tupleOutput (c : Cipher) (pre : State) : Word :=
  c.encrypt pre.key (inc pre.counter)

def tupleGenerate (c : Cipher) (s : State) (input : Option State) : Word × State :=
  let pre := tupleRequest c s input
  (tupleOutput c pre,
   xorState (rawTriple c ⟨pre.key, inc pre.counter⟩) (input.getD zeroState))

theorem update_refines (c : Cipher) (s d : State) :
    nistUpdate c s d = xorState (rawTriple c s) d := by rfl

theorem generate_refines (c : Cipher) (s : State) (d : Option State) :
    nistGenerate c s d = tupleGenerate c s d := by cases d <;> rfl

/-- A request above the interval returns no bits and no updated state. -/
def checkedGenerate (core : State → Option State → Word × State)
    (interval count : Nat) (s : State) (input : Option State) : Option (Word × State × Nat) :=
  if count > interval then none
  else let result := core s input
       some (result.1, result.2, count + 1)

theorem checked_refines (c : Cipher) (interval count : Nat) (s : State) (d : Option State) :
    checkedGenerate (nistGenerate c) interval count s d =
    checkedGenerate (tupleGenerate c) interval count s d := by
  have h := funext fun s => funext fun d => generate_refines c s d
  rw [h]

theorem reseed_required (c : Cipher) (interval count : Nat) (s : State) (d : Option State)
    (expired : count > interval) :
    checkedGenerate (nistGenerate c) interval count s d = none := by
  simp [checkedGenerate, expired]

theorem ctr_zero_present (c : Cipher) (s : State) :
    tupleRequest c s none = s ∧
    tupleRequest c s (some (physical 0)) = xorState (rawTriple c s) zeroState := by
  exact ⟨rfl, rfl⟩

theorem mask_cancels (a b : State) : xorState (xorState a b) b = a := by
  cases a with
  | mk ka va =>
    cases ka
    cases b with
    | mk kb vb =>
      cases kb
      simp [xorState, BitVec.xor_assoc]

theorem mask_switch (a b : State) : xorState a b = xorState b a := by
  simp [xorState, BitVec.xor_comm]

/-- For each previous state and fixed personalization/additional data,
every new state is attainable from one seed material value. -/
theorem seed_attainable (c : Cipher) (s target : State) :
    nistUpdate c s (xorState (rawTriple c s) target) = target := by
  rw [update_refines, mask_switch (rawTriple c s) (xorState (rawTriple c s) target),
      mask_switch (rawTriple c s) target, mask_cancels]

theorem seed_unique (c : Cipher) (s a b : State) (h : nistUpdate c s a = nistUpdate c s b) :
    a = b := by
  rw [update_refines, update_refines, mask_switch (rawTriple c s) a,
      mask_switch (rawTriple c s) b] at h
  simpa only [mask_cancels] using congrArg (fun x => xorState x (rawTriple c s)) h

/-- Undoing the publicly known mask on an exposed next state produces
three exact AES encryptions at consecutive counter inputs. -/
theorem exposed_triple (c : Cipher) (s : State) (input : Option State) :
    xorState (nistGenerate c s input).2 (input.getD zeroState) =
    rawTriple c ⟨(tupleRequest c s input).key, inc (tupleRequest c s input).counter⟩ := by
  rw [generate_refines]
  exact mask_cancels _ _

/-- Physical injection into V; both key words are left untouched by the mask. -/
theorem request_physical (c : Cipher) (s : State) (a : Word) :
    tupleRequest c s (some (physical a)) =
    ⟨(rawTriple c s).key, (rawTriple c s).counter ^^^ a⟩ := by
  simp [tupleRequest, xorState, physical, rawTriple]

def encode (c : Cipher) (s : State) (a : Word) : Word :=
  let g := rawTriple c s
  c.encrypt g.key (inc (g.counter ^^^ a))

def recover (c : Cipher) (s : State) (y : Word) : Word :=
  let g := rawTriple c s
  g.counter ^^^ dec (c.decrypt g.key y)

theorem physical_output (c : Cipher) (s : State) (a : Word) :
    (nistGenerate c s (some (physical a))).1 = encode c s a := by
  rw [generate_refines]
  simp [tupleGenerate, request_physical, tupleOutput, encode]

theorem inv_inc (v : Word) : dec (inc v) = v := by
  unfold dec inc
  bv_decide

theorem inc_inv (v : Word) : inc (dec v) = v := by
  unfold dec inc
  bv_decide

theorem increment_wrap : inc (0xffffffffffffffffffffffffffffffff : Word) = 0 := by
  decide

theorem undo_word_mask (v x : Word) : v ^^^ (v ^^^ x) = x := by
  simp [← BitVec.xor_assoc]

theorem recover_encode (c : Cipher) (s : State) (a : Word) :
    recover c s (encode c s a) = a := by
  simp [recover, encode, c.decryptEncrypt, inv_inc, undo_word_mask]

theorem encode_recover (c : Cipher) (s : State) (y : Word) :
    encode c s (recover c s y) = y := by
  simp [recover, encode, undo_word_mask, inc_inv, c.encryptDecrypt]

def firstNextKey (c : Cipher) (s : State) (a : Word) : Word :=
  (nistGenerate c s (some (physical a))).2.key.1

theorem first_key_equation (c : Cipher) (s : State) (a : Word) :
    firstNextKey c s a =
      c.encrypt (rawTriple c s).key (inc (inc ((rawTriple c s).counter ^^^ a))) := by
  unfold firstNextKey
  rw [generate_refines]
  unfold tupleGenerate
  rw [request_physical]
  simp [xorState, physical, Option.getD, rawTriple]

/-- The current state plus just one word of the subsequent state determine the output. -/
def recoverOutputFromStates (c : Cipher) (s : State) (c₁ : Word) : Word :=
  let k := (rawTriple c s).key
  c.encrypt k (dec (c.decrypt k c₁))

theorem two_snapshots_recover_output (c : Cipher) (s : State) (a : Word) :
    recoverOutputFromStates c s (firstNextKey c s a) =
    (nistGenerate c s (some (physical a))).1 := by
  simp [recoverOutputFromStates, first_key_equation, physical_output, encode,
        c.decryptEncrypt, inv_inc]

theorem two_snapshots_recover_input (c : Cipher) (s : State) (a : Word) :
    recover c s (recoverOutputFromStates c s (firstNextKey c s a)) = a := by
  rw [two_snapshots_recover_output, physical_output, recover_encode]

theorem consecutive_distinct (v : Word) :
    v ≠ inc v ∧ v ≠ inc (inc v) ∧ inc v ≠ inc (inc v) := by
  unfold inc
  bv_decide

theorem three_ciphertexts_distinct (c : Cipher) (k : Key) (v : Word) :
    c.encrypt k v ≠ c.encrypt k (inc v) ∧
    c.encrypt k v ≠ c.encrypt k (inc (inc v)) ∧
    c.encrypt k (inc v) ≠ c.encrypt k (inc (inc v)) := by
  have h := consecutive_distinct v
  have inj {x y : Word} (eq : c.encrypt k x = c.encrypt k y) : x = y := by
    simpa [c.decryptEncrypt] using congrArg (c.decrypt k) eq
  exact ⟨fun e => h.1 (inj e), fun e => h.2.1 (inj e), fun e => h.2.2 (inj e)⟩

/-- A single terminal state reveals two distinct words, each excluded for Y.
This event concerns the real cipher (permutativity only), even with secret A. -/
theorem one_snapshot_excludes_two (c : Cipher) (s : State) (a : Word) :
    let r := nistGenerate c s (some (physical a))
    r.1 ≠ r.2.key.1 ∧ r.1 ≠ r.2.key.2 ∧ r.2.key.1 ≠ r.2.key.2 := by
  dsimp only
  rw [generate_refines]
  let t := tupleRequest c s (some (physical a))
  simpa [t, tupleGenerate, tupleOutput, xorState, rawTriple, physical, Option.getD] using
    three_ciphertexts_distinct c t.key (inc t.counter)


/-- Successful Instantiate and Reseed for a right-padded optional input;
the two 4-tuples share this map. The administrative counter resets to 1. -/
def reseed (c : Cipher) (previous seed padded : State) : State × Nat :=
  (nistUpdate c previous (xorState seed padded), 1)

def instantiate (c : Cipher) (seed padded : State) : State × Nat :=
  reseed c zeroState seed padded

theorem reseed_bijection (c : Cipher) (previous padded target : State) :
    ∃ seed, reseed c previous seed padded = (target, 1) ∧
      ∀ other, reseed c previous other padded = (target, 1) → other = seed := by
  let seed := xorState (xorState (rawTriple c previous) target) padded
  have hs : reseed c previous seed padded = (target, 1) := by
    simp [reseed, seed, mask_cancels, seed_attainable]
  refine ⟨seed, hs, ?_⟩
  intro other ho
  have eq := congrArg Prod.fst (ho.trans hs.symm)
  have h := seed_unique c previous (xorState other padded) (xorState seed padded) eq
  simpa only [mask_cancels] using congrArg (fun x => xorState x padded) h

theorem instantiate_bijection (c : Cipher) (padded target : State) :
    ∃ seed, instantiate c seed padded = (target, 1) ∧
      ∀ other, instantiate c other padded = (target, 1) → other = seed :=
  reseed_bijection c zeroState padded target

/-- Known autonomous output, candidate key, and its unique compatible *prior*
counter. The converse below holds for any cipher permutation, so cannot by
itself prove the hardness of computing equivalent future outputs (§115). -/
def candidateState (c : Cipher) (y : Word) (k : Key) : State :=
  ⟨k, dec (c.decrypt k y)⟩

theorem candidate_compatible (c : Cipher) (y : Word) (k : Key) :
    (nistGenerate c (candidateState c y k) none).1 = y := by
  simp [generate_refines, tupleGenerate, tupleRequest, tupleOutput, candidateState,
        inc_inv, c.encryptDecrypt]

theorem candidate_recovers_state (c : Cipher) (s : State) :
    candidateState c (nistGenerate c s none).1 s.key = s := by
  cases s with
  | mk key counter =>
    simp [generate_refines, tupleGenerate, tupleRequest, tupleOutput, candidateState,
          c.decryptEncrypt, inv_inc]

theorem single_output_fiber (c : Cipher) (y : Word) (s : State) :
    (nistGenerate c s none).1 = y ↔ s = candidateState c y s.key := by
  constructor
  · intro h
    simpa only [h] using (candidate_recovers_state c s).symm
  · intro h
    conv => lhs; rw [h]
    exact candidate_compatible c y s.key

theorem candidate_injective (c : Cipher) (y : Word) (k l : Key)
    (h : candidateState c y k = candidateState c y l) : k = l :=
  congrArg State.key h

theorem state_influenced (c : Cipher) (s : State) (a b : Word)
    (h : firstNextKey c s a = firstNextKey c s b) : a = b := by
  have eq := congrArg (fun z => recover c s (recoverOutputFromStates c s z)) h
  simpa only [two_snapshots_recover_input] using eq

/-- A separating model for the scope of the structural evidence: this
permutation family ignores its key. Its one-output fiber is still full-sized,
but the next autonomous output is computable from the preceding output. -/
def identityCipher : Cipher :=
  ⟨fun _ x => x, fun _ y => y, fun _ _ => rfl, fun _ _ => rfl⟩

theorem fiber_size_is_insufficient (s : State) :
    let first := nistGenerate identityCipher s none
    (nistGenerate identityCipher first.2 none).1 = inc (inc (inc (inc first.1))) := by
  simp [generate_refines, tupleGenerate, tupleRequest, tupleOutput, rawTriple, xorState,
        zeroState, identityCipher]


/-- Two *new* autonomous blocks suffice for a 256-bit prediction challenge. -/
def nextTwo (c : Cipher) (s : State) : Word × Word :=
  let first := nistGenerate c s none
  (first.1, (nistGenerate c first.2 none).1)

/-- A finite code book whose entries each forecast the same two specified
blocks has at least one successful uniform guess for every covered state.
The code can stand for an equivalent predictor, without recovering the key. -/
theorem codebook_success {Code : Type} (c : Cipher) (s : State) (book : List Code)
    (forecast : Code → Word × Word)
    (covered : ∃ z, z ∈ book ∧ forecast z = nextTwo c s) :
    1 ≤ (book.filter fun z => decide (forecast z = nextTwo c s)).length := by
  obtain ⟨z, hz, correct⟩ := covered
  have mem : z ∈ book.filter (fun x => decide (forecast x = nextTwo c s)) :=
    List.mem_filter.mpr ⟨hz, by simp [correct]⟩
  cases filtered : book.filter (fun x => decide (forecast x = nextTwo c s)) with
  | nil => simp [filtered] at mem
  | cons head tail => simp

/-- Cross-multiplied bound: if hits/L ≤ 2^-246 and at least one code hits,
then the code space contains at least 2^246 entries. -/
theorem predictor_space_lower_bound (hits L : Nat) (hasOne : 1 ≤ hits)
    (upper : 2^246 * hits ≤ L) : 2^246 ≤ L := by
  have h := Nat.mul_le_mul_left (2^246) hasOne
  exact Nat.le_trans (by simpa using h) upper


/-- Counting certificate for the ideal-word probability of the observable
event: each excluded word occurs once in a uniform list of all words. -/
theorem two_word_count (c₁ c₂ : Word) (neq : c₁ ≠ c₂) (xs : List Word) :
    (xs.countP (fun y => y == c₁ || y == c₂)) = xs.count c₁ + xs.count c₂ := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    by_cases h₁ : x = c₁
    · subst x
      simp [List.countP_cons, List.count_cons, neq, ih, Nat.add_assoc, Nat.add_comm]
    · by_cases h₂ : x = c₂
      · subst x
        simp [List.countP_cons, List.count_cons, h₁, ih, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]
      · simp [List.countP_cons, List.count_cons, h₁, h₂, ih]

theorem uniform_event_has_two (c₁ c₂ : Word) (neq : c₁ ≠ c₂)
    (allWords : List Word) (once : ∀ w, allWords.count w = 1) :
    allWords.countP (fun y => y == c₁ || y == c₂) = 2 := by
  rw [two_word_count _ _ neq, once, once]

end CTRProfile

import Std

/- Finite counts for the CTR profile. Counts are natural numbers so that
   denominators and their normalization are explicit in the accompanying text. -/
namespace PTG3.Reduction

def total (xs : List α) (f : α → Nat) : Nat :=
  match xs with
  | [] => 0
  | x :: rest => f x + total rest f

theorem total_congr (xs : List α) {f g : α → Nat}
    (h : ∀ x, f x = g x) : total xs f = total xs g := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp [total, h x, ih]

private theorem total_zero (xs : List α) : total xs (fun _ => 0) = 0 := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp [total, ih]

private theorem total_add (xs : List α) (f g : α → Nat) :
    total xs (fun x => f x + g x) = total xs f + total xs g := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp only [total, ih]; omega

private theorem total_swap (xs : List α) (ys : List β) (a : α → β → Nat) :
    total xs (fun x => total ys (a x)) =
      total ys (fun y => total xs (fun x => a x y)) := by
  induction xs with
  | nil => simp [total, total_zero]
  | cons x xs ih => simp [total, total_add, ih]

private theorem total_point [DecidableEq α] (xs : List α) (v : α) (w : Nat)
    (hn : xs.Nodup) :
    total xs (fun x => if x = v then w else 0) = (if v ∈ xs then w else 0) := by
  induction xs with
  | nil => simp [total]
  | cons x xs ih =>
    obtain ⟨hx, hxs⟩ := List.nodup_cons.mp hn
    by_cases hh : x = v
    · subst x; simp [total, ih hxs, hx]
    · simp [total, ih hxs, hh, Ne.symm hh]

private def pairHit [DecidableEq α] [DecidableEq β]
    (f : α → β) (inv : β → Option α) (x : α) (y : β) : Nat :=
  if y = f x then (if inv y = some x then 1 else 0) else 0

private theorem pair_row [DecidableEq α] [DecidableEq β]
    (ys : List β) (hys : ys.Nodup) (allY : ∀ y, y ∈ ys)
    (f : α → β) (inv : β → Option α) (x : α) :
    total ys (pairHit f inv x) = (if inv (f x) = some x then 1 else 0) := by
  calc
    _ = total ys (fun y => if y = f x then
          (if inv (f x) = some x then 1 else 0) else 0) := by
      apply total_congr; intro y; by_cases h : y = f x <;> simp [pairHit, h]
    _ = _ := by rw [total_point ys (f x) _ hys]; simp [allY]

def inverted [DecidableEq β] (f : α → β) (inv : β → Option α) (y : β) : Nat :=
  match inv y with
  | none => 0
  | some x => if f x = y then 1 else 0

private theorem pair_col [DecidableEq α] [DecidableEq β]
    (xs : List α) (hxs : xs.Nodup) (allX : ∀ x, x ∈ xs)
    (f : α → β) (inv : β → Option α) (y : β) :
    total xs (fun x => pairHit f inv x y) = inverted f inv y := by
  cases hv : inv y with
  | none =>
    calc
      _ = total xs (fun _ => 0) := by
        apply total_congr; intro x; simp [pairHit, hv]
      _ = _ := by simp [total_zero, inverted, hv]
  | some z =>
    calc
      _ = total xs (fun x => if x = z then (if f z = y then 1 else 0) else 0) := by
        apply total_congr; intro x
        by_cases he : x = z
        · subst x; simp [pairHit, hv, eq_comm]
        · simp [pairHit, hv, he, Ne.symm he]
      _ = _ := by rw [total_point xs z _ hxs]; simp [allX, inverted, hv]

/-- Number of exactly recovered planted points equals number of uniformly
    addressed targets for which *any* preimage is returned. No injectivity. -/
theorem double_count [DecidableEq α] [DecidableEq β]
    (xs : List α) (ys : List β) (hx : xs.Nodup) (hy : ys.Nodup)
    (allX : ∀ x, x ∈ xs) (allY : ∀ y, y ∈ ys)
    (f : α → β) (inv : β → Option α) :
    total xs (fun x => if inv (f x) = some x then 1 else 0) =
      total ys (inverted f inv) := by
  calc
    _ = total xs (fun x => total ys (pairHit f inv x)) := by
      apply total_congr; intro x; exact (pair_row ys hy allY f inv x).symm
    _ = _ := total_swap xs ys (pairHit f inv)
    _ = _ := by apply total_congr; intro y; exact pair_col xs hx allX f inv y

/-- Fixed-coin identity extends to any finite distribution of independent coins
    represented by nonnegative integer weights. Equal domains in the CTR
    application give identical probability denominators on the two sides. -/
theorem randomized_double_count [DecidableEq α] [DecidableEq β]
    (xs : List α) (ys : List β) (hx : xs.Nodup) (hy : ys.Nodup)
    (allX : ∀ x, x ∈ xs) (allY : ∀ y, y ∈ ys)
    (coins : List ρ) (weight : ρ → Nat) (f : α → β) (inv : ρ → β → Option α) :
    total coins (fun r => weight r * total xs (fun x =>
      if inv r (f x) = some x then 1 else 0)) =
    total coins (fun r => weight r * total ys (inverted f (inv r))) := by
  apply total_congr; intro r
  rw [double_count xs ys hx hy allX allY f (inv r)]

theorem total_mono (xs : List α) {f g : α → Nat} (h : ∀ x, f x ≤ g x) :
    total xs f ≤ total xs g := by
  induction xs with
  | nil => exact Nat.le_refl _
  | cons x xs ih => exact Nat.add_le_add (h x) ih

/-- On a uniform tuple universe, keep only tuples with no repeated answers.
    The score can count winning continuations after the tuple has been seen.
    Dividing by the positive number of injective tuples gives the one-sided
    switching bound, including for events much rarer than a birthday collision. -/
theorem retained_success_count (tuples : List α) (retain : α → Bool) (wins : α → Nat) :
    total tuples (fun t => if retain t then wins t else 0) ≤ total tuples wins := by
  apply total_mono; intro t; cases retain t <;> simp

/-- Bound after a sequence of replacement steps. D is the number of distinct
    r-tuples, B the number of unrestricted tuples; all success probabilities
    and the PRP distinguishing allowance are scaled to a common denominator. -/
theorem success_hybrid (D B A : Nat) (hs : D ≤ B) (p : Nat → Nat) (n : Nat)
    (step : ∀ j, j < n → D * p j ≤ D * A + B * p (j + 1)) :
    D ^ n * p 0 ≤ B ^ n * (n * A + p n) := by
  induction n generalizing p with
  | zero => simp
  | succ n ih =>
    have h₀ := step 0 (Nat.zero_lt_succ n)
    have ht := ih (fun j => p (j + 1)) (fun j hj =>
      step (j + 1) (Nat.succ_lt_succ hj))
    have hp : D ^ (n + 1) ≤ B ^ (n + 1) := Nat.pow_le_pow_left hs _
    calc
      D ^ (n+1) * p 0 = D ^ n * (D * p 0) := by rw [Nat.pow_succ, Nat.mul_assoc]
      _ ≤ D ^ n * (D * A + B * p 1) := Nat.mul_le_mul_left _ h₀
      _ = D ^ (n+1) * A + B * (D ^ n * p 1) := by
        simp only [Nat.mul_add, Nat.pow_succ, Nat.mul_assoc, Nat.mul_left_comm]
      _ ≤ B ^ (n+1) * A + B * (B ^ n * (n * A + p (n+1))) :=
        Nat.add_le_add (Nat.mul_le_mul_right A hp) (Nat.mul_le_mul_left B ht)
      _ = B ^ (n+1) * ((n+1) * A + p (n+1)) := by
        simp only [Nat.pow_succ, Nat.succ_mul, Nat.mul_add, Nat.mul_assoc,
          Nat.mul_left_comm]
        omega

/-- Probability normalizations for a 256-bit AES key and 128-bit counter
    versus an unrestricted ordered triple of AES output blocks. -/
theorem aes_domain_sizes : (2 : Nat)^256 * 2^128 = (2^128)^3 := by decide

/-- Number of ordered selections of r objects without replacement. -/
def falling (m : Nat) : Nat → Nat
  | 0 => 1
  | r+1 => m * falling (m-1) r

private theorem sum_pointwise_const (xs : List α) (f : α → Nat) (v : Nat)
    (h : ∀ x, x ∈ xs → f x = v) : total xs f = xs.length * v := by
  induction xs with
  | nil => simp [total]
  | cons x xs ih =>
    rw [total, h x (by simp), ih (fun a ha => h a (by simp [ha]))]
    simp [Nat.succ_mul, Nat.add_comm]

def distinctPaths [DecidableEq α] (pool : List α) : Nat → Nat
  | 0 => 1
  | remaining + 1 => total pool (fun a => distinctPaths (pool.erase a) remaining)

theorem paths_falling [DecidableEq α] (pool : List α) (r : Nat) :
    distinctPaths pool r = falling pool.length r := by
  induction r generalizing pool with
  | zero => rfl
  | succ r ih =>
    unfold distinctPaths falling
    apply sum_pointwise_const
    intro a ha
    rw [ih, List.length_erase_of_mem ha]

/-- Count only continuations agreeing with a fixed tuple of guesses. -/
def hitPaths [DecidableEq α] (pool : List α) : List α → Nat
  | [] => 1
  | b :: bs => total pool (fun a => if a = b then hitPaths (pool.erase a) bs else 0)

theorem candidate_at_most_one [DecidableEq α] (pool target : List α) (h : pool.Nodup) :
    hitPaths pool target ≤ 1 := by
  induction target generalizing pool with
  | nil => exact Nat.le_refl _
  | cons b bs ih =>
    unfold hitPaths
    calc
      _ = total pool (fun a => if a = b then hitPaths (pool.erase b) bs else 0) := by
        apply total_congr; intro a; by_cases hab : a = b <;> simp [hab]
      _ = (if b ∈ pool then hitPaths (pool.erase b) bs else 0) := total_point _ _ _ h
      _ ≤ 1 := by split <;> first | exact ih (pool.erase b) (h.erase b) | omega

private theorem scale_total (n : Nat) (xs : List α) (f : α → Nat) :
    n * total xs f = total xs (fun x => n * f x) := by
  induction xs with
  | nil => simp [total]
  | cons x xs ih => simp [total, Nat.mul_add, ih]

/-- Transport a successful continuation through two laws in likelihood ratio
    at most n/d, using integer weights with common normalizations. -/
theorem seed_density_transfer (xs : List α) (actual ideal wins : α → Nat) (d n : Nat)
    (ratio : ∀ x, d * actual x ≤ n * ideal x) :
    d * total xs (fun x => actual x * wins x) ≤
      n * total xs (fun x => ideal x * wins x) := by
  rw [scale_total, scale_total]
  apply total_mono; intro x
  simp only [←Nat.mul_assoc]
  exact Nat.mul_le_mul_right _ (ratio x)

/-- Three ordered outputs at consecutive counter positions. -/
def triple (inc : w → w) (oracle : w → w) (v : w) : w × w × w :=
  (oracle (inc v), oracle (inc (inc v)), oracle (inc (inc (inc v))))

/-- The inverter only sees the triple. The oracle verifier privately knows v.
    The sampling proof instantiates checks with three as-yet-unused inputs. -/
def accepts [DecidableEq w] (inc : w → w) (enc : k → w → w)
    (inv : (w × w × w) → Option (k × w)) (checks : w → List w)
    (oracle : w → w) (v : w) : Nat :=
  match inv (triple inc oracle v) with
  | none => 0
  | some pair =>
    if pair.2 = v && (checks v).all (fun z => decide (enc pair.1 z = oracle z))
    then 1 else 0

theorem genuine_candidate_accepted [DecidableEq w] (inc : w → w) (enc : k → w → w)
    (inv : (w × w × w) → Option (k × w)) (checks : w → List w) (key : k) (v : w)
    (h : inv (triple inc (enc key) v) = some (key,v)) :
    accepts inc enc inv checks (enc key) v = 1 := by
  simp [accepts, h]

/-- The real-oracle accept count bounds successes against an unrestricted
    uniform target, even if F has collisions or unreachable target values. -/
theorem uniform_target_le_actual_verifier [DecidableEq w] [DecidableEq k]
    (inc : w → w) (enc : k → w → w) (inv : (w × w × w) → Option (k × w))
    (checks : w → List w) (xs : List (k × w)) (ys : List (w × w × w))
    (hx : xs.Nodup) (hy : ys.Nodup) (allX : ∀ x, x ∈ xs) (allY : ∀ y, y ∈ ys) :
    total ys (inverted (fun (kv : k × w) => triple inc (enc kv.1) kv.2) inv) ≤
      total xs (fun kv => accepts inc enc inv checks (enc kv.1) kv.2) := by
  rw [← double_count xs ys hx hy allX allY]
  apply total_mono; intro kv
  by_cases hh : inv (triple inc (enc kv.1) kv.2) = some kv
  · have ha := genuine_candidate_accepted inc enc inv checks kv.1 kv.2 hh
    simp [hh, ha]
  · simp [hh]

/-- If an inverter may supply an input of its own, partition its accepted
    candidates by that input. No independence of this choice is assumed. -/
theorem chosen_input_union [DecidableEq ι] (xs : List α) (indices : List ι)
    (hi : indices.Nodup) (allI : ∀ i, i ∈ indices) (choice : α → ι)
    (score : α → Nat) (cap : Nat)
    (per_input : ∀ i, total xs (fun x => if i = choice x then score x else 0) ≤ cap) :
    total xs score ≤ indices.length * cap := by
  calc
    _ = total xs (fun x => total indices
          (fun i => if i = choice x then score x else 0)) := by
        apply total_congr; intro x
        rw [total_point indices (choice x) (score x) hi]; simp [allI]
    _ = _ := total_swap xs indices (fun x i => if i = choice x then score x else 0)
    _ ≤ total indices (fun _ => cap) := total_mono _ per_input
    _ = _ := sum_pointwise_const _ _ _ (by simp)

/-- In the terminal RF model, the target triple is independent of the
    complete visible history, including the last output. A bijection chosen
    by that history gives exactly one triple per masked state. -/
theorem masked_target_fiber [DecidableEq β] (targets : List β) (hx : targets.Nodup)
    (all : ∀ t, t ∈ targets) (mask unmask : ν → β → β)
    (left : ∀ h t, unmask h (mask h t) = t)
    (right : ∀ h t, mask h (unmask h t) = t)
    (h : ν) (state : β) (historyWeight : Nat) :
    total targets (fun t => if mask h t = state then historyWeight else 0) = historyWeight := by
  calc
    _ = total targets (fun t => if t = unmask h state then historyWeight else 0) := by
      apply total_congr; intro t
      have e : mask h t = state ↔ t = unmask h state :=
        ⟨fun eq => by rw [← eq, left], fun eq => by rw [eq, right]⟩
      simp [e]
    _ = _ := by rw [total_point _ _ _ hx]; simp [all]

/-- In the ideal transcript, guessing an independent target succeeds on one
    candidate per view. With 2^n targets this is probability 2^(-n). -/
theorem uniform_guess_count [DecidableEq β] (views : List ν) (targets : List β)
    (hx : targets.Nodup) (all : ∀ t, t ∈ targets) (guess : ν → β)
    (weight : ν → Nat) :
    total views (fun h => total targets (fun y => if y = guess h then weight h else 0)) =
      total views weight := by
  apply total_congr; intro h
  rw [total_point _ _ _ hx]; simp [all]

/-- A fixed-key test that checks three known AES images always accepts when
    the oracle key equals the predetermined key. Other matching keys only
    increase its real success probability. -/
theorem fixed_key_test_count [DecidableEq α] [DecidableEq β]
    (keys : List α) (hk : keys.Nodup) (k₀ : α) (mem : k₀ ∈ keys)
    (signature : α → β) :
    1 ≤ total keys (fun k => if signature k = signature k₀ then 1 else 0) := by
  calc
    1 = total keys (fun k => if k = k₀ then 1 else 0) := by
      rw [total_point _ _ _ hk]; simp [mem]
    _ ≤ _ := by
      apply total_mono; intro k; by_cases eq : k = k₀ <;> simp [eq]

/-- D = (2^128)_3. This is the strict comparison
    2048·(2^(-256) − 1/D) > 2^(-246), with positive denominators cleared. -/
theorem segment_bound_floor_2048 :
    let d := falling (2^128) 3
    2^256 * d < (2^246 : Nat) * (2048 * (d-2^256)) := by decide

/-- For 1024 autonomous segments the extra ideal success term 2^(-256)
    suffices to pass the same threshold, even with a perfect seed. -/
theorem autonomous_bound_floor_1024 :
    let d := falling (2^128) 3
    2^256 * d < (2^246 : Nat) * (1024 * (d-2^256) + d) := by decide

end PTG3.Reduction

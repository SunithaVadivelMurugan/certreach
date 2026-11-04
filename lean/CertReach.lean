import Mathlib

/-!
# Certificates for packet-labelled reachability (Lean 4 draft)

STATUS: DRAFT. This file has NOT been compiled yet. Expect small errors
(names, tactics) on the first build; fix them without changing the theorem
statements, which are the part that needs human review.

Stage 1 (proved, untested): `cut_sound`, `checkPath_sound`, `positive_sound`,
`negative_sound`.
Stage 2 (statements only, marked `sorry`): `cut_complete`, `path_complete`.

A graph has nodes `Fin n` and packets `Fin k`. Each ordered pair of nodes carries a
label: the set of packets the edge admits, as a Boolean-valued function.
-/

namespace CertReach

/-- A labelled graph on nodes `Fin n` with packets `Fin k`. -/
structure LGraph (n k : Nat) where
  label : Fin n → Fin n → Fin k → Bool

variable {n k : Nat}

/-- `Reaches g p u v`: there is a walk from `u` to `v` on which every edge admits `p`. -/
inductive Reaches (g : LGraph n k) (p : Fin k) : Fin n → Fin n → Prop
  | refl (u : Fin n) : Reaches g p u u
  | step {u v w : Fin n} : g.label u v p = true → Reaches g p v w → Reaches g p u w

/-- `IsCut g G s t S`: `S` contains `s` but not `t`, and every edge leaving `S`
has a label disjoint from the group `G` of packets. -/
abbrev IsCut (g : LGraph n k) (G : Fin k → Bool) (s t : Fin n) (S : Fin n → Bool) : Prop :=
  S s = true ∧ S t = false ∧
  ∀ u v : Fin n, S u = true → S v = false → ∀ p : Fin k, G p = true → g.label u v p = false

/-- The cut checker, as a Boolean function. -/
def checkCut (g : LGraph n k) (G : Fin k → Bool) (s t : Fin n) (S : Fin n → Bool) : Bool :=
  decide (IsCut g G s t S)

theorem checkCut_sound (g : LGraph n k) (G : Fin k → Bool) (s t : Fin n) (S : Fin n → Bool)
    (h : checkCut g G s t S = true) : IsCut g G s t S :=
  of_decide_eq_true h

/-- A walk that starts inside `S` and uses only edges admitting a packet of the group
stays inside `S`. -/
theorem reaches_stay (g : LGraph n k) (G : Fin k → Bool) (S : Fin n → Bool)
    (hcut : ∀ u v : Fin n, S u = true → S v = false → ∀ p : Fin k, G p = true →
      g.label u v p = false)
    {p : Fin k} (hp : G p = true) {u v : Fin n} (h : Reaches g p u v) :
    S u = true → S v = true := by
  induction h with
  | refl => intro hu; exact hu
  | @step u' v' w hedge _ ih =>
    intro hu
    have hv : S v' = true := by
      by_contra hnv
      have hf : S v' = false := by simpa using hnv
      have hno := hcut u' v' hu hf p hp
      rw [hno] at hedge
      exact absurd hedge (by decide)
    exact ih hv

/-- Soundness of a cut: no packet of the group reaches the target. -/
theorem cut_sound (g : LGraph n k) (G : Fin k → Bool) (s t : Fin n) (S : Fin n → Bool)
    (hc : IsCut g G s t S) {p : Fin k} (hp : G p = true) : ¬ Reaches g p s t := by
  obtain ⟨hs, ht, hcut⟩ := hc
  intro h
  have hSt := reaches_stay g G S hcut hp h hs
  rw [ht] at hSt
  exact absurd hSt (by decide)

/-- Soundness of a negative certificate: cuts whose groups cover every queried packet. -/
theorem negative_sound (g : LGraph n k) (s t : Fin n) (P : Fin k → Bool)
    (cuts : List ((Fin k → Bool) × (Fin n → Bool)))
    (hcuts : ∀ c ∈ cuts, IsCut g c.1 s t c.2)
    (hcover : ∀ p, P p = true → ∃ c ∈ cuts, c.1 p = true) :
    ∀ p, P p = true → ¬ Reaches g p s t := by
  intro p hp
  obtain ⟨c, hc, hcp⟩ := hcover p hp
  exact cut_sound g c.1 s t c.2 (hcuts c hc) hcp

/-- The path checker: follow the listed nodes from `u`, requiring each edge to admit `p`,
and finish at `t`. -/
def checkPath (g : LGraph n k) (p : Fin k) : Fin n → List (Fin n) → Fin n → Bool
  | u, [], t => decide (u = t)
  | u, v :: rest, t => g.label u v p && checkPath g p v rest t

theorem checkPath_sound (g : LGraph n k) (p : Fin k) :
    ∀ (path : List (Fin n)) (u t : Fin n),
      checkPath g p u path t = true → Reaches g p u t
  | [], u, t, h => by
    have hut : u = t := by simpa [checkPath] using h
    subst hut
    exact Reaches.refl _
  | v :: rest, u, t, h => by
    simp only [checkPath, Bool.and_eq_true] at h
    exact Reaches.step h.1 (checkPath_sound g p rest v t h.2)

/-- Soundness of a positive certificate. -/
theorem positive_sound (g : LGraph n k) (s t : Fin n) (p : Fin k) (path : List (Fin n))
    (h : checkPath g p s path t = true) : Reaches g p s t :=
  checkPath_sound g p path s t h

/-! ## Stage 2: completeness (statements only) -/

/-- If `p` does not reach `t`, the set of nodes reachable from `s` is a cut for `{p}`. -/
theorem cut_complete (g : LGraph n k) (s t : Fin n) (p : Fin k) (h : ¬ Reaches g p s t) :
    ∃ S : Fin n → Bool, IsCut g (fun q => decide (q = p)) s t S := by
  sorry

/-- If `p` reaches `t`, some node list passes the path checker. -/
theorem path_complete (g : LGraph n k) (s t : Fin n) (p : Fin k) (h : Reaches g p s t) :
    ∃ path : List (Fin n), checkPath g p s path t = true := by
  sorry

end CertReach

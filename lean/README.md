# Lean 4 formalization (draft)

`CertReach.lean` formalizes the definitions and the soundness theorems for the two certificate types. It is a **draft that has not yet been compiled**, so expect small errors on the first build. The theorem statements are the part that needs careful human review; the proofs are checked by the Lean kernel.

| Item | Status |
| --- | --- |
| `LGraph`, `Reaches`, `IsCut`, `checkCut`, `checkPath` | definitions |
| `checkCut_sound`, `reaches_stay`, `cut_sound`, `negative_sound` | proofs written, untested |
| `checkPath_sound`, `positive_sound` | proofs written, untested |
| `cut_complete`, `path_complete` | statements only (`sorry`), good first exercises |

## Setup (about an hour, mostly downloading)

These steps follow the official installation guide at <https://lean-lang.org/install/manual>; check it for your operating system.

1. Install **VS Code** and the Lean 4 extension: `code --install-extension leanprover.lean4`. The extension can also walk you through installing `elan`, the Lean version manager.
2. Create a project that depends on Mathlib:
   ```bash
   lake +leanprover-community/mathlib4:lean-toolchain new CertReachLean math
   cd CertReachLean
   lake exe cache get      # downloads precompiled Mathlib; saves hours
   ```
   The Mathlib download is several gigabytes. On Windows, antivirus software can slow or break the download.
3. Open the folder in VS Code (`code .`) and choose "Trust authors" when asked.
4. Copy `CertReach.lean` into the project (for example as `CertReachLean/CertReach.lean`) and open it.

## What to expect

- The first open can take a minute while Mathlib loads.
- Two warnings about `sorry` (in `cut_complete` and `path_complete`) are expected.
- Any other red error is a bug in the draft. Fix it **without changing a theorem statement**, then rebuild with `lake build`.

## Reviewing the proofs

- The Lean kernel checks every proof, but it does not check that a theorem statement says what you mean. Read each statement carefully.
- When fixing build errors, change proofs and names, not theorem statements.

## Suggested first exercises

1. Prove `path_complete` by induction on `Reaches`.
2. Prove `cut_complete`: take `S u := decide (Reaches g p s u)` (use `Classical`), and prove the three parts of `IsCut`. You will need a small lemma that extends a walk by one edge.
3. State and prove the claim that a group has a cut if and only if the target is unreachable from the source in the union graph (Proposition 3 in the paper draft).

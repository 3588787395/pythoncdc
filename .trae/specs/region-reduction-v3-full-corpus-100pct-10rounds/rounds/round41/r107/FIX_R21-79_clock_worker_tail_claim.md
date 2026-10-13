# FIX_R21-79 — clock_worker tail claim: positive identification of "sequential code after the whole if/elif statement" inside the nested-elif expander

**Engineer:** r107a · **File edited:** `core/cfg/region_analyzer.py` **only**
**Base (pinned):** `996a1b1acf143458` (banked `[R21-77-F5]` analyzer, repo copy
`.../rounds/round41/CANDIDATE_r2177f5_996a1b1acf143458.py`) · **Candidate:** `3ad5ceaa23135334`
**Untouched:** `core/cfg/region_ast_generator.py` = `566ff5c502276e48`, `pycdc.py` = `cf4e2705ab042732`

## The rule, in one paragraph

In `_build_elif_region`, immediately after the nested-elif expander returns
`elif_info = _check_elif_chain(block, else_blocks, merge)` (i.e. before the chain region is
assembled, before the `else_blocks` struct-filter and before `all_blocks`/`IfRegion(…)`), the
candidate makes a **positive claim about the tail**, using only edge data and the chain's own
region data:

* **Walls `W`** = the chain's own structural member set — the chain head block, the main
  condition block, `all_condition_blocks`, the `then_blocks` arm, every `elif_conditions` entry
  and every block of every `elif_bodies` arm.
* **Tail `T`** = the transitive forward closure of the chain's **declared merge** block along
  `block.successors`, where a wall block is neither entered nor traversed.
* A block `f` currently sitting in `final_else` is **sequential-after-the-if** (not else-arm
  content) iff **(a)** `f ∈ T` **and (b)** `f` has **no predecessor in `W`**. (b) is the dual
  half of the CPython 3.11 elif layout fact the file already relies on elsewhere: the else arm
  is entered *only* through the last condition's false edge, so a true arm entry always has one
  chain-member predecessor; a block with no member predecessor that is nevertheless reachable
  from the chain's exit is a *sibling statement of the whole if statement*.
  Those blocks are dropped from `elif_info["final_else"]`, so the chain stops absorbing them,
  stops claiming them in `region.blocks`, and they stay with the parent sequence.

It fires only when `merge is not None` (a *declared* chain exit is the only anchor for
"after the chain"; the `merge=None` families are R21-77/R21-78 territory) and it refuses to act
when the merge itself is inside `final_else` (that is the step-6 merge-misdclaration shape,
TICKET_R21-78 — not this mechanism).

## Why this is principled (design-law compliance)

* Reads **only**: `successors` / `predecessors` (edge data) and the region-under-construction's
  own member block sets (`block`, `condition_block`, `all_condition_blocks`, `then_blocks`,
  `elif_info['conditions']`, `elif_info['bodies']`, `merge`).
* **No** function/file names, **no** absolute offsets as matching keys, **no** counters, **no**
  thresholds, **no** `len(...)` magnitude comparisons as the trigger. (The only length compare is
  the write-guard `_r2179_kept != _r2179_final_else`, which is an equality test used to avoid a
  no-op assignment, not a predicate.)
* Serves **principle 2** (unique membership: the tail is claimed by exactly one arm — none) and
  **principles 3/4** (nested regions stay single abstract nodes referenced by their entry; the
  closure never traverses a member block, so it cannot reach into an arm).
* **Bottom-up, one-way**: the correction happens at identification time, before the region is
  built; nothing is re-ordered in the generator's postprocess (banned).

## Excluded-premise reconciliation

1. **"Remove every block that is another region's entry from `elif_final_else`" is NOT implemented.**
   The discriminator is edge-based, not entry-identity-based. Evidence from the pinned base
   (`rig/dump_chain.py`): the legitimate else-arm entry `@7492` (13 instrs, `STORE_ATTR`) is a
   region-free block whose predecessors are `7248` (an `elif` condition, i.e. a wall) and `7270`;
   it fails (a) *and* is protected by (b). The nested chain entry `@7634` and the declared
   entries `@7582/@7604/@7706/@7712/@7972/@8186/@8294/…` are removed only because they are
   reachable from merge `@7216` **and** have no wall predecessor — a `else: if a: …` arm entry
   always has the last condition as predecessor and therefore survives.
2. **No narrower refusal of the fold** (`[R21-48]` family) was added; nothing is refused, the
   tail is *positively* claimed away from the arm.
3. **No emission-time reordering**: the generator is byte-unchanged (`566ff5c502276e48`).

## Fire site (measured, not asserted)

`clock_worker :: IfRegion@7186` (cond=`7186`, merge=`7216`, `elif_conditions=[7248]`,
`elif_bodies=[[7372,7488]]`):

| quantity | base `996a1b1acf143458` | candidate `3ad5ceaa23135334` |
|---|---|---|
| `elif_final_else` | 42 blocks `7492 7582 … 9144` | **1 block `7492`** |
| `region.blocks` | 48 | **7** (`7186 7202 7212 7248 7372 7488 7492`) |
| caller `else_blocks` after struct filter | 45 | **4** (`7248 7372 7488 7492`) |
| instruction bytes in pruned tail | — | 253 instrs freed (`rig/dump_chain.py`) |

Product bytes **do change** (base product 20190 B vs candidate 20078 B; `difflib` shows 30 lines
moved from inside the chain's `else:` arm to sibling position, i.e. the tail is now emitted at
the ORACLE's indentation level), so the predicate demonstrably fires.

## What it does NOT close (honest scope result)

The 112-instruction run `@7972..@8586` (ORACLE/`pyc` source lines 498–524) is **still not
emitted**. `rig/span_diff.py` shows the identical `delete orig[1192:1304]=112` span in *both*
arms, and the per-line attribution (`rig/line_diff.py`) is unchanged. Reason, measured: those
blocks are not dropped by `IfRegion@7186`'s claim at all — they are members of the **next chain
level**, `IfRegion@7634`, whose *then arm* block list is
`[7668, 7706, 7708, 7710, 7712, 7814, 7972, 7980, 8166, 8170, 8184, 8186, 8256, 8294, …, 8588]`.
The arm renderer emits the statements up to the nested `LoopRegion@7706` and stops there; after
this patch the blocks' `block_to_region` owner is `TryExceptRegion@6` (the function-wide try),
not the arm's region, so the parent sequence does not pick them up either. That is an
**arm-continuation / ownership-priority defect** (`_collect_branch_blocks` arm list + the
`block_to_region` innermost-vs-first-come assignment), a different mechanism from the
final_else claim, and it lives outside this ticket's single-mechanism scope. The claim-side
defect this ticket described is fixed; the emission-side defect that actually loses the 112
instructions is handed on with the evidence above.

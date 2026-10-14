# FIX_R21-89 — the fold-window guard completion (generator-only, built on [R21-88])

Candidate generator **`cb8c2c7928672abd`** (3,909,284 B, UTF-8 BOM, 100 % CRLF, zero `\\r\\r\\n`,
zero bare LF, `python -X utf8 -m py_compile` rc=0), produced only by
`D:/Temp/r115/DELIVER/PATCH_R21-89_region_ast_generator.py` **from the campaign base arm
`[R21-88] 47d44ec51fa325c5`** (anchor-verified `EXPECT_BASE`; two anchored edits — one call inserted
at the tail of `_r2188_and_prefix_or_tail`, one new method `_r2189_fold_window_guards`; two
consecutive runs reproduce the identical sha16 ⇒ idempotent; absolute paths only).
**No analyzer half**: the pinned `[R21-77-F5]` analyzer `996a1b1acf143458` is unchanged and re-hashed
after every run. `[R21-86]`, `[R21-79]` and `[R21-87]` are not used as bases or partners.

## The one rule

An `(A and B) or C` fold rewrites **this statement's own** arm window (and, when the tail leg
carries an else list, the chain continuation inherited from it). A block B inside one of those two
lists can be a *bare condition block*: it holds one whole boolean test and its last instruction is
the conditional jump over its body, while the bottom-up reduction declared no region for it and
instead recorded the test as an **`elif_conditions` entry of a leg region that this very fold has
consumed** (the leg's test was lifted into the folded expression, so that leg region is never
generated and never walks its own elif list). The resident branch walk `_process_if_blocks` then
sends B to `_generate_block_statements`, which drops the test as jump scaffolding and **emits no
statement**: the guard disappears, its siblings are hoisted one level, and the continuation —
claimed as the `else` of the nested region built at B's fall-through block — re-renders as a
mis-attached `else:`.

Instrumentation (runtime monkeypatch only; `rig/trace_r115.py`, `rig/census_r115.py`,
`rig/decl_r115.py`, `rig/decl2_r115.py`, `rig/diag_guard_r115.py`; every probe re-hashed
`core/cfg` after the run and proved its product byte-identical to the un-probed base product)
located the consumers and the refusals exactly:

* walk = `_process_if_blocks(list[7248, 7270, 7372, 7488, 7492], IfRegion@7164, 'then')` →
  `LIST(2)`; the `@7248` member (`LOAD_FAST now_date; LOAD_DEREF self; LOAD_ATTR first_run_date;
  COMPARE_OP !=; POP_JUMP_FORWARD_IF_FALSE to 7492`) produced **zero statements**;
* walk = `_process_if_blocks(list[8592, 8666, 8904, 8688, 8852, 8926, 9144, …], IfRegion@7582,
  'else')` → `LIST(3)`; the `@8592` member (`check_trading_time(7 args); CALL;
  POP_JUMP_FORWARD_IF_FALSE to 8904`) likewise produced zero statements;
* data that distinguishes the swallowed leg from a rendered one: no region has `entry`/
  `condition_block` = B, while `@7248` sits in `IfRegion@7186.elif_conditions` and `@8592` sits in
  `IfRegion@7634.elif_conditions` — and both of those claimants are fold legs whose tests this fold
  lifts, i.e. **the claim is real and the emitter is dead**. Proved at dispatch: a region declared
  for `@7248` without releasing that claim returns `_generate_if → LIST(0)` because of the resident
  refusal `region.entry in r.elif_conditions`.

## Residual A — the swallowed guard (`@@ -194,12 +194,12 @@`)

Block consumed without emission: `@7248`, the arm's first member, whose fall-through `@7270`
(already an IfRegion: `cond=7270, then=[7372,7488], else=[7492], merge=7582`) was dispatched one
level too high and whose false-target `@7492` was printed as that region's `else:`.
The rule declares the guard at identification time: a new `IfRegion(entry=condition_block=@7248,
then_blocks=[7270, 7372, 7488], else_blocks=[], merge_block=@7492)`, parented to the folded region,
with `@7270` re-parented into it, and `@7248` removed from `@7186`'s parallel
`elif_conditions`/`elif_bodies`. Because `@7492` **is a successor of a window block** (the body
flows into it), T is postdominator code, never an else arm: `@7270`'s claim `else_blocks == [T]`
is released (`else_blocks := []`, `T` dropped from its block record, `merge_block := T`) and `T`
stays in the arm list for the parent walk. Result — the product now prints gold's
`if now_date != self.first_run_date:` guard with its two siblings inside it and the continuation
sequential; hunk `H2` collapsed from `del=10 ins=10` to a one-line parenthesisation difference.

## Residual B — the ladder's first leg (`@@ -238,3` and `@@ -245,8`)

Block consumed without emission: `@8592`, head of the ladder that the `[R21-88]` chain-continuation
inheritance handed to `IfRegion@7582.else_blocks` as a *flat* list (a lossy projection of
`@7634`'s own `elif_conditions=[8592] / elif_bodies=[[8666,8688,8852]] /
elif_final_else=[8904, 8926, 9144, …]` declaration, which the same fold had just consumed).
Discriminator, successor-edge only: **no window block flows into `T`** and every successor of the
window outside the window lies at-or-after `T` (the body jumps past `T`) ⇒ `T` is the alternative
arm, not the continuation. The rule therefore claims the arm with the leg: `N.else_blocks` = the
blocks of the list at-or-after `@8904`, and the `@8592` claim is released from `@7634`'s elif lists.
No list surgery otherwise — the parent list keeps referencing the window because the resident
dispatch gate requires a nested region's blocks to be members of the walked list; those members are
then covered by N's own post-generation claim and skipped by the parent pass, so each block still
has exactly one emitter (principle 2). Result — line 239 now prints gold's
`elif check_trading_time(am_open, am_close, pm_open, pm_close, pm_over, …):` with its
`if check_handle_date(...)/else:` body at the right level.

## Rulers reused, and no new predicate minted

`_r2188_and_prefix_or_tail` conjuncts (jump polarity `IF_FALSE`, `NONE_CHECK_OPS` exclusion,
`CONDITIONAL_JUMP_OPS` membership, arm/E-anchored windows) verbatim; `_r4701_and_lift_or_tail`
window style; `region_analyzer.get_entry_region_for_block` / `is_block_entry` (the resident
`_nested_if_entry_generate` dispatch, `_process_if_blocks` step 5/6); `generated_blocks` /
`generated_offsets` and `_generated_regions` claim sets (appended only at existing sites); the
`[R21-88]` re-parent code (remove from old parent's `children`, set `parent`, append, sort by
entry) and its list-move semantics; `_if_generate_normal` / `_if_generate_elif_chain` /
`_process_if_blocks` do all emission — this rule only feeds them a complete declaration.
Criteria read stack shape, opcode class, region/block data, successor edges and in-list membership
only: no function names, no file names, no absolute offsets as keys, no counters, no magnitude
threshold as trigger.

## Why this is not one of the excluded shapes

Bottom-up reduction (the fold's own windows, declared before its walks); unique block membership
(no list is duplicated, no block gains a second emitter — proved by `back=+0`, `hunks 8→5` and the
absence of any duplicated marker in the product); nested regions stay single abstract nodes
referenced by entry; **correct-at-identification** — the declaration happens inside
`_r2188_and_prefix_or_tail` before this statement's arm/else walks begin, so there is no
retrospective text repair, no un-mark, no postprocess reorder, no re-print, and one-way dataflow;
no ledger pre-claim at the four structural methods (the `-485` shape: my first attempt placed the
pass in the pre-dispatch pre-pass and let it fire on *every* branch list — it produced bogus
declarations at `@426/@2838/@8964` and collapsed the unit to 195 lines/`-485`; rejected, and the
shipped arm is scoped to fold windows and refuses those blocks by the fall-through-successor and
`elif`-claim conjuncts); not the caller-side post-claim ledger and not `[R21-82]` bypass completion
(inert); not render-scoped claims from list membership; not `block_to_region` entry-owner
discrimination (the census shows `block_to_region` maps these blocks to `TryExceptRegion@6`, which
is precisely why the resident walk misses them — the rule never queries or rewrites that map); not
mid-walk tail transfer (`212/-282/back=-1`) — nothing is transferred during a walk; not an analyzer
change, and `[R21-79]` is not paired.

## Residual C verdict (`@@ -184,5 +184,5 @@`) — structural, but NOT the same cause

Measured, not assumed: at `@6496` the fold's arm window is `[6580, 6582, 6652]` and there is **no
bare condition block** in it — `@6690` (`if holiday_not_do_before == '0'`) *is* a region entry
(`IfRegion@6690, cond=6690, merge=6778`) whose parent is `IfRegion@6548`, a leg region of this
fold, while `@6690/@6702/@6778` sit in the *parent* `IfRegion@6280.then_blocks`. So the dedent is an
**arm-window under-declaration** (the tail-ownership axis, positive direction — the region does not
own code that belongs to its arm), not walk coverage; the two faces of A/B (a test block with no
region at all) cannot reach it, and closing it is the `[R21-79]`-adjacent positive-tail-claim axis
that is already excluded as measured-inert. Left unfixed deliberately rather than attempted blind.

## Verdict

Bar 1 met on both instruction metrics (instrs -25 -> -13, jsites -4 -> -3, back=+0 kept, ours=256
unchanged, no overshoot below 254); bars 2-4 met (zero collateral, zero panel regression,
CHANGED={realtime_event_source.pyc} over the ROOT-joined 402). indeg-equal did NOT flip and the
judge stays `12/13 Different control flow` => **banked, not installable**.

Per-face ablations prove the pair is not a cancellation reading: arm face alone
(`abl_r2189_armonly.py`, `4b988da14af58d41`) = `256/-20/+0/-3/9`, continuation face alone
(`abl_r2189_elseonly.py`, `fd28f04040cdb2cd`) = `256/-18/+0/-4/7`, both faces
(`cb8c2c7928672abd`) = `256/-13/+0/-3/5` - each face pays for the test it restores, and the shipped
arm pays both once.

Remaining distance: residual C, the flat chained-compare leg
(`elif A and B and delay_after_trading >= now_time >= after_trading` still printed as
`if A and B:` plus a nested `if delay... >= now_time >= after...:`), and the loop-tail
`else:` / `return None` pair (which is the whole of the residual +2 in `ours`).

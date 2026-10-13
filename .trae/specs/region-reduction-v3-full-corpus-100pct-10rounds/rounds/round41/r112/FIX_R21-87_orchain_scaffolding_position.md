# FIX_R21-87 — the `(A and B) or C` short-circuit chain must be folded at the arm's own position
(engineer r112a, round 41, axis = renderer position / nesting order)

## The rule in one paragraph

CPython compiles `if (A and B) or C: <arm>` (followed by the sibling statement at `E`) into three
short-circuit legs that all share one landing: `A; POP_JUMP_IF_FALSE -> T`, `B (possibly a chained
compare spanning several blocks); POP_JUMP_IF_TRUE -> arm`, its fall-through/connector blocks
landing on `T`, and `T: C; POP_JUMP_IF_FALSE -> E` with `C` true falling straight into the arm.
Region reduction hands those three legs to three `IfRegion`s — `R(cond=A, merge=T, else=[])`,
`Mr(cond=B)`, `Tr(entry=T, cond=T)` — and the arm renderer, taking `R` one region at a time, emits
`if A: if B or C: <arm>`, i.e. one scaffolding line too many, the arm one indent level too deep, and
the *next* sibling statement absorbed as an `elif` of the inner test. **[R21-87]** says: at
identification time, in `_if_generate_normal`, after the condition has been assembled and *before*
the arm sequence is dispatched, a positive-polarity single leg whose merge is itself a test leg
collapses the whole chain into ONE `If` whose test is `BoolOp(or, [BoolOp(and, [A, B]), C])` and
whose body is the arm — emitted once, in place, at the region's own position. No text is repaired
afterwards, no already-emitted statement is reordered, nothing is un-marked and re-printed; the
statement is right the first time it is printed.

## The discriminator (six conjuncts; stack/opcode/region data only)

1. `region.condition_block`'s last instruction is a conditional `IF_FALSE` jump (not a
   `NONE_CHECK` op) to `T`, `T is region.merge_block`, and `region.else_blocks` is empty — the outer
   leg is a positive single leg whose *false* exit is not the statement's end.
2. `T`'s own last instruction is again an `IF_FALSE` jump to `E` (`E != T`), and exactly one of `T`'s
   other successors is a member of `region.then_blocks` — that successor is the arm entry, so `T` is
   the `or` tail leg of the *same test*, not a merge point.
3. Exactly one successor of `condition_block` other than `T` lies strictly between them and is the
   entry of an `IfRegion Mr` with `Mr.condition_block is Mr.entry` — the middle `and` leg.
4. The last test block of that leg (`Mr.entry` together with its `chained_compare_blocks`) ends with
   an `IF_TRUE` jump onto the arm entry — the `and` leg's true exit *is* this statement's body.
5. `T` has a predecessor in `[Mr.entry, T)` that is not `condition_block` — the `and` leg's
   fall-through is handed back to the `or` tail (this is the same shared-landing fact that the
   analyzer's resident `_boolop_shared_target_is_join` uses; here it is read as block-edge data).
6. All three operands reconstruct (A from the assembled condition, B via the resident
   chained-compare scale, C from `T` minus its terminating jump).

Reduction: test = `BoolOp(or,[BoolOp(and,[A,B]),C])`; `region.then_blocks` is narrowed to the
`[arm, E)` offset window (the statement's own arm, nested regions still dispatched as abstract
nodes), `region.merge_block` is re-declared as `E`; the three leg test-blocks and the pure
connector blocks between them (`POP_TOP/NOP/RESUME/CACHE/JUMP_FORWARD/EXTENDED_ARG` only) go into
`generated_blocks`/`generated_offsets` so they are not re-emitted by the parent sequence — the same
hand-back technique as landed `_r4701_and_lift_or_tail`. *Ownership-conservation guard* (added after
the first destructive reading): the fold refuses unless every `then_block` is already either a
marked leg block or an arm block, i.e. unless narrowing provably loses nothing; the guard is
evaluated before any mutation, so a refusal is a byte-for-byte no-op.

## Resident rulers reused (nothing else minted)

* `_r4701_and_lift_or_tail` (generator, landed) — the family template: same three-leg shape at the
  *negative* polarity, same `generated_blocks` hand-back, same `BoolOp` re-assembly. `[R21-87]` is
  its positive-polarity sibling and sits physically next to it.
* `_build_chained_compare_from_region_data` (generator, landed) — builds operand `B` for the
  `pre_before_trading <= now_time < pm_close` legs; `_r4701` uses the identical scale.
* `_if_extract_condition_from_instructions` / `expr_reconstructor` (generator, landed) — operands
  `A` and `C` are reconstructed with the existing instruction-filter scale (same opname filter list
  as `inline_boolop_chains`).
* `inline_boolop_chains` + `_discover_predicate_and_chain` (generator, landed) — my hook runs
  *after* both, so an `and` chain already recognised by the resident scales is consumed by them and
  `[R21-87]` only sees the leftover single-leg case; `_convert_lambda_function_objects` still wraps
  the result.
* `_boolop_shared_target_is_join` (analyzer, landed) — cited as the identification-side precedent
  for "shared landing ⇒ join"; not called (the generator must not call analyzer privates) but its
  fact class is re-read here from block edges only.
* `[R21-86]` render-scoped claim/release ledger — untouched; my arm window deliberately never marks
  blocks inside `[arm, E)`, which is where the released `@7972..@8586` run lives, so the two rules
  are orthogonal (measured: the run is still printed once, `instrs` did not jump back to `-114`).

## Excluded-premise reconciliation

* **No jump-target landing channel** (`[[pythoncdc-no-landing-channel-in-generator]]`) — respected:
  the rule changes *nesting and the emitted test expression*, never a jump operand; the landing
  facts are read only as evidence.
* **Renderer-position half of addendum 9** — this is that axis, and it moved: the 4 sites of
  `if (A and B) or C:` now print folded and flat (`ours 262 → 257`, oracle 254; the 8-line
  overshoot is down to 3), so "the scaffolding is in the wrong place" is *confirmed as the cause of
  the overshoot* and partially cured.
* **`elif_final_else` tail release as a flip** (correct, zero gain) and the **ledger pre-claim /
  post-claim / entry-owner-discrimination** exclusions — not re-attempted; my rule claims no ledger
  and re-owns no block: it only narrows a `then_blocks` window that the guard proves already closed.
* **Analyzer-only stub-folded join** (destructive) — not re-attempted; `[R21-87]` is generator-only
  on the pinned F5 analyzer `996a1b1acf143458`, and `[R21-79]` was again left off.
* **New finding that partially contradicts the brief's arithmetic**: the base reading `instrs=-6`
  is *not* "94 % of the run recovered + 8 misplaced lines". With the scaffolding removed the same
  product reads `instrs=-26`. Roughly 20 instructions of the `@7164..@8592` tail were being paid for
  by duplicated scaffolding tests. `indeg-equal` stays `False` on every arm: the remaining deficit
  is missing code, not misplaced code, so a text-only repair of the position cannot flip the judge.
* **Site `@7164` (step 3) is not foldable from the generator**: its region `R@7164` owns the whole
  rest of the while-body (`then_blocks` extends far past `E=7582`), so the conservation guard
  refuses the fold there. Closing that leg needs an analyzer-side ownership re-declaration, which is
  the entry-owner axis already measured destructive — recorded, not re-attempted.

# FIX_R21-88 — tail ownership of the `@7164` chain: pre-pass re-declaration + chain-continuation fold (generator-only)

Candidate generator `47d44ec51fa325c5` (3,895,606 B, UTF-8 BOM, 100 % CRLF, zero bare LF,
zero `\r\r\n`, `python -X utf8 -m py_compile` rc=0), built only by
`D:/Temp/r113/DELIVER/PATCH_R21-88_region_ast_generator.py` **from the campaign best-known arm
`[R21-86] 59a405837c22a4cb`** (anchor-verified `EXPECT_SRC`; three anchored edits — fold method,
pre-pass method, pre-pass call; re-running reproduces the identical sha16 ⇒ idempotent; absolute
paths only). **No analyzer half**; the pinned `[R21-77-F5]` analyzer `996a1b1acf143458` is
unchanged. `[R21-87]` was not used as a base — the rule SUBSUMES its fold (same six
identification conjuncts verbatim) and changes only its two tail decisions.

## The rule, in one paragraph

An `(A and B) or C` chain whose region was over-extended by the bottom-up reduction (the
`@7164` shape: `then_blocks` lists the entire loop tail `@7582…@9144`, i.e. the statements
that *follow* the chain in the parent sequence) cannot fold, because folding must lift its
legs out of a region that has already claimed the tail — the conservation guard refuses, the
scaffold stays. `[R21-88]` states the ownership fact twice, both at identification time.
**(1) Pre-pass re-declaration** (`_r2188_tail_ownership_prepass`, run once before any region
dispatch): a fold-shape region R whose every then-block at-or-after its tail-leg's jump
target E is forward-reachable from E through successor edges without crossing an arm-window
or leg block does **not** own those blocks — E is where the parent sequence resumes, so the
reachable set is sequential code of the dispatching parent P. The blocks are *moved* (never
duplicated) out of `R.then_blocks`/`R.blocks` into the P list(s) that contain `R.entry` plus
`P.blocks`, and every region entering on a moved block is re-parented to P. R now folds
cleanly (strays empty). **(2) Chain-continuation inheritance** (`_r2188_and_prefix_or_tail`):
when the tail-leg block T is itself the condition block of its own IfRegion Tr and Tr
declares a non-empty `else_blocks` list lying entirely at-or-after E, the elif ladder E opens
is this statement's continuation: the fold inherits Tr's arm declaration — `then_blocks` =
arm window, `else_blocks` = Tr's else list, `merge_block` = Tr's merge, and the folded
region's `blocks` record absorbs `Tr.blocks` so the statement's post-generation claim covers
the ladder after its own else walk emitted it once. That removes the `[R21-87]` row-5 failure
mode (`merge := E` orphaning the ladder, `-26` instructions). Strays no Tr else list can
hold still take the `[R21-87]` conservation refusal.

## The discriminator

Region/block data only — merge/condition/arm lists, jump polarity (`IF_FALSE`/`IF_TRUE`,
`NONE_CHECK_OPS` excluded), successor edges, cleanup opcode class (`POP_TOP/NOP/RESUME/
CACHE/JUMP_FORWARD/EXTENDED_ARG`), and in-list membership relations; the only positional
tests are relative windows anchored at the region's own `arm`/`E` blocks, the same class
already sanctioned by `_r4701_and_lift_or_tail` and `[R21-87]`. No function names, no file
names, no absolute offsets as keys, no counters, no magnitude thresholds. Safety conjuncts:
unique membership is maintained by list *moves*; at pre-pass time nothing is claimed or
emitted yet, so there is no un-mark, no postprocess reorder, no re-print — one-way dataflow.

Measured effect on the victim: pre-pass transfers the 41-block tail `@7582…@9144` from
`IfRegion@7164` to `LoopRegion@5598` (host list `blocks`, where `@7164` lives); the fold then
fires at `@7164` (`(A and B) or C`, arm `@7248…@7492`, merge `@7582`) and at `@7582` with the
inherited `@7634` ladder; the run `@7972…@8588` emits once (marker census as in `[R21-86]`).
Product `256` lines vs oracle `254` (all four previously-blocked sites `@6322 @6496 @7164
@7582` now render flat), `instrs=-25`, `back=+0`, `jsites=-4`, 8 local hunks, `12/13`.

## Resident rulers reused (no rival predicate minted)

* `[R21-87]`/`_r4701_and_lift_or_tail` conjuncts (1)-(5) verbatim, incl.
  `_build_chained_compare_from_region_data`, `chained_compare_blocks`, leg-marking hand-back
  family, `_convert_lambda_function_objects`.
* `self.generated_blocks` / `generated_offsets` claim sets — appended at existing sites only.
* `region.parent` / `children` / `blocks` / `then_blocks` / `else_blocks` / `body_blocks` /
  `condition_block` / `merge_block` — analyzer-declared region data; `region_lists.py`
  (r110a) census is what enumerated the transfer set.
* `[R21-86]` ledger (`_r2186_released_blocks`, render-scoped claim + `:26911` honour) —
  untouched and load-bearing: the 17-block run release still fires at `IfRegion@7604` shapes.
* `_process_if_blocks` / `_if_generate_elif_chain` arm walks do all emission; the elif-vs-
  else rendering is their resident decision (this rule only feeds them the inherited lists).

## Excluded-premise reconciliation (why this is not the `[R21-48]`-family destructive shape)

The `[R21-48]`-era re-attempts and the entry-owner discriminator (`ours=4`, `-1439`) moved or
un-marked blocks *after* dispatch decisions, re-rentering emitted code and double-printing.
This rule: (i) pre-pass mutates region lists strictly before any emission or claim (the two
controls prove separateness: pre-pass alone = `262/-6/+0/+2`, fold alone (`[R21-87]`) =
`257/-26`; the pair = `256/-25`, no duplication markers); (ii) transfers are list *moves*
(principle 2), and the blanket claim of the folded region can no longer reach the moved tail
because the tail is no longer its member — the emitter is exactly one of P's walk (statements
`@7582…`) or the inherited else walk (the ladder), never a reprint; (iii) the v2 witness
row (transfer without the pre-pass, i.e. mid-walk release into a parent whose block list was
already snapshotted) **is** the old destructive shape and was measured as such — `212/-282/
-1/-33`, identical to `[R21-87]` row-2 — and rejected; the pre-pass exists precisely to move
the decision upstream of every snapshot. `[R21-79]` is not paired. Design-rule note: the
fold-time reachability transfer variant (v1/v2) seeded its BFS without/with E and is recorded
in MEASURE rows v1/v2 as falsified sub-shapes; the shipped arm uses reachability only as a
*guard* in the pre-pass, never as a release mechanism.

## Verdict

Bar 1 NOT met (`instrs` moved away from 0 vs the scaffolding-masked `-6` base, `jsites -4`),
judge `12/13` not flipped ⇒ bank, not installable. But it is the first arm in the campaign
to render all four or-chain sites flat at parent level with `back=+0`, delta `+2` lines, and
zero collateral: the remaining `-25` is localized to two tests the fold itself swallows
(`if now_date != self.first_run_date` around `@7248`, and the first ladder test
`check_trading_time` at `@8592`), not to the tail claim any more.

# FIX_R21-15 — RETURN-terminated else-arm placement in `run_tick_socket` (r35a)

Target: `site-packages/fly/data/quote.pyc` `<module>.Quote.run_tick_socket` 90/92.
Mirror: `D:/Temp/r35a/wt` (pristine `D:/Temp/r35a/wt/pristine`).
Editable file: `core/cfg/region_ast_generator.py` (sealed sha256 `c16daa4f87dc68e6...`).

## mirror proof
- generator sha256 `c16daa4f87dc68e6ee6224096d9487ca084b6d816289a73748a3b4f98a92f592` (matches brief)
- analyzer sha256 `35e227ac3e7b25af...` (matches brief) — READ-ONLY
- cfg_builder sha256 `2b1d8ad934c5b750...`

## verdict at a glance
`run_tick_socket` 90/92-file unit: `delta=1 hunks=2 landings=5` → **`delta=0 hunks=0 landings=0
judge_diff=False` (Equal)**; file 90/92 → **91/92**; broker 120/128 → **121/128**; other 12 files
unchanged; panel total 755/776 → **757/776**. Fire census **8**, 2 of 14 products byte-changed.

## baseline
Mirror regen of `fly/data/quote.pyc` in 5.6 s → `D:/Temp/r35a/out/fly_data_quote.py`;
`cmp` vs the sealed in-place product `site-packages/fly/data/quoteOK.py` = **IDENTICAL**
(mirror reproduces sealed bytes). Judge `pyc_verify single --source` → `units=90/92`.
`unit_diff --all` → `len orig=343 prod=344 delta=1`, `hunks=2 landings=5` (matches brief).

## anatomy (measured)
Product source puts the else arm at lines 1465-1470 (`else:` / warning / acquire / `updateflag=-1`
/ release / `return None`) and `stocks = list(...)` at **16-space indent inside the then arm**
(l.1448). Compiling that source with the ruler interpreter (3.11.7) lays it out as
`test@66 → else? no: [test][then-body incl. stocks..][JUMP_FORWARD@1120→@1278][else@1122..@1276 return][exit@1278]`.
Original layout (probe `D:/Temp/r35a/probe_orig.py`, jump targets resolved):

```
@64  LOAD_FAST message          L2160
@66  POP_JUMP_FORWARD_IF_FALSE  to @528          <- else arm = guard
@68  NOP                        L2161  (inner try setup)
...try body / handlers up to @526 RERAISE       L2162-2170
@138 JUMP_FORWARD               to @684 (L2177)  <- try body's normal exit
@528 guard  ... @682 RETURN_VALUE                L2172-2176 (else arm, TERMINAL)
@684 stocks = list(message.keys())[0]            L2177  <- continuation
```
In 3.11 there is no block-reordering pass, so **emission order == source order**; a then arm
that *contains* `stocks=` would have to emit it at @528 (right after the handlers), not after
the else. Therefore the original source has `stocks = ...` **dedented out of the if/else**, and
the whole difference is that the generator nests the if-statement's continuation inside the then
arm: that over-nesting is what (a) relocates the else arm 112 instructions late and (b) adds the
1 extra `JUMP_FORWARD` (delta=+1). The then-arm list `then=[68,70,136,684,808,844,…]` contains
684/808/844 … *because* the else arm cannot fall through — those blocks are reachable only from
the then edge, so dominance puts them in `then`, which is why membership pruning could not help.
⇒ correct fix = hoist the post-else continuation out of the then arm to after the If node
(equivalent exactly when the else arm is return/raise-terminated).

## 判据实现
`core/cfg/region_ast_generator.py`, inside `_if_generate_normal` — 3 hunks, +55/−2 lines
(59746 vs pristine 59693), markers `:21341` (predicate + head build), `:21210` (init
`_r2115_tail_blocks = []` next to the landed `_then_terminal_overflow = []`), `:22182`
(tail emit, right after the landed overflow channel and before `return if_result`).

Predicate — only the region's own arms, their last instructions and block order, decided at
emission time (no jump operand, no retrospective rewrite, no crossing a sibling region's internals):
① `region.else_blocks` non-empty ∧ `region.elif_conditions` empty;
② the else arm's **max-offset block**'s last instruction opname ∈
   `RETURN_VALUE | RETURN_CONST | RAISE_VARARGS` (the arm cannot fall through to the merge);
③ some `then_blocks` block has `start_offset >` that block's offset (the post-if continuation is
   currently mis-filed inside the then arm);
④ some has `start_offset <` it (the then arm is non-empty after the split).

Reduction: `region.then_blocks` is temporarily replaced by the head blocks for
`_if_generate_then_branch(region)` and restored immediately (try/finally); the tail blocks are then
emitted by the same owning region after the `If` node with
`_process_if_blocks(sorted(tail, key=start_offset), region, branch='then')` and appended to
`if_result`, i.e. the identical "claim/emit the remainder at the owning site" shape already landed in
`_generate_try` (gate 27) and `_generate_ternary` (gate 21) — both of which were left untouched
(no re-anchoring, verified by the 12 unchanged census products).
Equivalence argument: with ② true, the tail executes only when the test is true either way, so
dedenting it is semantics-preserving; with ③ true and 3.11's absence of a block-reordering pass,
the pyc's linear order *is* the source's emission order, so the dedent is the only source shape that
can reproduce it.
Inertness proof of the instrumentation: the diagnostic probe at `:21842` (before the mechanism was
written) regenerated a byte-identical quote product (`cmp` = IDENTICAL, labelled INERT); the
`[R21-15 FIRE]` census print used for the fire count was afterwards **stubbed out**, and quote plus
broker products regenerated without it are `cmp`-identical to the ones measured with it (rc=0 both),
so the shipped file carries no instrumentation.

## fire census
Patch installed, one process per file, `[R21-15 FIRE]` counted from saved per-file stderr
(`D:/Temp/r35a/out/probe_err/*.err`): **TOTAL_FIRES = 8** over the 14 files.

| file | fires | product byte-change vs unpatched |
|---|---|---|
| fly/data/quote | 1 (entry=24, else_term=680, head=[68,70,136], tail=10 blocks) | **CHANGED** |
| IQEngine/…/trade_live_broker | 1 (entry=568, else_term=1328, tail=20+ blocks) | **CHANGED** |
| IQCommon/logger/handlers | 2 (entry=412, entry=458) | SAME (no-op fire) |
| IQEngine/…/strategy/strategy | 2 (entry=266, entry=364) | SAME |
| IQCommon/util/trade_info_utils | 1 (entry=3270) | SAME |
| quotation, wizard, real_quote, klinedata, event_source, api_base, risk `__init__`, order_api, matcher | 0 | SAME |

8 fires ⇒ 2 of 14 products change byte-for-byte. The looser candidate (③ alone, no ②) fired 18×
over the same 14 files — predicate ② (else-arm tail ends RETURN_VALUE/RETURN_CONST/RAISE_VARARGS)
is what cuts it to 8, because the other candidates' else "terminals" were `POP_TOP`/`JUMP_FORWARD`.

## readings
All judged with `--source` on my own fresh products (never the in-place stale product).

| file | before (unpatched mirror) | after (patched) | bar |
|---|---|---|---|
| fly/data/quote | 90/92 | **91/92** | ≥90/92, victim flips ⇒ 91/92 ✓ |
| fly/data/quotation | 153/153 | 153/153 | 153/153 ✓ |
| trade_live_broker | 120/128 | **121/128** | ≥120/128 ✓ (+1, same predicate, bonus) |
| wizard_quant_api | 57/58 | 57/58 ✓ | real_quote 44/45 ✓ | klinedata 63/64 ✓ |
| handlers 29/30 ✓ | event_source 12/13 ✓ | api_base 27/28 ✓ | strategy 26/27 ✓ |
| risk `__init__` 42/43 ✓ | trade_info_utils 38/41 ✓ | order_api 37/37 ✓ | matcher 17/17 ✓ |
| **TOTAL (14 files)** | **755/776** | **757/776** | no decrease anywhere ✓ |

Victim shape (`unit_diff --all`): `delta=1 hunks=2 landings=5` → `len orig=343 prod=343 delta=0
hunks=0 landings=0 judge_diff=False`. The judge's remaining quote failure is
`<module>.Quote.run_individual_transform`; `run_tick_socket` is gone from the failure list.

## negatives
- The ticket's framing ("emit the RETURN-terminated else arm where the original ran it") is **not
  expressible in Python source**: an `else:` clause cannot be interleaved into the middle of its own
  then-body. Measured original layout (`@66 →@528`, try body exits `@138 JUMP_FORWARD →@684`,
  else `@528..@682` RETURN, continuation `@684`) proves the original source had the continuation
  **dedented out of the if/else**, so the actionable move is to hoist the continuation, not the arm.
  Both descriptions produce the same linear order; only the hoist is emittable.
- Membership is confirmed **not** the blocker (independent of the prior engineer): this patch does
  not touch `region_analyzer.py` at all, does not prune double-claimed block 684, and still makes the
  unit Equal. The double claim is harmless here because `then_blocks` is a *set of arms*, and the
  hoist is an arm-boundary decision.
- 6 of 8 fires are no-ops (byte-identical products) — handlers/strategy/trade_info_utils hoist the
  tail to a place where another channel already emitted the same statements. They are inert, not
  harmful; kept because narrowing them away needs a jump-target predicate (forbidden).
- An instrumented probe at the same emission point was `cmp`-proven byte-identical on quote before
  the mechanism was written; the shipped fire print goes to stderr only and the 12 unchanged census
  products are the proof it does not perturb.
- 3.11 has no `order_instructions` block-reordering pass, which is what licenses reading the
  pyc's linear order as source order; on 3.10-and-earlier pyc files this predicate's ③ would lose
  that guarantee (not exercised by this corpus — single-interpreter 3.11.7 throughout).
- Repo HEAD moved during the run (e28cade6 → 9a7d3c02); both new commits are ledger-only, and the
  sealed generator at the new HEAD is still `c16daa4f87dc68e6` == my pristine, so the patch applies
  to current sealed bytes. `git status core/` in the repo is empty (no repo writes).

## declaration
**LANDED-READY.** Delivered file is NOT byte-identical to sealed (it flips the victim unit).
- Criterion: `_if_generate_normal` in `core/cfg/region_ast_generator.py:21341` + `:22182` — the else
  arm's max-offset block ends in `RETURN_VALUE|RETURN_CONST|RAISE_VARARGS` ∧ some then block's offset
  is above it ∧ some is below ∧ not an elif chain ⇒ build the then body from the head blocks only and
  emit the above-else (i.e. post-if) then blocks after the `If` node, at the owning region.
- Deliverable: `D:/Temp/r35a/DELIVER/region_ast_generator.py`, sha256 **`ac8ec5aa2d5796ea…`**,
  59746 lines (**+55 / −2**, 3 hunks) over pristine `c16daa4f87dc68e6…`; `py_compile` OK;
  `cmp` mirror == deliver (IDENTICAL). The earlier intermediate build `f7e97ae6d5e22bb1` differed
  only by the 5-line `[R21-15 FIRE]` stderr census print, whose removal left quote and broker
  products `cmp`-identical.
- Final readings taken with the delivered bytes: quote **91/92**, broker **121/128**, quotation
  **153/153** (`pyc_verify single --source` on products regenerated by this file).
- Revert: `cp D:/Temp/r35a/wt/pristine/region_ast_generator.py D:/Temp/r35a/wt/core/cfg/region_ast_generator.py`
  (the repo was never written; `git status --porcelain core/` is empty).
- Not disturbed: `_generate_try` arm-tail ownership (gate 27) and `_generate_ternary` merge
  remainder (gate 21) — neither is re-anchored; both landed remainder channels still run ahead of the
  new one in the same order, and 12 of the 14 census products are byte-for-byte unchanged.

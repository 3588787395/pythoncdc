# FIX_R21-13 — r32a — combined landing: r25b continue-pad + lock try/finally emission order

Engineer: r32a · repo READ-ONLY `rr-v3r01-f557fd` @ `3fa09986` (never written, no git
mutation, no `gate_round.py`/`gate_chain.py`, no `*OK.py` into the repo).
Owned file (mirror only): `core/cfg/region_ast_generator.py`.
READ-ONLY consulted: `core/cfg/region_analyzer.py` (report only — NOT edited).

## mirror proof

`mkdir -p /d/Temp/r32a/{wt,pristine,DELIVER}` then from the repo
`cp -r pycdc.py core parsers utils bytecode scripts /d/Temp/r32a/wt/`.
sha256 first-16 re-read **inside the mirror** (files over the brief's numbers):

| file | sha16 | brief expected |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `c16daa4f87dc68e6` | `c16daa4f87dc68e6` ✓ |
| `core/cfg/region_analyzer.py` | `35e227ac3e7b25af` | `35e227ac3e7b25af` ✓ |
| `core/cfg/ast_generator_v2.py` | `beeaf14435e22922` | (read-only) |
| `core/cfg/comprehension_generator.py` | `7d8acab92ccc7782` | (read-only) |

`pristine/region_ast_generator.py` = mirror copy, `cmp` byte-identical, same `c16daa4f87dc68e6`.
Mirrors `D:/Temp/r25b`, `D:/Temp/r30a`, `D:/Temp/r31a` were NOT touched. All products in
`D:/Temp/r32a/out/`, written by `tools/regen.py` (in-process `pycdc.decompile_pyc`, `newline=''`).

## baseline

Unpatched mirror reproduces the brief exactly (judge = repo `scripts/pyc_verify.py single
<pyc> --source <fresh mirror product>`, always `--source`):

| file | UNPATCHED |
|---|---|
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | **120/128** ✓ |
| `fly/data/quote.pyc` | **90/92** ✓ |
| `fly/data/quotation.pyc` | **153/153** ✓ (sentinel) |

Sealed shapes (`unit_diff … --all`) at UNPATCHED:
`_process_order len orig=507 prod=42 delta=-465`; `_process_cancel_order orig=333 prod=40 delta=-293`.

## sealed-emission measurement (why the lock try/finally is emitted last)

Out-of-band only (`tools/dump_regions.py`, a separate process, after `analyze()`; never used
to make an artifact):

```
LIST ORDER (_process_cancel_order): LoopRegion@46, TryExceptRegion@98, TryExceptRegion@420,
    BoolOpRegion@1608, IfRegion@1100/998/946/926/690/608/514/420/332/312, Region@0
LOOP entry 46  children: [IfRegion@312, IfRegion@332]      ← TryExceptRegion@98 is NOT a child
blk@96/@98/@200/@252/@306 → region=TryExceptRegion@98, that region's parent = IfRegion@312
IfRegion@312.blocks = {44,312,332,350,418,442,…,1930}      ← contains NONE of 96/98/200/252/306
LoopRegion.body_blocks = [46,96,98,200,252,306,312,…]      ← ASCENDING, order already correct
```

=> the analyzer's *ordering* is right; the *parent/children declaration* is wrong: the lock
`try/finally` region is adopted by its own **successor** IfRegion (which does not hold its
blocks), so the loop never sees it as a child.

In-generator trace (`tools/probe.py`, line-print only, **PROVEN INERT**: `cmp out/broker.PROBE.py
out/broker.COMB.py` → identical, 3067 lines / 175556 B). Reading the emitted source at
`out/broker.R25B.py:423-497` shows the group present but LAST inside the `while` body:
`delete orig[15..48 @@98..@316] del=33` paired with `insert … prod[399..440] ins=41`
= a pure relocation, not DCE. Site named:

* `region_ast_generator.py:8377-8405` (`_loop_generate_body`, the `_anc_r405 is region`
  deferral branch of the ascending `for block in region.body_blocks:` walk) — the walk
  `continue`s on @96/@98/@200/@252/@306 trusting "the parent region will emit them"
  (`_parent_gen` is False), but that parent never holds them;
* the text is then produced by a tail path (`_loop_postprocess` →
  `_if_generate_branch_stmts(body_blocks_no_header)` at `:14280-14286`, and/or the global
  leftover pass) and appended to `body_stmts` ⇒ last statement of the loop body;
* trace lines: `PRB SKIPCAND off=98 reg=98 parent=312 pgen=False holds=False` (×5 blocks),
  and `PRB POST … tryregs=[]` for the same loop (`_loop_collect_child_regions:8540` collects
  only from `region.children`, which lacks it).

## prior-criterion re-verification (r25b, `446c82d884448ecf`)

The banked candidate file is stale in a second way: besides adding 42 lines at
`_process_if_blocks`' empty-BREAK-pad path, its base **lacks the landed R27-9 try/except/else
arm-tail block** (its diff deletes `region_ast_generator.py` 30885-30941). It was therefore
NOT installed; only its `+` hunk was re-applied onto the current sealed bytes by
`tools/patch_r25b.py`, anchored by CONTENT (5-line context: the
`generated_blocks/generated_offsets/continue` trio + `stmts.append({'type': 'Break'})`) and
re-derived index = pristine line **25706** (unique, `ANCHOR_HITS=1`).

Measured effect on today's sealed bytes (reproduces the brief):

```
_process_order         prod 42  -> 448   delta -465 -> -59   hunks 4 -> 20  landings 1 -> 14
_process_cancel_order  prod 40 -> 303    delta -293 -> -30   hunks 3 -> 6   landings 0 -> 3
```
Panel with r25b criterion ALONE (tag `R25B`, fresh products, `--source`):
`broker 120/128 · quote 90/92 · quotation 153/153 · wizard 57/58 · klinedata 63/64 ·
handlers 29/30 · event_source 12/13 · api_base 27/28 · strategy 26/27 · risk_init 42/43 ·
trade_info_utils 38/41 · order_api 37/37 · matcher 17/17` → **zero flips, zero decreases**
(the banked FALSIFIED reading re-confirmed on today's bytes).

## 判据实现

**R32A-1** = r25b criterion verbatim, `region_ast_generator.py:25739-25780` (deliver line
numbers), inside `_process_if_blocks`, `if role in (BlockRole.BREAK, BlockRole.PURE_BREAK)`'s
empty-`_meaningful_instrs` path, immediately before `stmts.append({'type': 'Break'})`:
`self._current_loop` exists ∧ every non-exception successor of the block lies in
`_r25b_loop.blocks` ∧ one of them `is` its header/condition/back-edge block ∧ some predecessor
ends `JUMP_BACKWARD(_NO_INTERRUPT)` landing exactly on it ⇒ emit nothing, mark generated.

**R32A-2** (new, generator-side emission-order) — `region_ast_generator.py:8404-8434`,
deliver lines; pristine single line `if not _parent_gen and not _is_loop_structural_r08:`
replaced by:

```python
_r32a_parent = getattr(_blk_region_r405, 'parent', None)
_r32a_parent_holds = (_r32a_parent is not None and block in _r32a_parent.blocks)
if (not _parent_gen and _r32a_parent_holds and not _is_loop_structural_r08):
    continue
```

Predicate: defer a block to its owning region's parent **only if that parent actually holds
the block** (`block in parent.blocks`, the same read the walk already performs at `:8407` and
`:8371`). If the declared parent does not own the block, the deferral can never be honoured,
so the block stays on the ascending `body_blocks` walk and is dispatched at its own position
(the existing pre-flush at `:8438-8465` recognises `@98` as `_is_child_entry_pre` via
`get_entry_region_for_block` and emits the whole `TryExceptRegion` there). No post-hoc pass,
no statement deletion, no sibling/parent-region content read beyond the child-entry idiom
already in the function, no cross-level heuristic. `_parent_gen`-True, parent-holds, and
loop-structural cases are byte-unchanged (`[C3]`).

## readings

`_process_order` before → after (UNPATCHED → R32A-1 → R32A-1+R32A-2 = `COMB2`):
```
prod   42  -> 448 -> 448          delta -465 -> -59 -> -59
hunks   4 ->  20 ->  19
delete orig[15..48 @@98..@316] del=33   ->  GONE
insert  … prod[399..440] ins=41         ->  shrinks to ins=8 (prod[432..440])
```
`_process_cancel_order`:
```
prod   40 -> 303 -> 334 (orig 333)   delta -293 -> -30 -> +1   hunks 3 -> 6 -> 5
delete orig[15..46 @@98..@310] del=31 ->  GONE
residual: del 1 @@924 (JUMP_BACKWARD) · rep 1/2 @@1606 (JUMP_FORWARD) · del 1 @@1824 ·
          ins 1 @@1930 · rep 1/2 @@2042   →  jump-target/landing family, `Different control flow`
```
Panel with BOTH criteria (`COMB2`, 14 files, `--source` on fresh products):
`broker 120/128 · quote 90/92 · quotation 153/153 · wizard 57/58 · real_quote 44/45 ·
klinedata 63/64 · handlers 29/30 · event_source 12/13 · api_base 27/28 · strategy 26/27 ·
risk_init 42/43 · trade_info_utils 38/41 · order_api 37/37 · matcher 17/17`
→ **no decrease anywhere, no flip anywhere**; the bar (`_process_order` or
`_process_cancel_order` Equal ⇒ 121/128) is NOT met.

Fire census (R32A-2, product-level, `cmp out/<f>.R25B.py out/<f>.COMB2.py` over all 14
files, every code object of each file compiled by the same regen):

```
broker FIRES (175556 -> 175536 bytes)
quote NOFIRE · quotation NOFIRE · wizard NOFIRE · real_quote NOFIRE · klinedata NOFIRE ·
handlers NOFIRE · event_source NOFIRE · api_base NOFIRE · strategy NOFIRE · risk_init NOFIRE ·
trade_info_utils NOFIRE · order_api NOFIRE · matcher NOFIRE
TOTAL_FIRES = 1  (1 of 14 files; 13/14 products byte-identical)
R32A-1 census (r25b criterion, same method): broker-only, delta -465/-293 -> -59/-30,
13 other products byte-identical (re-confirmed by r25b report §7.2 and by my R25B panel).
```

## negatives

1. **Zero flips.** The reorder is real and large (`_process_cancel_order` delta −30 → **+1**,
   i.e. the product is now *longer* than the original and its lock group sits at the right
   offset), but the judge still says `Different control flow`: the 5 residual hunks are
   jump-target/landing differences, the family the campaign already proved has **no landing
   channel in the generator** (AST carries no jump operands).
2. `_process_order` cannot be flipped by this mechanism at all: −59 is spread over 17 further
   hunks (`del=15 @@1638`, `del=10 @@1758`, `del=9 @@2646`, `del=8 @@2092`, `del=7 @@2394`, …)
   = other mechanisms, consistent with "broker needs seven distinct mechanisms for 128/128".
3. The **root defect is an analyzer declaration I may not edit**: `TryExceptRegion@98.parent`
   is set to its successor `IfRegion@312` (and `IfRegion@318` for `_process_order`), a region
   whose `blocks` contain none of `@96/@98/@200/@252/@306`, and consequently
   `LoopRegion@46.children == [IfRegion@312, IfRegion@332]`. Named hosts (READ, not edited):
   `core/cfg/region_analyzer.py:221-233` `Region.add_child` (first-adopter-wins:
   `if child.parent is not None and child.parent is not self: return` — an early wrong
   adoption is permanent) and the try-nesting adoption site
   `region_analyzer.py:9925-9935` (`region_b.add_child(region_a)`, keyed on `try_offset_start`
   pairing, with no `block ⊇ containment` test); the WithRegion adoption at
   `:13773-13775` was read and is not on this unit's path. A correct-at-identification fix
   there = "a container may only adopt a child whose blocks it holds" — that single predicate
   would make my R32A-2 guard redundant. **I did not attempt it (file ownership).**
4. My first attempt at R32A-2 was inverted (`and not _r32a_parent_holds`) and produced a
   product byte-identical to the r25b-only build (`cmp` proved it): caught by measurement,
   not by reasoning. The inverted form would ALSO have been the broad one (it changes the
   parent-holds population), which is how this campaign lost −20 and −4 units.
5. Instrumentation hygiene: every probe was `cmp`-proved per target; a probe that changed
   bytes would have been labelled VOID. `tools/probe.py` is NOT in the deliverable
   (mirror file restored from `out/gen.COMB2.py`, `sha16 a34cdcf4a4ae7147` = delivered).
6. Line-ending incident, self-reported: `tools/patch_r32a2.py`'s inserted block was written
   with bare LF (31 lines) because the patch script itself is LF. Detected by repr dump;
   normalised (`\r\n` canonical, bare-LF count now 0) so pristine lines are byte-identical
   to sealed. Deliverable is pure CRLF.
7. `pyc_verify` was always run with `--source` on my own fresh products (the stale in-place
   product was never consulted; I did not touch the repo's `*OK.py`).

## declaration

**FALSIFIED (zero-flip) — do NOT install as a landing.** Both criteria are measured,
narrow (1/14 files fire), and improve the sealed shape dramatically
(`_process_cancel_order` −293 → +1, `del=33` lock hunk eliminated; `_process_order`
−465 → −59, same hunk eliminated), but no unit reaches `Equal`, so broker stays
**120/128** and no other judged file changes. The remaining defect on both victims is
(a) a jump-landing family with no generator channel and (b) the analyzer parent/children
declaration named in §negatives-3 — **BLOCKED-BY-FILE-OWNERSHIP for that part**.

* Delivered (whole file, patched): `D:/Temp/r32a/DELIVER/region_ast_generator.py`
  59 765 lines · 3 758 660 bytes · pure CRLF · 0 bare LF.
* sha256 first-16 **`a34cdcf4a4ae7147`** (pristine sealed `c16daa4f87dc68e6`).
* diff vs pristine: **74 changed lines** = 73 added + 1 removed
  (`REPLACE 8404..8404 -> 8404..8434`, `INSERT at 25708 -> 25739..25780 (+42)`).
* `py_compile` → OK, 2 547 030-byte pyc at `D:/Temp/r32a/out/deliver_compile.pyc`.
* Repo untouched; the 402-file gate was NOT run; mirror left PATCHED so these readings are
  reproducible from `D:/Temp/r32a/wt`.
* Reproduce: `python -X utf8 D:/Temp/r32a/wt/tools/regen.py <repo>/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc D:/Temp/r32a/out/broker.COMB2.py`
  → `3067 lines / 175536 bytes` (deterministic, matches `out/broker.COMB2.py`).
* Revert (mirror scratch):
  `cp /d/Temp/r32a/pristine/region_ast_generator.py /d/Temp/r32a/wt/core/cfg/region_ast_generator.py`
  verify `python -X utf8 -c "import hashlib;print(hashlib.sha256(open(r'D:/Temp/r32a/wt/core/cfg/region_ast_generator.py','rb').read()).hexdigest()[:16])"` → `c16daa4f87dc68e6`.
* Bank for the next round: **R32A-2 is reusable** (1/14 fires, removes the mis-positioned
  lock group, no regression) but must be paired with an analyzer adoption-guard
  (`region_analyzer.py:9925-9935` / `Region.add_child` containment) to reach Equal.

# FIX R21-16 — fly/data/quote.pyc :: Quote.run_individual_transform (two-fix ticket, analyzer-side)

## 0. Ticket as received
R21-16: get `core/cfg/region_analyzer.py` (and ONLY it) so that
`fly/data/quote.pyc :: <module>.Quote.run_individual_transform` reads
`delta=0 hunks=0 landings=0 judge_diff=False` and the file flips `91/92 -> 92/92`.
Two independently-measured analyzer defects:
1. (fixed & banked by Variant D) `TryExceptRegion@686` declared with empty `try_blocks`;
   `_collect_body` BFS walks past `POP_EXCEPT` and swallows pre-handler blocks (586/638/640/684).
   Variant D split `_collect_body_raw(entry,_r2116_pe_stop=False)` + a two-pass wrapper -> `delta -52 -> -3`.
2. (this ticket's work) the residual `delta=-3` is a handler-suite relocation: instructions that
   belong at `@752..@1114` are emitted at `@1260+`. The return-`None` tail-threading hypothesis is
   RETIRED (not re-tested). Generator half disallowed (AST carries no jump operands).
Acceptance bar / panel / hygiene as given. Deliverables: `FIX_R21-16.md`,
`CANDIDATE_region_analyzer.py` (whole file) — only if §3 met with no panel regression.

## 1. Mirror + sealed-hash + cmp proof
Mirror rebuilt clean from the READ-ONLY repo (`pycdc.py core parsers utils bytecode scripts`,
all `__pycache__` stripped; `.trae/.../unit_diff.py` copied at the same relative depth):
`D:/Temp/r46/wt`.
Sealed hashes verified in the mirror:
- `core/cfg/region_ast_generator.py = 7d336164eff5bf65`  (matches ticket)
- `core/cfg/region_analyzer.py      = 35e227ac3e7b25af`  (matches ticket)
Fidelity proof: regenerated `quote.pyc` with the sealed mirror -> `D:/Temp/r46/out/quoteOK_baseline.py`
(94155 B) `cmp`-IDENTICAL to the repo's committed `site-packages/fly/data/quoteOK.py`.
=> **mirror VALID**.
Prior engineer's in-flight patch (`D:/Temp/r34/wt`, sha16 `f2bb527550ecf03c`) is byte-identical to the
repo `CANDIDATE_R21-16_variantD_region_analyzer.py` — i.e. it IS Variant D. Reproduced on my mirror:
`delta=-3 hunks=3 landings=2`, file `91/92`, `run_tick_socket` Equal. Kept as the base; my two new
criteria are layered on top of it (+26/-1 lines in the analyzer).

## 2. Baseline readings (quote, run_individual_transform; `--all`, `--source` judged)
| state | len orig/prod | delta | hunks | landings | judge | file |
|---|---|---|---|---|---|---|
| sealed analyzer (`35e227ac`) | 407 / 355 | -52 | 10 | 3 | Different control flow | 91/92 |
| Variant D (`f2bb5275`) | 407 / 404 | -3 | 3 | 2 | Different control flow | 91/92 |

## 3. 取证 (root-cause census)
### 3.1 Which collector line stole which blocks (defect 1, Variant D, confirmed)
The pre-entry swallow (586/638/640) originates in
`_extract_except_handler._collect_body_raw` at the successor walk past the POP_EXCEPT-cleanup
block (`region_analyzer.py:11349`); Variant D's `_r2116_pe_stop` second walk cuts it. Verified.

### 3.2 Which mechanism relocates @752..@1114 -> @1260+ (defect 2)
An **inert else-attribution probe** (`cmp`-proved byte-identical, `PROBE INERT`) inside
`_identify_try_except_regions` showed the inner `TryExceptRegion@686` (entry=686,
handler_entry=754) came out of `_find_try_else_blocks` with
`else_offs = [1050,1112,1116,1240,1282,1354,1396,1468,1510,1578,1620,...,2116]`
(i.e. it swallowed the whole `if message:` else + the entire stocks tail as a spurious try/except/**else**).
Mechanism: in `_find_try_else_blocks`, the `[R3-I]` handler->merge guard
(`region_analyzer.py:12244 _r3i_handler_reaches_merge`) BFS follows the handler's
**backward** edge (the inner handler ends in `continue`: block @1024 POP_EXCEPT-cleanup ->
block @1032 `JUMP_BACKWARD to 586` = loop head). Re-entering the loop, it reaches the post-try
merge and falsely returns `_handler_reaches_merge=True`, so the `else` interval `[precise_handler_end,
merge_point)` collects everything. The same code path already carries the `[R10/W10]` backward-jump guard
in the Pattern-TE branch (`:12096-12104`) but the R3-I branch lacked it.

compile() proof (3.11.7): the try/except/else vs try/except(continue)+sequential distinction.
- `try: A  except E as x: B  else: C`  -> body A, **C (else) first**, JUMP_FORWARD, **B (handler) last**.
- `try: A  except E as x: B; continue  C(sequential)` -> body A, JUMP_FORWARD->C, **B (handler) right
  after body** (`@752 JUMP_FORWARD to 1116 / @754 PUSH_EXC_INFO`), C last. The second matches the
  ORIGINAL layout (`@754` handler immediately after the body); the first matches the PRODUCT layout
  (handler at `@1260+`). Delta between them = exactly the relocation.

### 3.3 Census after fix (inert `analyze()` ownership probe, `PROBE INERT`)
- `TryExceptRegion@686` try_blocks=[686], handler_entry=[754], handlers=[[BaseException,x,[772,774,1024]]].
- `TryExceptRegion@640` (outer) try_blocks include the flat 1032, 1050, 1112, 1116, 1240...
- Ownership of the relocated blocks: block@1032, @1050, @1112, @1116 all -> `TryExceptRegion@640`.
A second inert probe inside `_collect_body` (`_first` walk from entry=772) showed the first walk
returns `[...,638,640,684,686,...]` (< 772 -> pre-entry swallow -> pe_stop second walk fires). The pe_stop
cut at the POP_EXCEPT-cleanup block@1024 was dropping the legitimate trailing `continue` block@1032 from
the handler body (`[772,774,1024]`, no 1032) — that is why the handler lost its `continue`.

## 4. Criterion as implemented (2 additive rules, +26/-1 lines, `region_analyzer.py` only)
**Fix #2a — R3-I backward-jump guard (symmetric to the banked [R10/W10]).** In
`_find_try_else_blocks`'s `_r3i_handler_reaches_merge` BFS, when the current block's last real
(non RESUME/NOP/CACHE) instruction is a `BACKWARD_JUMP_OPS` edge (continue/break/back-edge),
do NOT expand its successors — the handler terminated abnormally and does not complete into the
merge. Fires `GUARD_SKIP run_individual_transform merge=1116@handler=686` (exactly the victim, once).
Closes the 62-instruction relocation: `delta -3 -> 0`.

**Fix #2b — pe_stop keeps a pure-backward-jump handler terminator.** In `_collect_body_raw`, when the
`_r2116_pe_stop` second walk cuts at a POP_EXCEPT-cleanup block, if that block's normal (non-exception)
successor is a standalone block whose ONLY real instruction is a backward jump (continue/break),
append that block to the handler body without expanding past it. Restores the inner handler's
`continue`. Fires `PESTOP_ADD ... blk=1032` (and `blk=1112`). Closes `@1032 JUMP_BACKWARD`:
`hunks 3 -> 2`.
Gated identically to Variant D (only when the first walk provably swallowed a pre-entry block), so it
cannot truncate a well-formed handler (`run_tick_socket` stays Equal).

## 5. Post-patch victim reading + fire census + quotation + panel
Victim (`quoteOK_fix2b.py`, sha256 of analyzer `8efe7f0040241138`, product 93066 B, reproducible):
```
run_individual_transform  len orig=407 prod=407 delta=0 hunks=2 landings=2 judge_diff=True
[single] status=failure units=91/92   run_tick_socket NOT in failures (stays Equal)
```
Remaining hunks (both = the SAME single block, the `else: warning` message-falsy branch, relocated):
```
== delete orig[171..180 @@1050..@@1114]  del=9   (self.log.quote.warning('逐笔数据返回为空') + JUMP_BACKWARD)
== insert prod[263..272] @1558..         ins=9   (same block emitted AFTER the stocks then-tail)
landings: orig[109] @682 POP_JUMP_IF_FALSE ->idx171 vs prod @684 ->idx263 ;
          orig[271] @1620 JUMP_FORWARD ->idx366 vs prod @1556 ->idx271
```
Fire census (inert counters, quote product `cmp`-identical when instrumented): across
`quote, quotation, handlers, broker` the two criteria fire ONLY in `quote::run_individual_transform`
(1 GUARD_SKIP + 2 PESTOP_ADD). Zero fires on the other three.

14-file panel (`python -X utf8 D:/Temp/t30/panel14.py D:/Temp/r46/wt fix2b 0 14`, `--source`-judged):
**TOTAL_FIRES = 1** — only `quote.pyc` product byte-CHANGED; every other file byte-**SAME** vs sealed,
no unit count decreased.

| file | size | vs sealed | units |
|---|---|---|---|
| fly/data/quotation.pyc | 182759 | SAME | 153/153 |
| **fly/data/quote.pyc** | 93066 | **CHANGED** | 91/92 (delta -3->0, hunks 3->2) |
| IQCommon/api/klinedata.pyc | 102772 | SAME | 64/64 |
| IQCommon/logger/handlers.pyc | 9068 | SAME | 29/30 |
| IQCommon/strategy/wizard_quant_api.pyc | 34541 | SAME | 58/58 |
| IQCommon/util/trade_info_utils.pyc | 61281 | SAME | 38/41 |
| IQData/api/api_base.pyc | 33228 | SAME | 27/28 |
| IQData/plugins/.../real_quote.pyc | 53841 | SAME | 45/45 |
| IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | 13021 | SAME | 27/27 |
| IQEngine/plugins/.../order_api.pyc | 34308 | SAME | 37/37 |
| IQEngine/plugins/.../trade_live_broker.pyc | 178207 | SAME | 121/128 |
| IQEngine/plugins/.../matcher.pyc | 13299 | SAME | 17/17 |
| IQEngine/plugins/.../realtime_event_source.pyc | 20555 | SAME | 12/13 |
| IQEngine/plugins/.../risk_calculation/__init__.pyc | 55531 | SAME | 43/43 |

## 6. Negative evidence (with numbers)
- The residual after #2a+#2b is NOT another collector line and NOT tail threading: it is the placement of
  the single `else: warning` block. compile()-proven (3.11.7) on the isolated while-body:
  - shape4 `if message: try/except(continue)+stocks  else: warning(continue)` ->
    layout `handler, stocks, warning` (stocks BEFORE warning). `hunks` unchanged for this block => WRONG.
  - shape5 `if message: try/except(continue) else: warning(continue); <stocks AFTER the if>` ->
    layout `handler, warning@before, stocks` — matches ORIGINAL (`@682 ->warning@1050`, handler `@754`,
    warning+`@1114` continue, `@1116` stocks = post-if merge). CORRECT.
  => The fix must re-attribute blocks 1116+ (`stocks`/`deques.appendleft`) as the **post-`if/else` merge**
  of the `if message:` IfRegion (and give the `else` its own `continue` block@1112), not the then-tail.
- This is the documented high-risk "ordering wall": `_identify_conditional_regions` ->
  `_collect_branch_blocks(then_succ, merge, then_stop)` (`region_analyzer.py:20461`), where `merge` is the
  nearest common post-dominator of then/else. Because the `else` branch ends in `continue` (no fall
  through to the merge), no common post-dominator exists, so the then-walk runs the try's forward-success
  jump into 1116 and absorbs it as then-tail. Prior campaign stop-set patches in this site reported
  "zero flips + 4 regressions"; my two additive criteria deliberately do NOT touch this site (they fire on
  1/14 panel files). A bounded merge re-attribution was NOT attempted this gate because the blast radius is
  every no-common-post-dominator `if/else` with a nested try-success jump, which the 14-file panel would
  very likely regress; the safe, measured improvement is delivered instead.

## 7. Declaration
FALSIFIED as a candidate (does not meet §3 acceptance: file is NOT flipped — `run_individual_transform`
still `delta=0 hunks=2 landings=2 judge_diff=True`, file `91/92`).

Delivered as the largest honest measured partial: on top of banked Variant D, two provably-narrow,
zero-regression analyzer criteria (R3-I backward-jump guard + pe_stop keep-pure-continue) take
`run_individual_transform` from `delta=-3 hunks=3` to `delta=0 hunks=2`, `len prod 404 -> 407`,
TOTAL_FIRES=1 (quote only), all 13 other panel files byte-identical, `run_tick_socket` Equal.
Candidate: `D:/Temp/r46/DELIVER/CANDIDATE_region_analyzer.py` (`8efe7f0040241138`, pure CRLF, compiles).

NEXT TICKET (must be analyzer-side, `region_analyzer.py`): the final hunk is a conditional-region
merge re-attribution in `_identify_conditional_regions` (~`:20461`) / `_collect_branch_blocks`, keyed on
`if message:` region `entry=640 else_blocks=[1050]`:
(1) let the `else` branch own its trailing `continue` block@1112 (mirror of fix #2b, but on the
IfRegion else-collection); (2) set the IfRegion `merge_block = block@1116` and exclude 1116+ from
`then_blocks` when the `else` arm has no fall-through to the merge (ends in continue/break/return), so
`stocks`/`deques.appendleft` are emitted as post-`if/else` siblings (shape5). Region census to hand off:
`IfRegion@640 then=[686(try),1116,1240,...], else=[1050], leaked-continue-blocks=[1112(warning),1032(already
fixed)]`; bytecode layout required = `@752 JUMP_FORWARD->@1116(stocks)`, handler `@754..@1032(continue)`,
else `@1050..@1114(continue)`, stocks `@1116..@1620 JUMP_FORWARD->2116(after-outer-try)`.
Must be validated with the 14-file panel; expect api_base/strategy/handlers to be the first regressions if
the merge rule is not keyed tightly enough.

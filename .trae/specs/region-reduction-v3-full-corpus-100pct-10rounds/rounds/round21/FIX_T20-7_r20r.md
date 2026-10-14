# FIX_T20-7 — r20r — ternary-consumed-span silent discard (build_current_period_df)

Branch `rr-v3r01-f557fd` @ HEAD `fef79e80`. File owned: `core/cfg/region_ast_generator.py` ONLY.
Sealed hashes re-read (task quotes verified, no drift):
- region_ast_generator.py = `e17603a761eaadef`
- ast_generator_v2.py = `beeaf14435e22922`
- region_analyzer.py = `640d33a77dcb71c2`

(Live doc; appended as I work.)

## mirror build proof
- `cp -r pycdc.py core parsers utils bytecode scripts` + `cp --parents -r` of the 6 battery dirs at identical depth into `/d/Temp/r20r/wt`.
- sha256(16) self-certify: region_ast_generator.py e17603a761eaadef=repo, ast_generator_v2.py beeaf14435e22922=repo, region_analyzer.py 640d33a77dcb71c2=repo, pycdc.py cf4e2705ab042732=repo. All IDENTICAL. Task's quoted hashes match the copied files (no drift).
- Regenerated `fly/data/quote.pyc` product in mirror → `/d/Temp/r20r/out/quote_base_OK.py` → `cmp` vs repo committed `site-packages/fly/data/quoteOK.py`: **IDENTICAL**. Mirror executes landed bytes.

## Stage 1 baseline (unpatched mirror; generated + judged with pyc_verify single --source)
quote 86/92 · klinedata 63/64 · handlers 29/30 · wizard_quant_api 55/58 · trade_info_utils 38/41 · api_base 27/28 · real_quote 43/45 · strategy 26/27 · realtime_event_source 12/13 · risk/__init__ 42/43 · trade_live_broker 118/128 · [SENT] quotation 153/153 · matcher 17/17 · order_api 37/37. **ALL match the quoted baseline exactly.**
Victim unit_diff baseline reproduced: `len orig=123 prod=113 delta=-10 hunks=1 landings=0 judge_diff=True`.

## per-unit 取证 (build_current_period_df)
Original tail bytecode (from dis):
```
@506 POP_JUMP_FORWARD_IF_FALSE to 512   # cond: nowdataframe.loc['Row_sum']['is_open'] != 0
@508 LOAD_CONST 1 / @510 JUMP to 514    # true value 1
@512 LOAD_CONST 0                        # false value 0
@514 BUILD_LIST                          # MERGE block: [1 if .. else 0]
@516 LOAD_FAST tempdict / @518 'is_open' / @520 STORE_SUBSCR   # tempdict['is_open'] = [..]
@524 LOAD_GLOBAL NULL+pandas ... @556 CALL / @566 STORE_FAST tmp   # tmp = pandas.DataFrame(tempdict, index=index)
@568 LOAD_FAST tmp / @570 RETURN_VALUE   # return tmp
```
CFG: merge_block=@514, instrs [514,516..568,570]. Ternary region entry=118 merge=514 blocks=[118,508,512,514] merge_context='store' container_type='list'.
Baseline product emits ONLY: `tempdict['money'] = [...]` then bare `[1 if ... else 0]` (Expr) — i.e. container branch :45840-45841 appended `Expr(List([IfExp]))`, then the marking loop :46118-46121 marks @514 fully generated (also re-marked by caller :18008), so @516..@570 (the `tempdict['is_open']=` STORE, `tmp=DataFrame(...)`, `return tmp`) are silently discarded.
Recording subclass confirmed: @514/@508/@512 each marked generated at BOTH :46121 (inside _generate_ternary) and :18008 (caller _if_generate_then_branch). Un-marking @514 alone cannot work (parent re-walks @514 and cannot rebuild the on-stack list value). Correct fix must COMBINE container value with the post-store assignment + emit the remainder — which `_try_build_ternary_store_assign` (called with the container as value) already does (it scans the first STORE_*, rebuilds everything after it into region.post_consumer_extra_stmts).

## 判据实现 (the exact change + predicate — NOT blank)
File: `core/cfg/region_ast_generator.py`, inside `_generate_ternary`.
Change = 18-line insertion at source line 45841 (new block spans 45841–45858 in the delivered file);
the repo's original line `results.append({'type': 'Expr', 'value': container_info})` is preserved as the
fall-through of the new block, so this is strictly additive.

PREDICATE (the ternary's own merge_block, no sibling-region read):
```
if region.merge_block is not None:
    _c_mb_instrs = [i for i in region.merge_block.instructions
                    if i.opname not in ('RESUME', 'NOP', 'CACHE')]
    if any(i.opname in ('STORE_SUBSCR','STORE_ATTR','DELETE_SUBSCR') for i in _c_mb_instrs):
        _c_store_assign = self._try_build_ternary_store_assign(region, ternary_expr)
if _c_store_assign is not None:
    results.append(_c_store_assign)
    results.extend(region.post_consumer_extra_stmts or [])
    for block in region.blocks: self.generated_blocks.add(block)
    return results
```
Rationale in spec terms: the ternary's CONSUMED SPAN of merge_block is the container value expression
(`@514 BUILD_LIST` wrapping the IfExp). When a STORE_* (STORE_SUBSCR/STORE_ATTR/DELETE_SUBSCR) still
follows in the same merge_block, the consumed span does **not** cover the block ⇒ the container branch
must not emit a bare `Expr` and mark the whole block consumed. Instead the ternary region — which OWNS
merge_block under unique membership — emits the full assignment whose value is reconstructed by
replaying `before_store` from `[ternary_expr]` (BUILD_LIST re-folds the IfExp into the list), and delegates
the post-store remainder to `_try_build_ternary_store_assign`, which already rebuilds everything after the
first STORE into `region.post_consumer_extra_stmts` (`tmp = pandas.DataFrame(tempdict, index=index)`, `return tmp`).
Shape = the `_gt_exclude_merge` in-function precedent (a merge_block coverage test evaluated from the
owned region), realized as "emit the remainder as statements here" because the then-branch caller re-marks
(see below).

## stage readings (patched, mirror-generated, judged with pyc_verify single --source)
Victim `<module>.Quote.build_current_period_df`:
  baseline: `delta=-10 hunks=1 landings=0 judge_diff=True`  →  patched: `delta=0 hunks=0 landings=0 judge_diff=False` (unit now Equal).
Panel: quote 86→**87**/92 · klinedata 63/64 · handlers 29/30 · wizard_quant_api 55/58 · trade_info_utils 38/41 · api_base 27/28 · real_quote 43/45 · strategy 26/27 · realtime_event_source 12/13 · risk/__init__ 42/43 · trade_live_broker 118/128.
Sentinels: quotation 153/153 · matcher 17/17 · order_api 37/37.  NO decrease.
Batteries (ROOT=D:\Temp\r20r\wt ⇒ patched): repro RED=9/9 (=9R/9) · arm 0G/3R · ccneg 3G/1R · retbreak 2G/2R DRIFT_VS_BASELINE=0 · orderapi 5G/0R · tail 13G/0R.  ALL at recorded baseline.

## 负面证据 (banked)
1. The `_gt_exclude_merge` "do-not-declare-consumed" shape at :46121 ALONE cannot fix this victim: a
   recording `generated_blocks` subclass proved block @514 (and @508/@512) is marked consumed at BOTH
   :46121 (inside `_generate_ternary`) AND :18008 (caller `_if_generate_then_branch`). Excluding @514 at
   one site is undone by the other; and if @514 were left unclaimed, the parent `_generate_block_statements`
   could not rebuild the container value (it lives on the stack from the anchored entry @118, not re-loaded
   in @514). ⇒ the correct mechanism for this dispatch is EMIT-THE-REMAINDER, not un-mark.
2. The discarded hunk is NOT only the tail @524–@568: the `tempdict['is_open'] =` STORE itself (@516–@520)
   is dropped too, because the container branch emits a bare `Expr(List([IfExp]))`. Reconstructing @516..
   standalone would back-fill the store RHS as phantom `None`. Only replaying `before_store` from
   `[ternary_expr]` (BUILD_LIST re-folds IfExp→list) yields the correct `tempdict['is_open'] = [1 if … else 0]`.
3. Task's quoted hash `region_ast_generator.py = dff6e81a5f2ff9f6` does NOT match the copied file;
   the landed bytes are `e17603a761eaadef` (as the task itself corrected). No other hash drift.

## final declaration
LANDED-READY. Single mechanism, file `core/cfg/region_ast_generator.py` only, one 18-line additive insertion
at :45841. Produces a named unit flip (quote 86/92→87/92) with zero panel/sentinel/battery movement.
Delivered file: `D:/Temp/r20r/DELIVER/region_ast_generator.py`, sha256 first-16 = `4f295dfc6ebd2caa`, py_compile OK.
Revert command (restore sealed bytes; repo file was never written and is still `e17603a761eaadef`):
    git -C D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main checkout HEAD -- core/cfg/region_ast_generator.py

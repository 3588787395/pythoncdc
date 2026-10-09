# FIX T19-4 — ternary condition fused with an *unclosed host-call prefix* (order_api)

Verdict: **LANDED-READY** (stages 3-6 all pass on the mirror; see the readings below).

Target: `site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc`
units `35/37` → `37/37`.

## 1. Files delivered (whole files, byte-exact, line endings preserved)

| file | delta | note |
|---|---|---|
| `DELIVER/region_ast_generator.py` | +276 / −0 lines, 2 hunks | the criterion + the reduction route |
| `DELIVER/ast_generator_v2.py` | +33 / −1 lines, 4 hunks | **also changed** — needed so the reduction route can fold the fused ternary branches |

Both mirror copies are pure-CRLF like the originals (`region_ast_generator.py` keeps
its leading BOM; `ast_generator_v2.py` has none). The live repo's two files were
hash-checked before and after the work and are untouched (`sha256 5066b136…` /
`e1e0dcda…`, identical to the pristine copies used for the baseline arm).

### Why `ast_generator_v2.py` is in scope

`_generate_container_construction_region`'s route hands the block instructions to
`self.expr_reconstructor.reconstruct(...)`, and that reconstructor folds a fused
ternary branch into an `IfExp` through `_open_ternary_region` /
`_track_ternary_region` / `_close_ternary_region` — but `_open_ternary_region` was
only ever called for the `POP_JUMP_*_IF_NONE / IF_NOT_NONE` polarity
(`ast_generator_v2.py:755`, single call site). For the `POP_JUMP_FORWARD_IF_FALSE`
polarity that order_api uses, the stream's two branch pushes were never folded, so
`reconstruct` returned garbage (`Call(func=Constant 'sell', …)`). The patch adds the
IF_FALSE/IF_TRUE polarity to **the same** open/track/close mechanism behind an
opt-in switch (`reconstruct(..., fold_cond_jump_ternary=True)`, default off, reset in
`reset()`), so every existing call path stays byte-identical; the reduction route is
the only caller that turns it on.

## 2. The criterion as landed (verbatim from the code comment)

`_ternary_host_call_prefix_span` (region_ast_generator.py, right after
`_generate_container_construction_region`):

> **【判据】只读栈效应与指令族，不读名字/常量/绝对偏移/块数阈值：**
> 1. 区域条件块末为条件跳转，前向模拟块体（跳转之前）的值栈得净深 R，
>    跳转弹出条件值后仍残留 L = R - 1 >= 1 个元素——即跳转时栈上除条件
>    之外还压着下层元素（既有 `_ternary_nested_in_container_construction`
>    的栈深判据，本判据补上它 docstring 第 3 条逃逸的另一半）。
> 2. 沿 merge 链继续前向模拟（每步「弹条件 + 臂压回一个结果」净值 0，
>    两条臂不重复计数），链上**第一个把栈深降到 L 以下的指令属于调用
>    消费族**（CALL/PRECALL/…）：它消费的元素在跳转时就已经活着，
>    所以栈底那些元素不是「若干彼此独立的已求值表达式」，而是一个尚未
>    闭合的调用构造（宿主调用的接收者与已成型实参）。⇒ 该跳转不是语句级
>    分派，三元是嵌套表达式，不得作为顶层 TernaryRegion 独立归约。
>    若先降到 L 以下的指令属于其它族（STORE_*/POP_TOP/BINARY_SUBSCR…），
>    栈底属于别的结构（如 `d[k] = (a if c else b)` 的赋值目标 d/k），
>    返回 None，保持既有行为。
> 3. 同一条链继续模拟直到栈深回到 0（该语句整体被消费）；链上经过的全部
>    块（条件块 + 两侧臂块 + merge 块，含同一语句内的兄弟三元）的指令，
>    按 offset 排序，即整体归约为**一个**表达式的跨度。
> 模拟不可靠（效应不可得、栈下溢、臂非纯值块、链断裂/成环、跨度未闭合）
> 一律返回 None。

Supporting structural requirements landed in the same function (no names/constants):
* arm blocks must be pure value blocks (net stack effect `+1`, all successors == merge,
  no conditional jump inside) — otherwise bail;
* the depth-zero closing instruction must be a statement-level consumer
  (`POP_TOP` / `STORE_*` / `RETURN_VALUE` / `RETURN_CONST`), else bail;
* the span's instruction offsets must be hole-free;
* in-block statements before the last stack-depth-zero crossing are taken by the
  existing `_split_block_condition_prefix` and emitted as their own statements
  (prefix), and the closing block's instructions *after* the crossing are emitted
  as their own statements (tail) — the span only owns what it consumes;
* stack effects come only from `_instruction_stack_effect` (reused; no second table);
  the call-family / close-family tests are opcode-family membership sets.
* `steps < 64` is a walk bound (hang guard), not part of the discriminator.

Hook site: `_generate_ternary`, immediately after the existing
`_ternary_nested_in_container_construction` arm — a bail (`None`) leaves the whole
existing path untouched and marks nothing.

## 3. Measured readings, baseline vs patched (mirror `D:/Temp/r19t1`)

### Stage 1 — mirror reproduces baseline (unpatched)
* `repro_orderapi/run_orderapi.py` → `GREEN=2 RED=3 / 5`
  (o1 failure, o2 success, o3 success, o4 failure, o5 failure)
* order_api via mirror → `status=failure units=35/37`
  (`<module>.future_order`, `<module>.option_order` failing)
* live-file sha256 of both deliverable files == mirror pristine copies (no drift).

### Stage 3 — battery gate
* patched: `GREEN=5 RED=0 / 5` (o1/o4/o5 flipped to success; o2/o3 stay success).

### Stage 4 — order_api gate
* patched: `status=success units=37/37 success_rate=100.00%`.
* Product text now carries the host statements, e.g. line 222
  `strategy_log.info('生成订单，…'.format(order_id=order_.order_id, symbol=order_.symbol, side='买入' if …`
  (baseline folded them into bare `return`s).

### Stage 6 — product compiles
* `python -X utf8 -m py_compile D:/Temp/r19t1_prod_final.py` → OK.

### Stage 5 — collateral batteries (must stay exactly as baseline)

| battery | baseline | patched | same? |
|---|---|---|---|
| `round19/repro_orderapi` | GREEN=2 RED=3 / 5 | GREEN=5 RED=0 / 5 | intended flip |
| `round14/repro_arm/run_arm.py` | GREEN=0 RED=3 / 3 | GREEN=0 RED=3 / 3 | yes |
| `round14/repro_ccneg/run_ccneg.py` | GREEN=3 RED=1 / 4 | GREEN=3 RED=1 / 4 | yes |
| `round14/repro/run_repro.py` | RED=9 / 9 (all `units=1/2`) | RED=9 / 9 (all `units=1/2`) | yes |
| `round18/repro_retbreak` (no runner: `pycdc --region` + `pyc_verify single` per file) | GREEN=2 RED=2 / 4 (r01,r02 red; r03,r04 green) | GREEN=2 RED=2 / 4 (same arms) | yes |

Text-level check (equal counts are not "unchanged emission"): after the patched run its
products were stashed, the pristine pair re-installed, all four collateral batteries
re-run, and `diff -rq` over `$TEMP/r14arm`, `$TEMP/r14ccneg`, `$TEMP/r14repro`,
`$TEMP/r18rb_base` returned **no product-text differences at all** — the collateral
batteries emit byte-identical products on baseline and patched arms.

### Stage 5 — corpus panel, no unit-count decrease

Same mirror, same `$TEMP` product dirs, unpatched arm then patched arm
(`pycdc.py --region` + `scripts/pyc_verify.py single --source`). The 16 named files
plus the 5 alternates for the ambiguous basenames (`handlers`, `api_base`,
`strategy` ×2, `bar`):

| pyc (under `site-packages/`) | baseline | patched | delta |
|---|---|---|---|
| IQCommon/api/klinedata.pyc | 63/64 | 63/64 | 0 |
| IQCommon/logger/handlers.pyc | 29/30 | 29/30 | 0 |
| IQCommon/strategy/wizard_quant_api.pyc | 55/58 | 55/58 | 0 |
| IQCommon/util/trade_info_utils.pyc | 38/41 | 38/41 | 0 |
| IQData/api/api_base.pyc | 27/28 | 27/28 | 0 |
| IQData/plugins/plugin_system_realquote/real_quote.pyc | 43/45 | 43/45 | 0 |
| IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | 26/27 | 26/27 | 0 |
| IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc | 12/13 | 12/13 | 0 |
| IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43 | 41/43 | 0 |
| IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | 118/128 | 0 |
| fly/data/quote.pyc | 86/92 | 86/92 | 0 |
| IQEngine/plugins/plugin_system_matcher/matcher.pyc | 17/17 | 17/17 | 0 |
| fly/data/quotation.pyc | 153/153 | 153/153 | 0 |
| IQEngine/core/bar.pyc | 85/85 | 85/85 | 0 |
| IQEngine/core/strategy/strategy_universe.pyc | 11/11 | 11/11 | 0 |
| fly/dumpload/load_daily.pyc | 27/27 | 27/27 | 0 |
| IQEngine/utils/logger/handlers.pyc (alt) | 17/17 | 17/17 | 0 |
| IQEngine/api/api_base.pyc (alt) | 49/49 | 49/49 | 0 |
| IQEngine/core/strategy/strategy.pyc (alt) | 20/20 | 20/20 | 0 |
| IQCommon/strategy/strategy.pyc (alt) | 2/2 | 2/2 | 0 |
| IQEngine/plugins/plugin_fly_data/local_variables/bar.pyc (alt) | 22/22 | 22/22 | 0 |

DOWN count: **0** / 21 files.

## 4. Intermediate negative arms (measured, then fixed — not shipped)

First build (span = whole blocks, full-block `generated_blocks` marking, no prefix/tail
recovery) reached `GREEN=5 RED=0` and `37/37` but regressed the corpus panel:

* `fly/data/quotation.pyc` 153/153 → **152/153**, new failure
  `<module>.get_quote: Different bytecode`; unit diff showed
  `log, is_trade = getLogger()` swallowed by the host statement
  `quote = Quote(log, 'trade' if is_trade else 'backtest')` (the maximal straight-line
  cond block holds a *completed* statement before the expression prefix).
* `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` 118/128 → **116/128**,
  new failures `<module>.TradeLiveBroker.fund_transfer` (line 2997, offset 186) and
  `<module>.TradeLiveBroker.market_fund_transfer` (line 3020, offset 144), both
  `Different bytecode`; unit diff showed the `return False` / `return True` statements
  swallowed (they sit in the closing block *after* the statement's `POP_TOP`).

Tentative variant "mark only fully-covered blocks as generated" fixed o5 badly instead
(`GREEN=4 RED=1 / 5`, o5 back to bare ternaries) because the unmarked closing block got
re-dispatched; it was reverted. The shipped build keeps whole-span block marking **and**
emits the prefix / tail instructions of the touched blocks as their own statements
(reusing `_build_statements_from_instructions`), which restores both corpus files to
baseline while keeping `GREEN=5 RED=0 / 5` and `37/37`.

Also re-measured as still-falsified (per DIAG §3, not retried here beyond the sanity
check that the mirror baseline matches the doc): the `_EXPR_REGION_TYPES` removal and
the `child_expr_regions` bypass.

## 5. Residual risk / notes for the landing gate

* The new arm keys on `reconstruct(...)` returning a *statement* node or a
  `POP_TOP`/`RETURN_VALUE` closing instruction; everything else bails conservatively, so
  the blast radius is limited to cond blocks whose residual stack is eaten by a later
  `CALL`/`PRECALL`.
* `fold_cond_jump_ternary` is off by default, but the full 402-file gate (label 19 vs 18)
  and `pytest` are the authority for byte-level side effects — not run in this mirror.
* Scratch/logs live in `D:/Temp/r19t1_diag/` (`coll_base.log`, `coll_patch3.log`), products
  in `D:/Temp/r19t1_collateral/{base,patch2,patch3}/`; final order_api product
  `D:/Temp/r19t1_prod_final.py`.

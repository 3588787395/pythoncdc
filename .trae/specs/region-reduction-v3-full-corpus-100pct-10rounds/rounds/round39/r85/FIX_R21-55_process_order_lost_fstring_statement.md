# FIX_R21-55 — `_process_order` lost statements: which class, and the builder that returns the empty arms

Ticket: R21-55 (pre-assigned). Unit `<module>.TradeLiveBroker._process_order` in
`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`.
Working mirror `D:/Temp/r85` (plain gate-38 landed bytes, no banked base).

## §0 Mirror certification + premise check (measured, not copied)

Landed bytes copied from the read-only repo (`core/ scripts/ parsers/ utils/ bytecode/ pycdc.py`):

```
core/cfg/region_ast_generator.py  sha16=11324f276cce6d5b  bytes=3846610   (brief says 11324f276cce6d5b ✓)
core/cfg/region_analyzer.py       sha16=f7d849e974904492  bytes=2104888   (brief says f7d849e974904492 ✓)
python = 3.11.7 ; pyc magic = 3.11
```

Base product regenerated with `python -X utf8 pycdc.py --region -o out_base/trade_live_broker.py <abs pyc>`:

```
[single] status=failure units=126/128 success_rate=98.44%
  ***<module>.TradeLiveBroker._process_order: Failure: Different control flow
  ***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow
```

⇒ brief's "file reads 126/128" **confirmed**; the two failures are exactly the two named units, so
the four canaries (`ipo_stocks_order`, `_process_cancel_order`, `_trade_status_handle`,
`etf_purchase_redemption`) are Equal at base.

Ticket anchors in `region_ast_generator.py` (re-verified present on today's landed bytes):
`_try_wrap_fstring_pending_call` def :51128 ✓, `[R21-27b]` callee-stack helper :51079 ✓,
tail-call-pair rule :51157 ✓, prefix-window fixes :45344 / :45367 / :45471 ✓, call site :45558 ✓,
wrapper-tried-first fallback :51680 ✓ (line numbers shifted by +0; verified by grep, see §1).

## §1 Full unfiltered window list on TODAY's landed bytes (re-derived with `allwin_r63.py`)

```
len orig=507 prod=439 delta=-68      hunks=14
#1  delete orig[266..281 @1638..@1710] del=15 ins=0
#2  delete orig[287..288 @1754..@1754] del=1  ins=0
#3  delete orig[289..299 @1758..@1796] del=10 ins=0
#4  delete orig[340..348 @2092..@2152] del=8  ins=0
#5  delete orig[357..360 @2230..@2234] del=3  ins=0
#6  delete orig[369..370 @2304..@2304] del=1  ins=0
#7  delete orig[371..374 @2308..@2312] del=3  ins=0
#8  delete orig[383..384 @2390..@2390] del=1  ins=0
#9  delete orig[385..392 @2394..@2426] del=7  ins=0
#10 replace orig[393..401 @2430..@2490] del=8 ins=1
#11 delete orig[410..413 @2568..@2572] del=3  ins=0
#12 delete orig[422..423 @2642..@2642] del=1  ins=0
#13 delete orig[424..433 @2646..@2690] del=9  ins=0
#14 insert prod[395..396]              del=0 ins=1
```

Brief's re-measurement (`len orig=507 prod=439 delta=-68`, window #1 = `del 15 @1638..@1710`) is
**confirmed exactly**. Correction to the brief: plain `unit_diff.py` reports `hunks=14` here as well,
so on this unit the sub-3 filter is *not* under-counting; the allwin list above is what a `unit_diff`
run yields, with per-window detail. The count that matters is that **13 of 14 windows are pure deletes**.

## §2 The 15-instruction window is class (a), not class (b) — measured

Original instruction stream around the window (from `dis.get_instructions` on the pyc code object):

```
@1632 POP_JUMP_FORWARD_IF_FALSE to 1802      (the `if is_stock(order.symbol):` test)
@1634 LOAD_CONST '股票' / @1636 STORE_FAST type_str
@1638 LOAD_GLOBAL NULL+strategy_log / @1650 LOAD_ATTR info / @1660 LOAD_GLOBAL NULL+_
@1672 LOAD_CONST '生成订单，订单号：' / @1674 LOAD_FAST order / @1676 LOAD_ATTR order_id / @1686 FORMAT_VALUE str
@1688 LOAD_CONST ' ' / @1690 LOAD_FAST type_str / @1692 FORMAT_VALUE str
@1694 LOAD_CONST '代码：' / @1696 LOAD_FAST order / @1698 LOAD_ATTR symbol / @1708 FORMAT_VALUE str
@1710 LOAD_CONST ' 数量：' / @1712 LOAD_FAST order / @1714 LOAD_ATTR entrust_direction
@1724 LOAD_GLOBAL EntrustDirection / @1736 LOAD_ATTR BUY / @1746 COMPARE_OP == / @1752 POP_JUMP_FORWARD_IF_FALSE to 1758
@1754 LOAD_CONST '买入' / @1756 JUMP_FORWARD to 1760
@1758 LOAD_CONST '卖出' / @1760 FORMAT_VALUE str / @1762 LOAD_FAST order_amount / @1764 FORMAT_VALUE str
@1766 BUILD_STRING / @1768 PRECALL / @1772 CALL / @1782 PRECALL / @1786 CALL / @1796 POP_TOP
@1798 EXTENDED_ARG / @1800 JUMP_FORWARD to 2912
```

i.e. **one** statement
`strategy_log.info(_(f'生成订单，订单号：{order.order_id!s} {type_str!s} 代码：{order.symbol!s} 数量：{"买入" if order.entrust_direction == EntrustDirection.BUY else "卖出"!s}{order_amount!s}'))`
in which the conditional expression sits *inside an f-string interpolation*: its test is the tail of
the block that carries the whole statement, its true arm `@1754` is a lone `LOAD_CONST`, and its merge
`@1760` resumes the same statement (FORMAT_VALUE → BUILD_STRING → CALL → CALL → POP_TOP).

What the product emits there (source, `_process_order` body lines 41-45 of `out_base/trade_live_broker.py`):

```
type_str = '股票'
if order.entrust_direction == EntrustDirection.BUY:
    """买入"""
else:
    """卖出"""
```

and its compiled form (windows #1-#3 prod side) is
`LOAD_FAST order / LOAD_ATTR entrust_direction / … / COMPARE_OP == / POP_JUMP_FORWARD_IF_FALSE / JUMP_FORWARD`
— an **empty then arm and an empty else arm**, i.e. exactly the `POP_JUMP_IF_FALSE / JUMP_FORWARD / NOP`
skeleton the ticket names as class (a). Interpreter fact verified by direct `compile()` probe
(`if x: """buy""" else: """sell"""` → `PJF→12 / JF→14 / NOP`): CPython 3.11 discards a
constant-string expression statement, so the rendered arms compile to nothing.

So the statement is *absent* (class (b) symptom) **because** it was replaced by an empty-arm if
skeleton (class (a) mechanism). The two classes are one defect on this unit; the ticket's separation
("class (b) is not class (a)") is **falsified by the product bytes**: the surviving skeleton carries
the ternary's *test* and drops its *arms* — a class-(a) signature — while the *host statement* is the
casualty. Windows #4-#13 are the same signature at the `.format(side=… if … else …, oper=… if … else …)`
sites in the option/future branches, i.e. ternary-as-call-argument proper.

Consequence for the fix: the site is an expression-level conditional whose host statement must be
restored; nothing here is a jump-landing or placement problem.

## §3 Ablation result — the rejecting predicate is pinned, and it is a single named line

The empty arms are **not** produced by a declined generator-side wrapper; the
`TernaryRegion` never exists. Line-intersect probe (`work/trace_r2155.py`, `sys.settrace`
restricted to `_detect_ternary_pattern` frames of `_process_order`) — all four loss-site
candidate blocks walk to the very end of the detector and are declined by one statement:

```
candidate @1634 -> true_block=1754 false_block=1758 merge_block=None value_target=None
                   has_jump_forward_skip=False  -> line 26141 `return None`
candidate @2236 -> true_block=2304 false_block=2308 merge_block=None ... -> 26141
candidate @2310 -> true_block=2390 false_block=2394 ...                 -> 26141
candidate @2574 -> true_block=2642 false_block=2646 ...                 -> 26141
```

`region_analyzer.py:26130-26141` is `[R47 消费点守卫]`:

```python
if (merge_block is None and value_target is None and not has_jump_forward_skip):
    return None
```

and its own comment names this very shape ("try-except 内的 f-string inline if-else，异常边使
`find_nearest_common_post_dominator` 返回 None … 交由 IfRegion 按语句级结构归约"). The consequence
of handing it to `IfRegion` is the measured loss: the probe of the landed region list shows

```
IfRegion @1634  condition_block=1634 then=[1754] else=[1758] merge=1760  IF_THEN_ELSE
IfRegion @2236  blocks=[2236, 2304, 2308]      IfRegion @2310  blocks=[2310, 2390, 2394]
IfRegion @2574  blocks=[2574, 2642, 2646]      (no TernaryRegion anywhere in _process_order)
```

`_generate_region` therefore renders `if <tail of the block>: <const> else: <const>`, CPython
compiles the constant arms away (§2), and the *host statement* carried by the same block dies with
them. So the ticket's "use ablation to find which builder returns the empty arms" answer is:
**no builder returns empty arms — the analyzer refuses to declare the expression-level region at
`26141`, and `IfRegion`'s ordinary statement renderer gets an expression-level diamond it cannot
represent.** The wrapper `_try_wrap_fstring_pending_call` is never reached, because its input
(a TernaryRegion) does not exist.

## §4 Why `merge_block` is None although the diamond is complete (measured, `work/probe_merge_r2155.py`)

```
true_block  @1754 instrs=[LOAD_CONST '买入', JUMP_FORWARD 1760]  successors=[1760, 3026]  preds=[1634]
false_block @1758 instrs=[LOAD_CONST '卖出']                      successors=[1760, 3026]  preds=[1634]
join        @1760 instrs=[FORMAT_VALUE, LOAD_FAST order_amount, FORMAT_VALUE, BUILD_STRING 9,
                          PRECALL, CALL, PRECALL, CALL, POP_TOP, JUMP_FORWARD 2912]  preds=[1754, 1758]
find_nearest_common_post_dominator({1754,1758}) = None
```

`3026` is the `except BaseException` handler: the CFG builder attaches an **exception edge to every
block inside the try range**, so each arm has a second successor that bypasses `@1760`; no block
post-dominates both arms and the post-dominator query answers None. The join is nonetheless
uniquely determined by normal-completion structure: the true arm's unconditional `JUMP_FORWARD`
target is a block that is also a successor of the false arm and whose predecessor set is **exactly**
the two arms (`preds=[1754, 1758]`). Both arms are single-value blocks (`_is_ternary_block` already
accepted them), so every normal path out of the diamond carries exactly one value into `@1760`,
which consumes it (`FORMAT_VALUE`). Recovery from successor/predecessor structure is therefore a
proof, not a preference; `[R47]` declines only because the *post-dominator* instrument is blinded.

## §5 Population census BEFORE editing (probe is read-only; landed bytes untouched)

Rig: `work/census_r2155.py` (full pipeline, 20 panel files, `sys.settrace` on
`_detect_ternary_pattern` frames) and `work/census_r2155_corpus.py` (analyzer-only, 406 pyc,
8 shards). The predicate under census is `_r2155_diamond_join`, textually the predicate that
`build_cand_r85a_r2155.py` installs.

**Membership / counting rule (cite this rule, not a bare number):**
`EVAL` = the guard statement `region_analyzer.py:26138` executed by `_detect_ternary_pattern`;
`REJECT` = its body `:26141` executed (i.e. `merge_block is None and value_target is None and
not has_jump_forward_skip`); `FIRE` = a REJECT whose `true_block/false_block` satisfy the
predicate, **deduplicated by (code object, condition block)** — one candidate block examined by
several passes counts once.

Panel (20 files, chunks of 7+7+6, `work/census_p*/census_r2155.json`):

| file | EVAL | REJECT | FIRE |
|---|---|---|---|
| trade_live_broker.pyc | 15 | 7 | **6** |
| quotation 12 / quote 16 / klinedata 33 / handlers 0 / wizard_quant_api 1 / trade_info_utils 3 / api_base 8 | 73 | 0 | 0 |
| real_quote 8 / strategy 1 / order_api 6 / matcher 5 / realtime_event_source 0 / risk_calculation 12 | 47(excl. broker) | 0 | 0 |
| arg_checker ×3 (2/2/2), profiler_func ×3 (0/0/0) | 6 | 0 | 0 |
| **panel total** | **126** | **7** | **6** |

All 7 rejects — and therefore all 6 fires — are in `<module>.TradeLiveBroker._process_order`
(`@1634, @2092, @2236, @2310, @2430, @2574`) plus one non-firing reject in
`market_fund_transfer:@126`.

Corpus-wide (analyzer-only, **406 pyc**, 8 shards ≤ 20 s each, `work/CENSUS_r2155_corpus.log`):

```
files scanned=406   EVAL=361   REJECT=10   FIRE=6
files with REJECT>0:  IQCommon/util/fileio_utils.pyc  eval=4 reject=3 fire=0
                      IQEngine/.../trade_live_broker.pyc eval=15 reject=7 fire=6
files with FIRE>0:   ['IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc']
```

So the signature's whole-corpus action surface is exactly the six loss sites of the target unit
(6 of the unit's 14 windows are 1:1 with a site; windows #2/#3, #5-#7, #8-#9, #11-#13 are the
arm/continuation pieces of the same statements). One load error in the census (`email_utils.py.pyc`,
`Unsupported magic number: 0x6F532023` — a text file named .pyc), same as the campaign's 402-file gate.

**Control that proves the predicate is not "any reject":** `market_fund_transfer:@126` has
`true_block @242` and `false_block @352`, both ending in `POP_JUMP_FORWARD_IF_FALSE`
(`work/probe_merge_r2155.py`), i.e. two statement-level branches. Conjunct ① (unconditional
forward jump) and conjunct ③ (false arm not a conditional jump) each decline it independently.

Probe inertness: the census only reads `frame.f_locals` and calls a pure predicate; the products
produced under the traced census are the same as the untraced ones — verified in §6 by comparing
`changed files` base vs probe.

## §6 The two halves, measured (delta / windows / judge side by side; products certified)

Mirror bytes per row; every product regenerated with
`python -X utf8 pycdc.py --region -o <out> <abs pyc>` after deleting the old output.

| variant | bytes installed (sha16) | `_process_order` | judge line | broker product |
|---|---|---|---|---|
| base (landed) | gen `11324f276cce6d5b` / ana `f7d849e974904492` | `orig=507 prod=439 delta=-68 hunks=14` | `units=126/128` (`_process_order`, `_sync_worker` Different control flow) | `a6d6deb78a5a5eac` 179259 B |
| A = [R21-55] analyzer diamond-join recovery (6 fires) | ana `842e2748bcdfeb66` | `delta=-97 hunks=4` | **`units=126/128`** (no flip; windows #1-#3 closed, `.format` sites degraded) | `9221e0d00361b40d` 178383 B |
| B = A + conjunct ⑥ (join head must consume) | ana `9a1fdd46e9cc6325` | `delta=-33 hunks=11` | `units=126/128` | `10d6f2dada1e725e` 179205 B |
| C = [R21-55c] generator arm-tolerates exception-entry successor | gen `45796ca24b371a8c` | `delta=-68 hunks=14`, **product byte-identical to base** | `units=126/128` | `a6d6deb78a5a5eac` (== base) |
| **A+C (the pair)** | gen `45796ca24b371a8c` + ana `842e2748bcdfeb66` | **`orig=507 prod=507 delta=0 hunks=0`** | **`units=127/128`, only `_sync_worker` failing ⇒ `_process_order` Equal** | `f25d834a6b0d763e` 179288 B |

Co-requisite proof, not preference: C alone changes **0 of 20** panel products (it only relaxes the
arm test of `_ternary_host_call_prefix_span`, which is never reached until A creates the sibling
`TernaryRegion`s); A alone is a **regression** (`-68 → -97`) because the sibling regions exist but
their host-call span is refused. Only the pair flips the unit. `_sync_worker` (the other failing
unit, not mine) is untouched by the pair: `-3 / 5 windows` on both base and A+C products.

Why B is not installed: B narrows A to the single site whose join head consumes the value; it is a
strict improvement over base (`-68 → -33`) but it does not flip, and the pair A+C closes the whole
unit, so B is kept only as the narrower-blast-radius alternative if a gate ever rejects A.

## §7 20-file panel: byte census + judge (A+C vs base)

`work/panel_r85.py` / `work/judge_r85.py`; logs `work/PANEL_base.log`, `work/PANEL_AC.log`,
`work/PANEL_base_judge.log`, `work/PANEL_AC_judge.log`.

```
changed files = 1     (IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
                       a6d6deb78a5a5eac 179259 B  ->  f25d834a6b0d763e 179288 B)
DECREASES = 0         panel unit total 927 -> 928
quotation.pyc 153/153   quote.pyc 92/92   order_api.pyc 37/37
realtime_event_source 12/13 (clock_worker unchanged)   klinedata 64/64  handlers 30/30
matcher 17/17  wizard_quant_api 58/58  trade_info_utils 41/41  api_base 28/28
real_quote 45/45  strategy 27/27  risk_calculation 43/43
arg_checker 33/50, 36/43, 43/43   profiler_func 13/18, 11/18, 18/18   (all unchanged)
broker: 126/128 -> 127/128, only remaining FAIL = <module>.TradeLiveBroker._sync_worker
```

The four canaries of the target file (`ipo_stocks_order`, `_process_cancel_order`,
`_trade_status_handle`, `etf_purchase_redemption`) do not appear in the failure list ⇒ Equal.

## §8 Membership rule and remaining scope

* Corpus signature population (rule stated in §5, same rule for A): **FIRE = 6** under A
  (all in `_process_order`: `@1634, @2092, @2236, @2310, @2430, @2574`), **FIRE = 2** under B
  (`@1634`, `@2310`), out of **EVAL=361 / REJECT=10** corpus-wide over 406 pyc. Two independent
  rejects decline: `market_fund_transfer:@126` (arms end in conditional jumps) and
  `fileio_utils` 3 rejects (0 fires). So the criterion's corpus-wide action surface is the target
  unit's six sites, and `changed files = 1` confirms it at the product level.
* C's action surface is not a new claim on the population: it only relaxes `_adopt_arm`'s
  "arm must have no other successor" test for successors that are exception-entry blocks, and with
  the landed analyzer it changes 0 of 20 panel products.
* Remaining on this file: `_sync_worker` (not this ticket). The ticket's own conclusion is
  superseded on one point: `_process_order` **does** flip with this pair — the ticket's "17 windows
  must all close, and no criterion can do it alone" was right that a single criterion is not enough,
  but the two criteria (analyzer join recovery + generator arm tolerance) are the same root fact
  seen at two levels: **the CFG's exception edges are attached to every block inside a try range,
  and both the post-dominator query and the arm-successor query treat them as normal paths.**

## §9 Deliverable manifest + repo cleanliness

`D:/Temp/r85/DELIVER/`

| file | sha16 | role |
|---|---|---|
| `build_cand_r85a_r2155.py` | — | rebuild [R21-55] analyzer half from landed `f7d849e974904492` |
| `build_cand_r85b_r2155.py` | — | rebuild variant B (A + conjunct ⑥) from the same landed bytes |
| `build_cand_r85c_r2155.py` | — | rebuild [R21-55c] generator half from landed `11324f276cce6d5b` |
| `CANDIDATE_r85a_r2155_diamond_join_region_analyzer.py` | `842e2748bcdfeb66` | analyzer candidate (pair half 1) |
| `CANDIDATE_r85b_r2155_diamond_join_consumption_region_analyzer.py` | `9a1fdd46e9cc6325` | narrower analyzer variant (banked alternative) |
| `CANDIDATE_r85c_r2155_generator_arm_exc_successor.py` | `45796ca24b371a8c` | generator candidate (pair half 2) |
| `MEASURED_r85_base_broker_product.py` | `a6d6deb78a5a5eac` | base product (landed bytes) |
| `products/MEASURED_r85_{A,B,C,AC_pair}_broker_product.py` | `9221e0d0…` `10d6f2da…` `a6d6deb7…`(=base) `f25d834a…` | one per variant |
| `census/`, `panel/`, `rigs/` | — | panel + 406-pyc census JSONs and logs, halves' window dumps, probe/trace/census/panel/judge rigs |

* **Install = the pair A+C** (`842e2748bcdfeb66` + `45796ca24b371a8c`), not B, not A alone, not C alone.
* Reproducibility re-verified: each builder re-run from the landed bytes produces byte-identical
  output (`work/repro/{a,b,c}.py` compared to the delivered files), all three BOM + all-CRLF, no
  `\r\r\n`, `py_compile` OK.
* Repo untouched: `git status --porcelain -- core/ site-packages/ scripts/ parsers/ utils/ bytecode/
  pycdc.py` = 0 lines; the mirror is restored to the landed bytes
  (`11324f276cce6d5b` / `f7d849e974904492`).

Probe inertness, measured rather than asserted: the same in-process pipeline
(`build_cfg -> RegionASTGenerator.generate -> CFGASTConverter -> CFGCodeGenerator`) run twice,
without and with the census trace installed on `RegionAnalyzer.analyze`, produces the identical
module source — `f1d9b96066fe0e27`, 167194 chars both — while the counters reproduce independently
(`eval=15 reject=7 fire=6`, the same six sites plus the `market_fund_transfer:@126` non-firing reject).

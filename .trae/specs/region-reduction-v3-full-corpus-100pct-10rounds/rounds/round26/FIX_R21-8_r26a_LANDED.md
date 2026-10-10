# FIX_R21-8 — ticket R21-8 · broker `_process_tick_order` loop-declaration mismatch

Engineer: r26a · branch `rr-v3r01-f557fd` · HEAD `76b54549`
Owned file: `core/cfg/region_analyzer.py` ONLY.
Victim: `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
unit `<module>.TradeLiveBroker._process_tick_order`.

## Status log (appended while working)

- [x] mirror build + self-certify hashes
- [x] Stage 1 baseline on UNPATCHED mirror (119/128 reproduced)
- [x] signature re-verification (loop declarations printed; ticket axis FALSIFIED, real defect one level down)
- [x] 判据实现 — region_analyzer.py:21219-21292 in _build_basic_if_region (def :20723)
- [x] stage readings (panel + batteries + fire census + byte-cmp collateral)
- [x] 负面证据 (6 items)
- [x] final declaration: LANDED-READY, sha256 first-16 35e227ac3e7b25af, py_compile OK, revert command given


## Mirror build proof
`/d/Temp/r26a/wt` from repo HEAD `76b54549`, `cp -r pycdc.py core parsers utils bytecode scripts`
+ `cp --parents -r` of the six battery dirs. `sha256sum` first-16 in the mirror:
```
b7f3076323813787  core/cfg/region_analyzer.py          (== brief)
5043790fbeaca162  core/cfg/region_ast_generator.py     (== brief, sealed)
7d8acab92ccc7782  core/cfg/comprehension_generator.py  (== brief)
beeaf14435e22922  core/cfg/ast_generator_v2.py         (== brief)
```
pristine copy kept at `/d/Temp/r26a/pristine/` (core/parsers/utils/bytecode/scripts/pycdc.py/.trae).
D:/Temp/r25b mirror NOT used.

## Stage 1 baseline (UNPATCHED mirror, products in D:/Temp/r26a/out)
`trade_live_broker.pyc` = units=119/128 (gen 5 s) -> MATCHES brief.
Shape (`unit_diff.py --all`, run from the REPO rig against the MIRROR product
`D:/Temp/r26a/out/s1_broker/IQEngine_plugins_plugin_system_trade_trade_live_broker.py`):
```
len orig=182 prod=182 delta=0
   ~ orig[30] @178 JUMP_BACKWARD ->idx22 | prod[30] @178 JUMP_BACKWARD ->idx19
hunks=0 landings=1 judge_diff=True
```
idx22 = orig @130 `LOAD_GLOBAL len` (loop header re-test), idx19 = prod @114
`LOAD_FAST self` (outer loop condition test) => the prod back edge lands 3 instrs EARLIER.

## Signature re-verification — what the loop declarations ACTUALLY are
Out-of-band probe (`D:/Temp/r26a/out/probe_loops.py`, mirror on sys.path, reads AFTER
`analyze()` returned, no product written). `<module>.TradeLiveBroker._process_tick_order`
(188 instrs, firstlineno 941) -> `analyze()` returns LIST of 8 regions:
```
[0] WHILE_LOOP  entry=114  exit=None  nblocks=15  parent=WHILE_LOOP
[1] WHILE_LOOP  entry=46   exit=None  nblocks=2   parent=WHILE_LOOP
[2] WHILE_LOOP  entry=46   exit=None  nblocks=18  parent=None            (is_while_true=True)
[3] TRY_FINALLY entry=182  nblocks=5  parent=WHILE_LOOP
[4] IF_ELIF_CHAIN entry=446 exit=1132 nblocks=4  parent=WHILE_LOOP
[5] IF_THEN_ELSE  entry=402 exit=1132 nblocks=6  parent=WHILE_LOOP
[6] IF_THEN       entry=130 exit=180  nblocks=2  parent=WHILE_LOOP   <== the defect
[7] BASIC         entry=0   nblocks=1
```
loop[0] (= real source `while self.before_trading_start:`): entry=b[@114]
last=`POP_JUMP_FORWARD_IF_FALSE(1132)`; header_block=b[@130..176] last=
`POP_JUMP_FORWARD_IF_FALSE(180)`; condition_block=@114; back_edge_block=
b[@724..1130] last=`POP_JUMP_BACKWARD_IF_TRUE(130)`; body_blocks starts=
130,178,180,182,290,342,396,402,444,446,558,560,610,724; else/init/break = EMPTY.
loop[1] (= `while not self.before_trading_start: time.sleep(60)`): entry=@46
last=`POP_JUMP_FORWARD_IF_TRUE(114)`, header_block=@60, back_edge_block=@60 (itself),
body_blocks=[@60].  ENTRY != HEADER here TOO — and this loop DECOMPILES CORRECTLY.
loop[2] (`while True:`): entry==header==@46, back_edge_block=@1132 `JUMP_BACKWARD(46)`.
Block carrying @178: single instruction `JUMP_BACKWARD -> 130` (orig) / `-> 114` (prod).

## 判据实现 (LANDED — exact file:line + predicate)

ONE file changed: `core/cfg/region_analyzer.py`. Installed **inside `_build_basic_if_region`**
(`def` at `core/cfg/region_analyzer.py:20723`), at the建区 point, i.e. immediately BEFORE the
pristine line `region_type = RegionType.IF_THEN_ELSE if else_blocks else RegionType.IF_THEN`
(pristine `:21219` -> delivered `:21293`). Patch body = **delivered lines 21219-21292**
(74 lines, one hunk `@@ -21218,0 +21219,74 @@`, 0 lines removed).

Predicate (all conditions on the region's OWN blocks + their own last instructions;
no `.successors`, no `get_block_by_offset`, no sibling/parent read, no names/constants,
no ordering dependence):

```
C   = block (region entry / 条件块),  B = then_blocks[0],  E = merge
(not else_blocks) and len(then_blocks) == 1 and C is not None
and all_condition_blocks == {C}                      # 条件单块，无 boolop/链式比较延伸
and C.last.opname in ('POP_JUMP_FORWARD_IF_FALSE','POP_JUMP_IF_FALSE')
and isinstance(C.last.argval, int) and C.last.argval == E.start_offset   # 假分支一次性出环 = 循环出口
and B.last.opname in ('JUMP_BACKWARD','JUMP_BACKWARD_NO_INTERRUPT','JUMP_ABSOLUTE')
and isinstance(B.last.argval, int) and B.last.argval == C.start_offset   # 真分支回跳到条件自身
and all(i.opname in {NOP,CACHE,RESUME,PUSH_NULL,EXTENDED_ARG} | back for i in B.instructions)
and any(i.opname in back for i in B.instructions)                        # B 体内除回跳外无语句
```
Hit => declare in place (correct-at-identification, no retrospective repair):
`LoopRegion(region_type=WHILE_LOOP, entry=C, header_block=C, condition_block=C,
back_edge_block=B, back_edge_blocks={B}, body_blocks=sorted([C,B]), else/init/break=[],
continue_map={}, metadata={for_iter_*: None, natural_back_edge: B, is_degenerate_while: False, ...})`
and `return` it instead of the `IfRegion(IF_THEN, entry=C, then=[B], merge=E)`.
Block set is IDENTICAL to the refused IfRegion's (`{C,B}`) => 每块唯一归属 unchanged;
WHILE_LOOP -> ast.While is the existing one-type-one-node map; no new region type, no new
AST node type, fallback path untouched so non-matching regions emit byte-identically.

Why this is the right declaration: CPython compiles the EMPTY-BODY while `while cond: pass`
as exactly `C: <cond>; POP_JUMP_FORWARD_IF_FALSE -> E` / `B: JUMP_BACKWARD -> C`. The refused
IfRegion rendered `if cond: continue`, and `continue` lands on the ENCLOSING loop's entry
(@114) instead of on C (@130) — one jump slot, identical instruction stream.

## stage readings (all from the MIRROR `/d/Temp/r26a/wt`, judged with `--source`)

UNPATCHED stage 1 (s1_broker) -> PATCHED (s2/s6_broker, delivered bytes):
| file | brief | unpatched mirror | patched mirror |
|---|---|---|---|
| trade_live_broker.pyc | 119/128 | **119/128** | **120/128** (+1) |
| fly/data/quote | 89/92 | - | 89/92 |
| wizard_quant_api | 57/58 | - | 57/58 |
| real_quote | 44/45 | - | 44/45 |
| klinedata | 63/64 | - | 63/64 |
| handlers | 29/30 | - | 29/30 |
| trade_info_utils | 38/41 | - | 38/41 |
| api_base | 27/28 | - | 27/28 |
| strategy | 26/27 | - | 26/27 |
| realtime_event_source | 12/13 | - | 12/13 |
| risk_calculation/__init__ | 42/43 | - | 42/43 |
| quotation (sentinel) | 153/153 | - | 153/153 |
| matcher (sentinel) | 17/17 | - | 17/17 |
| order_api (sentinel) | 37/37 | - | 37/37 |
extra campaign-panel files (all green, unchanged): bar 85/85, strategy_universe 11/11,
load_daily 27/27, plugin_system_log/__init__ 10/10, plugin_system_trade/function 71/71.

Victim unit shape, `unit_diff.py --all` (REPO rig vs MIRROR products):
```
pristine product : len orig=182 prod=182 delta=0  hunks=0 landings=1 judge_diff=True
                   ~ orig[30] @178 JUMP_BACKWARD ->idx22 | prod[30] @178 JUMP_BACKWARD ->idx19
delivered product: len orig=182 prod=182 delta=0  hunks=0 landings=0 judge_diff=False   (= Equal)
```
Product diff is exactly one line: `if len(self.open_orders) == 0:` -> `while len(self.open_orders) == 0:`
(the sealed generator renders the back-edge block as `continue` inside the new While; recompiles to
@130 test + @178 `JUMP_BACKWARD -> 130`, i.e. the original jump slot).

Batteries, run inside the mirror at the recorded relative depth, with the DELIVERED bytes:
repro **9R/9** · arm **0G/3R** · ccneg **3G/1R** · retbreak **2G/2R DRIFT_VS_BASELINE=0** ·
orderapi **5G/0R** · tail **13G/0R** — all six at recorded values.

Fire census (`D:/Temp/r26a/out/census_r26a.py`, wrapper on the PRISTINE analyzer that only
READS the args and calls the original unchanged, in-process whole-file pipeline, 14 panel
files): `FIRES=1 offsets=[130]` on trade_live_broker, 0 on all 13 others => **TOTAL_FIRES = 1**.

Collateral proof (stronger than counts): pristine-tree products vs delivered-byte products,
`cmp` byte-for-byte over the 18 non-victim files = **18/18 BYTE-IDENTICAL**.

## 负面证据 (what is FALSE in the ticket as briefed)

1. The named axis is FALSIFIED: `WHILE_LOOP entry=114 != header_block=130` is **not** a wrong
   declaration. It is this analyzer's standard convention for a top-test while loop — the
   sibling loop[1] (`while not self.before_trading_start: time.sleep(60)`) has the SAME
   mismatch (entry=@46, header=@60) and decompiles CORRECTLY at 119/128; loop[0]'s
   `header_block=130` is exactly the natural-loop header, i.e. the target of its own
   back edge `@1130 POP_JUMP_BACKWARD_IF_TRUE -> 130`, and `entry=114` is the condition
   block whose *fall-through* is the header (same relation as 46->60). Forcing
   `header_block := entry` there would have re-declared a correct region.
2. Real shape (verified by instruction-level alignment, `idxcmp.py`): the original source is
   `while self.before_trading_start:` (@114 test, false->@1132) whose FIRST body statement is
   the EMPTY-BODY loop `while len(self.open_orders) == 0: <空体>` (@130 test, false->@180,
   true->@178 `JUMP_BACKWARD -> 130`). The lost loop is one level BELOW loop[0]; it was
   claimed as `IF_THEN entry=130 exit=180 then=[@178]` (@178 is a bare back edge, so the
   `_then_back_edge_blocks` filter at `:20619-20627` kept it because `B == then_succ`).
3. Census confirms the ticket's own premise that this is NOT the merge-declaration axis:
   the refused region has `merge=@180` (not None), and the three IfRegions are
   IF_ELIF_CHAIN@446(exit 1132), IF_THEN_ELSE@402(exit 1132), IF_THEN@130(exit 180) —
   none merge-less.
4. Generator-side landing fixes remain unexecutable and were NOT attempted: no jump operand
   is edited anywhere; the change is region TYPE -> AST node type.
5. Zero-flip risk that had to be measured away: `LoopRegion` returned from an IfRegion builder
   could have broken IfRegion-typed post-passes (`_ifregion_by_entry`, `.then_blocks` readers).
   It did not: `_ifregion_by_entry` registration and the trailing-`return None` marking sit
   AFTER my early return, so a LoopRegion is never entered into that map; measured products of
   the other 13+5 files are byte-identical.
6. Probes: `probe_loops.py` and `census_r26a.py` run in separate processes that never write a
   judged product, and read only `block.instructions` / `get_last_instruction()` /
   `start_offset` / `region.*` after `analyze()` returned; no `block.successors` and no
   `get_block_by_offset` were read inside the analyzer. Every judged reading above came from
   `pycdc.py --region` runs of the mirror tree, verified by `cmp` against the pristine-tree
   products for the non-target files.

## final declaration

**LANDED-READY.**

* Delivered file: `D:/Temp/r26a/DELIVER/region_analyzer.py` = the WHOLE changed file
  (32811 lines vs pristine 32737; CRLF preserved: 32810 CRLF, 0 lone LF).
* **sha256 first-16 = `35e227ac3e7b25af`** (pristine sealed bytes = `b7f3076323813787`).
* Changed-line count vs pristine: **74 added, 0 removed, exactly one hunk**
  `@@ -21218,0 +21219,74 @@` inside `_build_basic_if_region` (def at `:20723`).
* `py_compile` proof: `python -X utf8 -m py_compile D:/Temp/r26a/DELIVER/region_analyzer.py`
  -> rc=0 (`PY_COMPILE_OK`), plus `py_compile.compile(..., doraise=True)` inside the patcher.
* Criterion: the named unit `<module>.TradeLiveBroker._process_tick_order` flipped
  `hunks=0 landings=1 judge_diff=True` -> **`hunks=0 landings=0 judge_diff=False`**, and
  `trade_live_broker.pyc` **119/128 -> 120/128**; zero decreases on the other ten panel
  files (byte-identical products), sentinels 153/153 · 17/17 · 37/37, all six batteries at
  recorded values, `TOTAL_FIRES = 1`.
* Scope honesty: one unit flip only; broker still needs 7 distinct mechanisms for 128/128
  (`etf_purchase_redemption` and the `_process_order`/`_process_cancel_order`, `handlers._target`,
  `kill_trade_process`, `clock_worker` axes are NOT touched by this criterion and stay registered).
* Repo state: `git status -- core/` EMPTY, repo `core/cfg/region_analyzer.py` still
  `b7f3076323813787` — I performed no repo writes and no `git` writes; all products are in
  `D:/Temp/r26a/out`; no `gate_round.py` / `gate_chain.py` was ever run by me.
* Revert command (byte-exact, certifier-side):
  `cp -f /d/Temp/r26a/pristine/core/cfg/region_analyzer.py /d/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_analyzer.py`
  then assert `sha256sum` first-16 == `b7f3076323813787`; mirror-side revert is the same `cp`
  onto `/d/Temp/r26a/wt/core/cfg/region_analyzer.py`. Reinstaller:
  `python -X utf8 /d/Temp/r26a/out/patch_r26a.py` (asserts pristine hash + single anchor, idempotent).

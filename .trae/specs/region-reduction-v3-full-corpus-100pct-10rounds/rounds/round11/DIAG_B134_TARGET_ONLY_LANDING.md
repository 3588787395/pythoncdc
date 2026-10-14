# DIAG B134 — TARGET_ONLY landing: `bar._history_bars` + `strategy_universe._on_clear_de_listed`

Status: IN PROGRESS (writing incrementally; scratch `D:/Temp/r134/`).
Scope: diagnosis only. No edits under `core/`, no git writes, no 402-file gate.

## 0. Units under test (from sealed round-10 reports)

- `site-packages/IQEngine/core/bar.pyc :: <module>.BarData._history_bars` — 84/85, `Different control flow`
- `site-packages/IQEngine/core/strategy/strategy_universe.pyc :: <module>.StrategyUniverse._on_clear_de_listed` — 10/11, `Different control flow`

Both registered `TARGET_ONLY` in `rounds/round10/UNITMAP_R10.md` line 21 / 35.

## 1. Hunk lists (measured)

Instrument: `python -X utf8 D:/Temp/r10g7/r10g7_hunk.py --corpus REL UNIT` (full-qualname
pairing, nested code objects normalised to `<co …>`, INSERTED separated from DELETED).
Products read from the sealed round-10 disk bytes
(`site-packages/IQEngine/core/barOK.py` sha256[:16] `0c175045e3b0a186`, mtime Oct 8 11:26;
`site-packages/IQEngine/core/strategy/strategy_universeOK.py` `c6cc05ab5fee6b97`).

Readings re-confirmed on the live tree with the judge (compare-only):
`pyc_verify single bar.pyc` → `status=failure units=84/85`, only
`<module>.BarData._history_bars: Different control flow`;
`pyc_verify single strategy_universe.pyc` → `units=10/11`, only
`<module>.StrategyUniverse._on_clear_de_listed`. ⇒ **both prior readings stand**.

### U1 `bar.pyc :: <module>.BarData._history_bars`

Exactly **one** hunk, same opcode, target only (`real=0 reloc=1 deleted=1 inserted=1`,
len 66/66, net 0):

```
replace orig[27:28]=1 prod[27:28]=1   orig_off@126 prod_off@126
   DELETED(orig only): POP_JUMP_FORWARD_IF_FALSE ->@140
   INSERTED(prod only): POP_JUMP_FORWARD_IF_FALSE ->@304
```

* jump site = the `POP_JUMP_FORWARD_IF_FALSE` closing the test
  `engine.config.strategy.frequency == '1m'` (block tail @126).
* ORIGINAL landing @140 = `LOAD_GLOBAL ExecutionContext / LOAD_ATTR phase / CALL …` —
  i.e. the **next operand test of the same statement**, `ExecutionContext().phase() ==
  ExecutionPhase.BEFORE_TRADING_START`. (Prior brief F2 said "`ExecutionContext().phase`
  statement" — confirmed.)
* EMITTED landing @304 = `LOAD_FAST engine; LOAD_ATTR data_proxy; LOAD_METHOD get_history(…)`
  — the if-region merge / post-if continuation. (Prior brief F2 said it lands inside
  `engine.data_proxy.get_history(...)` — confirmed.)
* Emitted product source (barOK.py:287-290):
  `if engine.config.strategy.frequency == '1m':` / `    if frequency == '1d' or ExecutionContext.phase() == ExecutionPhase.BEFORE_TRADING_START:` / `        dt = …`
  The **only** thing wrong is the first jump's target. Byte sequence identical otherwise, which
  proves the original statement is `if A and B or C:` (short-circuit: A-false ⇒ go test C)
  rendered as `if A: if B or C:` (A-false ⇒ go merge). Full windows in `D:/Temp/r134/land_bar.txt`.

### U2 `strategy_universe.pyc :: <module>.StrategyUniverse._on_clear_de_listed`

Exactly **one** hunk, same class (`real=0 reloc=1 deleted=1 inserted=1`, len 70/70, net 0):

```
replace orig[19:20]=1 prod[19:20]=1   orig_off@112 prod_off@112
   DELETED(orig only): POP_JUMP_FORWARD_IF_FALSE ->@156
   INSERTED(prod only): POP_JUMP_FORWARD_IF_FALSE ->@198
```

* jump site = `POP_JUMP_FORWARD_IF_FALSE` on `LOAD_FAST i` (block tail @112).
* ORIGINAL landing @156 = `LOAD_FAST de_listed; LOAD_METHOD add; LOAD_FAST o; CALL; POP_TOP`
  — the `de_listed.add(o)` statement. (Prior brief F3 confirmed.)
* EMITTED landing @198 = `JUMP_BACKWARD → @44` = the **for-loop back-edge block**
  (= merge of the enclosing if region, and also the target of the *inner* test's
  `POP_JUMP_FORWARD_IF_TRUE @154`). (Prior brief F3 confirmed.)
* Emitted product source (strategy_universeOK.py:76-79):
  `if i:` / `    if not i.delisted_date > self._engine.trading_dt:` / `        de_listed.add(o)`
  The original opcode sequence is instead the one of a single test
  `if not i or not (i.delisted_date > trading_dt): de_listed.add(o)` — A-false edge jumps to the
  SHARED BODY, not to the region merge. Full windows in `D:/Temp/r134/land_su.txt`.

### 1.1 The structural identity shared by both (measured, not inferred)

In both units the original landing block has **two in-edges**: (i) the forward jump from the
failing tail and (ii) the fall-through from the immediately following test block; and in both
units the emitted landing is the if-region **merge** block which is also the target of another
jump in the same statement's test chain. Detailed CFG/role numbers are in §2 (measured on the
real dispatch path, not from a hand-built analyzer).

## 2. Role census (measured on the real dispatch path)

Instrument: `D:/Temp/r134/probe_dispatch.py` — it monkeypatches `RegionASTGenerator.__init__`
(tracks EVERY generator instance, 79 for `bar.pyc` / 10 for `strategy_universe.pyc`, target
generator `gen#38[_history_bars]` / `gen#8[_on_clear_de_listed]`),
`_generate_region`, `_generate_if`, `_process_if_blocks`, `_generate_block_statements` and
`generate()`, then calls the real entry point `pycdc.main()`
(`pycdc.py:87-91` = `build_cfg` → `RegionASTGenerator(cfg, top_level_code=…)` → `.generate()`,
`self.regions = self.region_analyzer.analyze()` at `region_ast_generator.py:770`).
So every region/role below was **alive on the dispatched path**, not from a hand-built `analyze()`.
Logs: `D:/Temp/r134/probe_bar.txt`, `D:/Temp/r134/probe_su.txt`.

Note: the block that carries the failing jump is **not** `@86`/`@110` (those are interior
instructions); it is `blk@34` (bar) and `blk@46` (su).

### U1 `bar :: _history_bars` — CFG edges of the ORIGINAL code object (real `build_cfg`)

| block | tail opcode | tail jump arg | successors (ft, jump) | predecessors | exception succ |
|---|---|---|---|---|---|
| blk@34 (covers @34..@126) | `POP_JUMP_FORWARD_IF_FALSE` | **140** | [128, 140] | [18, 30] | ∅ |
| blk@128 (@128..@138) | `POP_JUMP_FORWARD_IF_TRUE` | 206 | [140, 206] | [34] | ∅ |
| blk@140 (@140..@204) | `POP_JUMP_FORWARD_IF_FALSE` | 304 | [206, 304] | **[34, 128]** | ∅ |
| blk@206 (body `dt = …`) | `STORE_FAST` | – | [304] | [128, 140] | ∅ |
| blk@304 (`get_history` + return) | `RETURN_VALUE` | – | [] | [140, 206] | ∅ |

Regions **dispatched** for this unit (`_generate_region` / `_generate_if` log lines):

* `IfRegion entry=34 cond=34 merge=140 IF_THEN then_blocks=[128,206] else=[] blocks=[34,128,206]`
  → blk@34 = `condition_block` **and** `entry`; blk@128 = `then_blocks`; **blk@140 = `merge_block`
  + `exit` (NOT a member of `blocks`)**; blk@206 = `then_blocks`.
  ⇒ **the analyzer's own merge for the failing jump is `140` — exactly the original landing.**
* `IfRegion entry=128 cond=140 merge=304 IF_THEN then_blocks=[206] blocks=[128,206]`
  → blk@128 = `entry`, blk@140 = `condition_block` (**outside its `blocks`**), blk@304 = `merge_block`+`exit`.
* `BoolOpRegion entry=128 merge=304 op_chain=[(128,'or'),(140,'or')] blocks=[128,140]`
  → blk@128 = `entry` + `op_chain_member`; blk@140 = `op_chain_member`; blk@304 = `merge_block`.
* `Region(BASIC) entry=206`, `Region(BASIC) entry=304`.
* **No region anywhere in the dispatched set claims blk@34 as a BoolOp operand** — the
  `and` half of `(A and B) or C` is not in any `op_chain` (measured over all 12 regions of the unit).

`generated_blocks` write timing for blk@140 (the correct landing) while rendering the **outer**
if (`_generate_if:14515` of `IfRegion(34)`, i.e. `_process_if_blocks:25188` of the outer region):
```
GB.ADD blk@140 | _if_extract_condition_from_instructions:24046 <- _if_generate_normal:20864 <- _generate_if:14515 <- _generate_region:4070 <- _process_if_blocks:25188
GB.ADD blk@140 | _if_generate_normal:21076 <- _generate_if:14515 <- _generate_region:4070 <- _process_if_blocks:25188 <- _if_generate_then_branch:18173
```
⇒ blk@140 is claimed as *inner-region condition material* before the outer region ever gets a
chance to use it as its merge; blk@34's emitted AST is
`If(test=Compare(engine.config.strategy.frequency == '1m'), body=[If(test=BoolOp('or',[B, C]))])`
(full JSON in the log) — the nested `If` swallows the outer `merge=140`.

### U2 `strategy_universe :: _on_clear_de_listed` — CFG edges

| block | tail opcode | tail jump arg | successors | predecessors | exception succ |
|---|---|---|---|---|---|
| blk@44 | `FOR_ITER` | 200 | [46, 200] | [0, 198] | ∅ |
| blk@46 (covers @46..@112) | `POP_JUMP_FORWARD_IF_FALSE` | **156** | [114, 156] | [44] | ∅ |
| blk@114 (@114..@154) | `POP_JUMP_FORWARD_IF_TRUE` | 198 | [156, 198] | [46] | ∅ |
| blk@156 (body `de_listed.add(o)`) | `POP_TOP` | – | [198] | **[46, 114]** | ∅ |
| blk@198 (loop back edge) | `JUMP_BACKWARD` | 44 | [44] | [114, 156] | ∅ |
| blk@200 | `POP_JUMP_FORWARD_IF_FALSE` | 424 | [204, 424] | [44] | ∅ |

Regions **dispatched**:

* `LoopRegion entry=44 FOR_LOOP blocks=[0,44,46,114,156,198]` — blk@44 = `entry`+`header_block`;
  blk@46/114/156/198 are loop members.
* `IfRegion entry=46 cond=46 merge=156 IF_THEN then_blocks=[114] blocks=[46,114]`
  → blk@46 = `condition_block`+`entry`; blk@114 = `then_blocks`; **blk@156 = `merge_block`+`exit`
  (not in `blocks`)** ⇒ again **the analyzer's merge equals the original landing (156)**.
* `IfRegion entry=114 cond=114 merge=None IF_THEN then_blocks=[156] else_blocks=[198] blocks=[114,156]`
  → blk@156 = `then_blocks` (inner region claims it), **blk@198 = `else_blocks`+`exit`**.
* `IfRegion entry=200 cond=200 IF_THEN_ELSE then=[204] else=[424]` (the healthy `if de_listed:`).
* **No BoolOpRegion anywhere in this unit** — the `or` of `not i or not X` was never folded into
  an operand chain; the emitted AST is
  `If(test=Name i, body=[If(test=UnaryOp('not', Compare(i.delisted_date > … )), body=[Expr add(o)])])`.

Claim write timing for the correct landing blk@156 (outer region rendering, `_process_if_blocks:25890`
→ inner `_generate_region`):
```
GB.ADD blk@156 | _generate_block_statements_body:56312 <- _generate_block_statements:51913 <- _process_if_blocks:26298 <- _if_generate_then_branch:18173 <- _if_generate_normal:21234 <- _generate_if:14515
GB.ADD blk@156 | _process_if_blocks:26458 <- ... <- _generate_if:14515 <- _generate_region:4070
GB.ADD blk@156 | _process_if_blocks:25904 <- _if_generate_then_branch:18173 ...
GB.ADD blk@156 | _generate_loop:5371 <- _generate_region:4056 <- generate:1911
```

### 2.1 Shared measured shape (both units)

For both, with X = the block carrying the failing tail (`blk@34` / `blk@46`):
1. X's **jump successor** = X's region's `merge_block` = the ORIGINAL landing;
2. X's **fall-through successor** = X's `then_blocks[0]`, a conditional block whose own
   `merge`/`exit` is a *later* block M′ (304 / 198);
3. `merge_block` ∉ outer `region.blocks`, and is instead claimed by the **inner** region as
   `condition_block` (bar, via `_if_extract_condition_from_instructions:24046`) or as
   `then_blocks` (su, via `_generate_block_statements_body:56312`);
4. no exception edge on any of these blocks;
5. the emitter renders X's region as `if <X test>: <inner statement>` and therefore the
   emitted jump target is the *end of the inner statement* = M′, i.e. the outer region's
   `merge_block` value is never consulted when the tail is attached.

## 2.2 Oracle test (target shape proof, not a fix)

Hand-editing ONLY that statement in the sealed products (`D:/Temp/r134/bar_oracle.py`,
`D:/Temp/r134/su_oracle.py`), judged with `pyc_verify single … --source`:
* `bar.pyc` → **status=success units=85/85 success_rate=100.00%**
* `strategy_universe.pyc` → **status=success units=11/11 success_rate=100.00%**
Target shapes: bar `if A and B or C: body` (single BoolOp test); su
`if not i or not X: body`. ⇒ Each unit is indeed the sole failing unit, and the only thing
that must change is the *shape of that one test* — nothing is missing or extra in the product.

(pending)

## 3. Host emitter/analyzer line

(pending)

## 3. Host line (measured by line-level trace on the real pipeline)

Instrument `D:/Temp/r134/probe_chain2.py` (wraps the analyzer's whole BoolOp-chain family,
filters by `cfg.code.co_name`) established that on the real path the chain detector IS
attempted for the failing head block, and `D:/Temp/r134/probe_guard2.py` (sys.settrace inside
that one method, frames parented to the wrapped call) recorded the exact rejecting branch.
Call path in the analyzer: `RegionAnalyzer.analyze:1494` → `_identify_boolop_regions:26278` →
`_detect_boolop_chain_start:27713` → **`_detect_boolop_conditional_chain`**.

### U1 bar — rejected at `core/cfg/region_analyzer.py:_detect_boolop_conditional_chain:29013-29014`

```
CALL _detect_boolop_chain_start(@34 set()) from _identify_boolop_regions:26278
CALL _detect_boolop_conditional_chain(@34 set()) from _detect_boolop_chain_start:27713  ->  None
...
  :28891  _r54_j=@140 _r54_f=@128          (head jump successor / fall-through successor)
  :28916  _r54_k=@206                      (the other operand's non-target successor)
  :28923  _r54_mixed=False                 (needs _r54_k tail ∈ FORWARD_CONDITIONAL_JUMP_OPS;
                                            @206 tail is STORE_FAST ⇒ False)
  :28975  _sb_has_body=True                (a STORE_FAST before the tail inside blk@34)
  :29009  _existing_dual_br=None           (blk@34 not owned by any BoolOpRegion yet)
  :29013  if _sb_has_body:
  :29014  return None
```
⇒ The chain head `blk@34` carries two unrelated leading statements
(`engine = Engine.instance()`, `dt = engine.calendar_dt`) **inside the same basic block** as the
last operand test, so the `_sb_has_body` gate refuses to start a chain there and the `or`-tail
never gets absorbed. The analyzer then reduces `blk@34` to `IfRegion(34, merge=140, then=[128,206])`
whose merge is right, but which the emitter can only render as a nested `if`.

### U2 su — chain walk stops at `…:29736-29737`, rejected at `…:29942-29943`

```
CALL _detect_boolop_conditional_chain(@46 {…blocks of the loop…}) from _detect_boolop_chain_start:27713  ->  None
  :28891  _r54_j=@156 _r54_f=@114        (head jump successor = BODY, fall-through = next test)
  :28975  _sb_has_body=False             (⇒ the bar gate does NOT fire here)
  :29492  chain=[(46, 'and')]            (operand polarity inferred as `and`, not `or`)
  :29726  ft_succ=@114 ∈ block_to_region → _ft_reg = LoopRegion
  :29729  ft_succ ∈ _ft_reg.body_blocks  → B1b carve-out consulted
  :29736  _b1b_loop_body_run_continuation(@46, tail, @114, has_or_member=False) → False → break
  :29942  if len(chain) < 2:
  :29943  return None
```
⇒ su is stopped by the **loop-ownership carve-out** of the chain walk (the `R2-B9`/`B1b` branch
at `:29711-29737`), not by `_sb_has_body`. The walk never even tried `blk@114` as a second
operand, so no `BoolOpRegion` exists anywhere in the unit (census §2 U2 confirms).
Also note `_detect_boolop_conditional_chain(@114)` → None (the second operand as head), and
`_resolve_boolop_condition_region(@46)` → None.

### 3.1 The identity that both rejections ignore (shared criterion, separate branches)

Measured whitelisted facts, identical in both units, with `H` = head block carrying the failing
tail, `J` = H's jump successor, `F` = H's fall-through successor:

* H's tail is a `POP_JUMP_FORWARD_IF_FALSE` with argval = `J.start_offset` (bar @126→140,
  su @112→156);
* `preds(J) == {H, F}` and `succs(J)` contains the body/next-operand while `succs(F)` contains
  `J` (bar: F=@128 tail `POP_JUMP_FORWARD_IF_TRUE→206`, succs=[140,206];
  su: F=@114 tail `POP_JUMP_FORWARD_IF_TRUE→198`, succs=[156,198]);
* `J` is **not** a member of H's region `blocks` — it is held only as `merge_block` (bar) or as
  the inner region's `then_blocks` (su);
* no exception edge on H, F, J;
* the emitted `IfRegion(H)` merge is exactly `J` — i.e. **the analyzer already names the correct
  landing; nothing else in the pipeline ever consults it when attaching the tail.**

## 4. Same site or separate?

(pending)

## 5. Suppression experiments (does the product move?)

(pending)

## 6. Minimal repro battery

(pending)

## 7. Falsifications of prior measurements

(pending)


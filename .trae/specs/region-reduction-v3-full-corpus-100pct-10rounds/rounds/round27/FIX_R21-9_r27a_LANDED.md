# FIX_R21-9 — engineer r27a — mechanism: arm statements emitted into a later suite

Owner file: `core/cfg/region_ast_generator.py` (repo READ-ONLY for me).
Branch `rr-v3r01-f557fd`, HEAD `705ce10d`.
Mirror: `D:/Temp/r27a/wt` · pristine: `D:/Temp/r27a/pristine` · products: `D:/Temp/r27a/out`

## Sections
1. Mirror build proof
2. Stage 1 baseline (unpatched mirror)
3. Exemplar A / B reproduction
4. 判据实现 (exact file:line + predicate)
5. Stage readings (panel + batteries)
6. 负面证据
7. Final declaration

STATUS: IN PROGRESS

## 1. Mirror build proof

Built `D:/Temp/r27a/wt` from repo `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`
@ HEAD `705ce10d` (branch `rr-v3r01-f557fd`).

```
cp -r pycdc.py core parsers utils bytecode scripts /d/Temp/r27a/wt/
S=.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds
cp --parents -r $S/round14/{repro,repro_arm,repro_ccneg} $S/round18/repro_retbreak \
              $S/round19/{repro_orderapi,repro_tail} /d/Temp/r27a/wt/
```
All six battery dirs verified present at identical relative depth (runners print
`ROOT=D:\Temp\r27a\wt`, i.e. their 7-dirname resolution lands on the mirror root).

sha256 first-16, mirror files (self-certified):

| file | sha16 | expected |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `5043790fbeaca162` | `5043790fbeaca162` MATCH |
| `core/cfg/region_analyzer.py` | `b7f3076323813787` | MATCH (read-only) |
| `core/cfg/comprehension_generator.py` | `7d8acab92ccc7782` | MATCH (read-only) |
| `core/cfg/ast_generator_v2.py` | `beeaf14435e22922` | MATCH (read-only) |

Pristine snapshot copied to `D:/Temp/r27a/pristine/core` (region_ast_generator.py
re-verified `5043790fbeaca162`). `D:/Temp/r25b` and `D:/Temp/r26a` NOT used.
Products: only `D:/Temp/r27a/out/**`. No `*OK.py` in the repo. No `git` writes.

## 2. Stage 1 baseline — UNPATCHED mirror, generated then judged with `--source`

Generator: `python -X utf8 pycdc.py --region <pyc> -o out/base/<name>_prod.py` (cwd = mirror).
Judge: `python -X utf8 scripts/pyc_verify.py single <pyc> --source <that fresh product>`.
Every product freshly written under `D:/Temp/r27a/out/base/` (removed before regen);
no in-place `*OK.py` was read. Tree = unpatched mirror.

| panel file | read | brief | |
|---|---|---|---|
| fly/data/quote.pyc | 89/92 | 89/92 | OK |
| .../trade_live_broker.pyc | 119/128 | 119/128 | OK |
| IQCommon/strategy/wizard_quant_api.pyc | 57/58 | 57/58 | OK |
| .../real_quote.pyc | 44/45 | 44/45 | OK |
| IQCommon/api/klinedata.pyc | 63/64 | 63/64 | OK |
| IQCommon/logger/handlers.pyc | 29/30 | 29/30 | OK |
| IQCommon/util/trade_info_utils.pyc | 38/41 | 38/41 | OK |
| IQData/api/api_base.pyc | 27/28 | 27/28 | OK |
| .../fly_data/strategy/strategy.pyc | 26/27 | 26/27 | OK |
| .../realtime_event_source.pyc | 12/13 | 12/13 | OK |
| .../plugin_system_risk_calculation/__init__.pyc | 42/43 | 42/43 | OK |
| fly/data/quotation.pyc (sentinel) | 153/153 | 153/153 | OK |
| plugin_system_matcher/matcher.pyc (sentinel) | 17/17 | 17/17 | OK |
| plugin_fly_data/fly_api/order_api.pyc (sentinel) | 37/37 | 37/37 | OK |

quote's three red units are exactly `<module>.Quote.check_frequency`,
`<module>.Quote.run_individual_transform`, `<module>.Quote.run_tick_socket`.

Note: the brief's order_api panel path `IQCommon/api/order_api.pyc` does not exist; the
real corpus file is `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` (memory
already flags "the corpus pyc paths my briefs kept getting wrong"). Same for matcher =
`IQEngine/plugins/plugin_system_matcher/matcher.pyc`.

Batteries, unpatched mirror:

| battery | read | recorded | |
|---|---|---|---|
| round14/repro | RED=9 / 9 | 9R/9 | OK |
| round14/repro_arm | GREEN=0 RED=3 / 3 | 0G/3R | OK |
| round14/repro_ccneg | GREEN=3 RED=1 / 4 | 3G/1R | OK |
| round18/repro_retbreak | GREEN=2 RED=2 DRIFT_VS_BASELINE=0 / 4 | 2G/2R DRIFT=0 | OK |
| round19/repro_orderapi | GREEN=5 RED=0 / 5 | 5G/0R | OK |
| round19/repro_tail | GREEN=13 RED=0 / 13 | 13G/0R | OK |

MIRROR CERTIFIED — every value reproduces the brief.

## 3. Both exemplars reproduced on the UNPATCHED mirror tree

`unit_diff.py ... --all` (path given as absolute pyc; `--prod` = fresh `out/base/quote_prod.py`).
Tree for every reading below is stated.

Exemplar A — `<module>.Quote.run_tick_socket`, unpatched mirror:
```
len orig=343 prod=344 delta=1
== delete orig[90..114 @@528..@@682] prod[90..90] del=24 ins=0
== insert  orig[226..226 @@1278..@-] prod[202..227] del=0 ins=25
hunks=2 landings=5 judge_diff=True
```
Matches the brief (delta=1, hunks=2, landings=5; one relocation = del 24 + ins 25).

Exemplar B — `<module>.Quote.check_frequency`, unpatched mirror:
```
len orig=131 prod=132 delta=1
== replace orig[106..108 @@456..@@458] prod[106..107] del=2 ins=1
   - @456 LOAD_CONST None / - @458 RETURN_VALUE   + @456 JUMP_FORWARD
== insert orig[131..131] prod[130..132] del=0 ins=2
   + @562 LOAD_CONST None / + @564 RETURN_VALUE
hunks=2 landings=2 judge_diff=True
```
Matches the brief exactly.

### Decoding (all read-only probes in a separate process; no artifact produced by them)
`dis` + `dis._parse_exception_table` on `check_frequency`: exception table
`(314,360 → handler 460)` so the protected try body is `@314..@358` only; `@360..@458`
sits **between the try body and the first handler**, i.e. it is the `else` clause run.
Empirical CPython-3.11.7 compile test (`out/` inline, two hand-written shapes):
* `else:` clause **containing** `return None` → `... @104 RAISE_VARARGS; @106 LOAD_CONST None;
  @108 RETURN_VALUE; @110 PUSH_EXC_INFO` = **the original's shape**.
* `return None` **after** the whole try/except/else → `... @104 RAISE; @106 JUMP_FORWARD to 184;
  @108 PUSH_EXC_INFO; …; @184 LOAD_CONST None; @186 RETURN_VALUE` = **the product's shape**.
So B's source really did end its `else` arm with `return None`; the product hoists that
terminator out of the arm.

Region dump (`RegionAnalyzer(cfg).analyze()`, the returned LIST), check_frequency:
```
TryExceptRegion entry=314  blocks=[312,314,360,372,424,436,460,478,552,554]
   try_blocks=[314]  else_blocks=[360,372,424,436]  handler_entry_blocks=[460]
   cleanup_blocks=[552,554]  has_else=True has_finally=False
IfRegion entry=304  blocks=[304,312,314,360,372,424,436,456,560]  else_blocks=[560]
Region  entry=456 (bare, parent=IfRegion:304)   ← the arm's own terminator block
blk@456 role=IF_THEN instrs=[LOAD_CONST 456, RETURN_VALUE 458] succ=[] preds=[424]
```
Block **456 is not in the try region's `blocks` at all** — its only predecessor is the
else-arm block 424, and `456 < first handler entry 460`. The orelse suite stops at the
declared `else_blocks`, so 456 is re-emitted by the enclosing `IfRegion:304` suite AFTER
the `Try` node. That is the defect.

Region dump, run_tick_socket:
```
IfRegion entry=24  then_blocks=[68,70,136,684,808,1276,844,1190,1146,1188,1226,1230,1234]
                   else_blocks=[528,680]  merge_block=1512  condition_block=24
```
The relocated range `@528..@682` (the `else` arm, ending in its own
`LOAD_CONST None; RETURN_VALUE` @680/@682) **is** emitted inside its own `else:` arm in
the product text (product lines 34-38). The hunk exists because the ANALYZER declares
block 684 (`stocks = list(message.keys())[0]` … the post-`if` merge code) a **then_block**
with `merge_block=1512`, so the then suite swallows 684 and the whole arm is pushed ~110
instructions later. See §6 — A and B do not share a host.

## 4. 判据实现 (the predicate I landed)

File: `core/cfg/region_ast_generator.py` — **the only file I changed.**
Host method: `RegionASTGenerator._generate_try` (def at `:29798`), inside the
`try/except/else` arm assembly (`if region.else_blocks and region.has_else and not
_try_body_terminates_abnormally:` at `:30827`), immediately after the existing
`[R09 fix]` `_filtered_else.append(_r09_r.entry)` (`:30845`) and before `_parent_is_loop`
(`:30846` pristine). In the PATCHED file the block is `:30846`–`:30896`, predicate head at
**`core/cfg/region_ast_generator.py:30867`**.

```python
if region.else_blocks and region.handler_entry_blocks:
    _r27_arm_hi      = max(b.start_offset for b in region.else_blocks)
    _r27_handler_lo  = min(hb.start_offset for hb in region.handler_entry_blocks)
    _r27_reserved    = ⋃ id(b) for b in region.{try_blocks, handler_entry_blocks,
                                               finally_blocks, cleanup_blocks}
    _r27_arm         = {id(b) for b in region.else_blocks}
    repeat until fixpoint:
        for b in self.cfg.blocks.values():
            accept b  iff  id(b) ∉ _r27_arm ∪ _r27_reserved
                          and  _r27_arm_hi < b.start_offset < _r27_handler_lo
                          and  b.predecessors  non-empty
                          and  all(id(p) in _r27_arm for p in b.predecessors)
    append accepted blocks (ascending offset) to _filtered_else
```
In words — **[R27-9 try/except/else arm-tail ownership]**: CPython lays a
`try/except/else` out as `<try body> <else clause as one contiguous run> <first handler:
PUSH_EXC_INFO>`; therefore any block strictly inside the interval
`(max else_block offset, min handler_entry offset)` whose **every** predecessor already
belongs to the arm can only execute on the no-exception path, so it *is* part of the arm —
including its own terminator. Claim it while the arm is being assembled, so it is emitted
inside `Try.orelse` instead of being re-emitted by the enclosing suite after the `Try`
node.

Fire on the victim: `_r27_arm_hi = 436`, `_r27_handler_lo = 460`, block 456 accepted
(preds = [424] ⊂ else arm). `_filtered_else` becomes `[360,372,424,436,456]`.
Properties: one call site; only EXTENDS the arm list (never drops/reorders an analyzer
declaration), so any region without such a tail block emits byte-identically (measured:
13/13 other panel products byte-identical); reads only offsets + CFG predecessor identity —
no jump operand, no landing target, no cross-level region re-derivation; no repair pass
(it runs at the identification site of the arm).

## 5. Stage readings (PATCHED mirror tree = D:/Temp/r27a/wt, products = out/p1/)

Product-vs-pristine-product `cmp` per target is the inertness proof.

| panel file | baseline | patched | product |
|---|---|---|---|
| **fly/data/quote.pyc** | 89/92 | **90/92** | CHANGED (1 line) |
| trade_live_broker.pyc | 119/128 | 119/128 | BYTE-IDENTICAL |
| wizard_quant_api.pyc | 57/58 | 57/58 | BYTE-IDENTICAL |
| real_quote.pyc | 44/45 | 44/45 | BYTE-IDENTICAL |
| klinedata.pyc | 63/64 | 63/64 | BYTE-IDENTICAL |
| handlers.pyc | 29/30 | 29/30 | BYTE-IDENTICAL |
| trade_info_utils.pyc | 38/41 | 38/41 | BYTE-IDENTICAL |
| api_base.pyc | 27/28 | 27/28 | BYTE-IDENTICAL |
| strategy.pyc | 26/27 | 26/27 | BYTE-IDENTICAL |
| realtime_event_source.pyc | 12/13 | 12/13 | BYTE-IDENTICAL |
| plugin_system_risk_calculation/__init__.pyc | 42/43 | 42/43 | BYTE-IDENTICAL |
| quotation.pyc (sentinel) | 153/153 | 153/153 | BYTE-IDENTICAL |
| matcher.pyc (sentinel) | 17/17 | 17/17 | BYTE-IDENTICAL |
| order_api.pyc (sentinel) | 37/37 | 37/37 | BYTE-IDENTICAL |

Per-unit shape for the flipped unit (`unit_diff … --all`):
`check_frequency` base `len 131/132 delta=1 hunks=2 landings=2 judge_diff=True`
→ patched `len orig=131 prod=131 delta=0 hunks=0 landings=0 judge_diff=False`.
Whole-product textual delta is ONE line: `-            return None` /
`+                return None` (12-space → 16-space, i.e. into the `else:` suite).

Other quote units unaffected (patched vs baseline, identical readings):
`run_tick_socket` `hunks=2 landings=5 judge_diff=True` both;
`run_individual_transform` `hunks=10 landings=3 judge_diff=True` both (delta=-52).

Batteries on the patched mirror — all at recorded values:
repro RED=9/9 · arm GREEN=0 RED=3/3 · ccneg GREEN=3 RED=1/4 ·
retbreak GREEN=2 RED=2 DRIFT_VS_BASELINE=0/4 · orderapi GREEN=5 RED=0/5 ·
tail GREEN=13 RED=0/13.

Third check (never booked): broker `_process_tick_order` — broker's patched product is
BYTE-IDENTICAL to the pristine product, so the predicate does not move it (119/128).

## 6. 负面证据

1. **A and B do NOT share a host** (refuted, three independent proofs).
   * Structure: B's misplaced block (456) is not declared in the owner region's
     `else_blocks`; A's relocated block (528/680) **is** declared and **is** emitted
     inside its own `else:` suite in the product text — A's product line 34-38 already
     read `else: warning / acquire / updateflag=-1 / release / return None`.
   * Cause: A's displacement comes from the *then* arm of `IfRegion entry=24`
     absorbing `684`, which the analyzer declares `then_blocks=[…684…]` with
     `merge_block=1512`; the fix would have to contradict an analyzer declaration about
     a block owned elsewhere, i.e. the ruled-out merge/arm-ownership route.
   * Mechanically: my predicate is guarded by
     `region.else_blocks and region.handler_entry_blocks` — an `IfRegion` has no
     `handler_entry_blocks`, so it cannot fire for A. Measured: A's `unit_diff` reading
     is unchanged (`hunks=2 landings=5`) and its hunk is byte-for-byte the same range
     (`delete orig[90..114 @@528..@682]` / `insert prod[202..227]`) before and after.
   ⇒ **A is a separate ticket** (single mechanism: "post-conditional merge code absorbed
   into the then arm when the else arm terminates in a return", host
   `_if_generate_then_branch :17780` / `_merge_block_is_then_exclusive :20275`, victim
   `IfRegion entry=24` of `run_tick_socket`). I did not write a second predicate.
2. The predicate is inert on 13 of 14 panel products (`cmp` byte-identical), so the
   landed flip is not carried by collateral re-nesting; the quote product differs by
   exactly one source line.
3. `run_individual_transform` (delta=-52, hunks=10) untouched by this predicate — a
   third, unrelated mechanism inside the same file.
4. Ruled out before coding (per brief, not re-opened): jump-landing edits in the
   generator (AST has no jump operands). B is NOT a landing case — the `landings=2` rows
   at baseline were pure shift shadows; after the fix `landings=0`, i.e. the flip came
   from nesting/order only, which is what makes it expressible.
5. Bare `Region entry=560` (the implicit tail) stays in `IfRegion:304`'s `else_blocks`;
   the fix does not touch it — the function tail remains `LOAD_CONST None;
   RETURN_VALUE` @560/@562 as in the original.

## 7. Final declaration

**LANDED-READY.**

* Deliverable: `D:/Temp/r27a/DELIVER/region_ast_generator.py` (WHOLE changed file).
* Delivered sha256 first-16: **`c16daa4f87dc68e6`** (3 752 989 bytes)
  — pristine sealed bytes = `5043790fbeaca162` (3 749 415 bytes).
* Changed lines vs pristine: **51 added, 0 deleted, 0 modified** (59 642 → 59 693 lines);
  single insertion at `:30846–:30896` inside `_generate_try`.
* `py_compile` proof: `python -X utf8 -m py_compile core/cfg/region_ast_generator.py`
  → OK in the mirror, and `py_compile` of the DELIVER file itself → `DELIVER_PY_COMPILE_OK`.
* Result: named-unit flip **`check_frequency` RED→Equal**, `fly/data/quote.pyc`
  **89/92 → 90/92**; zero decreases across the other 13 panel files; sentinels
  153/153 · 17/17 · 37/37; all six batteries at recorded values.
* Repo untouched: `core/cfg/region_ast_generator.py` in
  `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` still hashes `5043790fbeaca162`;
  no `*OK.py` written, no `git` write, `gate_round.py`/`gate_chain.py` never executed.
* Revert command (restore sealed bytes in any install target):
  `cp /d/Temp/r27a/pristine/core/cfg/region_ast_generator.py <root>/core/cfg/region_ast_generator.py`
  — or, in a checkout of `rr-v3r01-f557fd` @ `705ce10d`,
  `git checkout -- core/cfg/region_ast_generator.py`.



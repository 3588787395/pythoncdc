# Round 67 · diag6 · FACTS (read-only diagnose agent)

Workspace `D:/Temp/opencode/r67gate/diag6`. Repo untouched (only read).
Targets: `IQCommon/strategy/wizard_quant_api.pyc`,
`IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`, `fly/logger.pyc`.
Python 3.11.7 (matches the pyc target runtime).

## Step 0 - baseline replay (`--arm=landed`) : ALL THREE REPLAY IDENTICAL TO BRIEF

targets (`dump/landed.jsonl`, 6.6 s):
```
landed wizard_quant_api.pyc   51/53  [['calculate_di',75,73,0,45], ['params_analysis',133,126,1,117]]
landed __init__.pyc           33/35  [['_on_publish_after_trading_end',486,481,3,33], ['_save_testds_to_csv',71,68,7,19]]
landed logger.pyc             29/30  [['write_logging_thread',113,113,1,40]]
```
canary (`dump/canary_landed.jsonl`, 11.6 s) - sha per-file identical to BRIEF:
```
fly/data/quotation.pyc        143/143 sha=4d41187e356544e0
fly/common/market_time.pyc     10/10  sha=af77224b34b203c4
IQCommon/util/datetime_func.pyc 26/26 sha=e711b8ea86d49a15
IQData/utils/datetime_func.pyc  25/25 sha=9d09af09249da177
```
battery (`dump/battery_landed.jsonl`, 3.0 s): **115/127 matched, 12 defect functions**, per-file
readings byte-identical to the BRIEF table (incl. `probe_r63b2_cases 7/9`, `r65_trytail 8/9`,
`fs2 6/10`, `r66d3_pred 2/3`, `r63b5_w1 1/2`, `r64d5_contsink 1/2`, `d2/d8 7/9`).

strict ruler `python -X utf8 cstrict.py build_landed targets.txt dump/landed_strict.json` (0.8 s):
```
wizard_quant_api  strict 52/56 missing=0 extra=0
   .filter_desicion [seq_len] 179/181 ; .get_DMI.calculate_di [seq_len] 81/79
   .init_stock_pool_filter [target_diff] #33 JUMP 终点 orig=('security_pool_info','LOAD_FAST') decomp=('final_stocks','LOAD_FAST')
   .params_analysis [seq_len] 134/128
risk_calculation  strict 34/37 missing=0 extra=0
   ._on_publish_after_trading_end [seq_len] 488/481 ; ._on_set_positions [seq_len] 297/298 ; ._save_testds_to_csv [seq_len] 75/68
fly/logger        strict 62/64 missing=0 extra=0
   .Backtest.write_logging_thread [seq_diff] #71 orig=('msgs','LOAD_FAST') decomp=('<JUMP>','JUMP')
   .SafeFileHandler.check_baseFilename [target_diff] #14 POP_JUMP_IF_TRUE 终点 orig=('1','LOAD_CONST') decomp=('0','LOAD_CONST')
```
=> brief pre-reads CONFIRMED, no correction needed at step 0.

## Step 1 - per-code-object hunk tables (`logs/nested_diff.py`, new tool) + attribution

`nested_diff.py <pyc> <okpy>` walks BOTH code-object trees by full path
(`<parent>/<name>#<const-index>`) and diffs CACHE-filtered, jump-normalized instruction lists.
Outputs saved: `logs/nd_wizard.txt`, `logs/nd_risk.txt`, `logs/nd_fly_logger.txt`.

### ADJUDICATION of count artifacts (must read before using the tables)
`nested_diff` reports **10 differing code objects for wizard, 3 for risk, 1 for logger**, but the
official ruler only fails 2/2/1 and strict only 4/3/2. The surplus is *my* tool, not the corpus:
`<root>` (4x `NOP` delete), `ST_stock_filter#34` / `HALT_stock_filter#35` (1x `NOP`),
`read_config_file#51` (2x `NOP`), `init_stock_pool_filter#33` (`NOP` delete + `EXTENDED_ARG` insert)
are **CPython pseudo-instruction artifacts** - both rulers strip `NOP`/`EXTENDED_ARG`, and all of
these functions are *matched* on both rulers (only `init_stock_pool_filter` is flagged, and there
for a JUMP *target index*, i.e. a position shift, not a lost name). Consequence: only the rows
below that coincide with a ruler failure are real defects. `nhunks.py` cannot see pure-deletion
context at all (`if hi <= lo: continue`), which is why the real `calculate_di` defect was invisible
there; `nested_diff.py` supersedes it.

### wizard_quant_api (58 code objects) - REAL defects after artifact suppression

| code object | orig/decomp | hunks | rulers |
|---|---|---|---|
| `/filter_desicion#10` | 195/197 | `insert decomp=[LOAD_CONST None, RETURN_VALUE]` (tail) | OFFICIAL PASS, strict seq_len 179/181 |
| `/params_analysis#11` | 144/137 | 3 (see below) | BOTH FAIL |
| `/get_DMI#31/calculate_di#1` | 90/88 | `delete LOAD_CLOSURE low` @38, `delete LOAD_CLOSURE high` @56 | BOTH FAIL |
| `…/calculate_di#1/<genexpr>#3` | 64/40 | `delete orig[32:56]` (24 instr.) | (shadow of the above) |
| `…/calculate_di#1/<genexpr>#4` | 64/40 | `delete orig[32:56]` (24 instr.) | (shadow of the above) |
| `/init_stock_pool_filter#33` | 175/175 | NOP + EXTENDED_ARG only | OFFICIAL PASS, strict target_diff (index shift) |

### risk_calculation (43 code objects)

| code object | orig/decomp | hunks | rulers |
|---|---|---|---|
| `…#18/_on_set_positions#9` | 336/337 | `replace orig[256:258]=[EXTENDED_ARG, JUMP_BACKWARD] -> [JUMP_FORWARD]`, `insert decomp[301:303]=[EXTENDED_ARG, JUMP_BACKWARD]` | OFFICIAL PASS, strict 297/298 |
| `…#18/_on_publish_after_trading_end#10` | 531/523 | `delete NOP`, `replace orig[491:499]=[JUMP_FORWARD, LOAD_GLOBAL NULL+time, LOAD_ATTR sleep, LOAD_CONST 0.01, PRECALL, CALL…] -> [NOP]` | BOTH FAIL |
| `…#18/_save_testds_to_csv#28` | 81/75 | 7 (below) | BOTH FAIL |

### fly/logger (64 code objects)

| code object | orig/decomp | hunks | rulers |
|---|---|---|---|
| `/Backtest#12/write_logging_thread#4` | 127/128 | `delete orig[78:87]` == `insert decomp[117:126]` (same 9-instr group), `replace orig[122]=[JUMP_FORWARD] -> [EXTENDED_ARG, JUMP_BACKWARD]` | BOTH FAIL (official 113/113 hunk=1) |
| `/SafeFileHandler…/check_baseFilename` | 34/34 | 0 substantive | OFFICIAL PASS, strict target_diff (REAL, see Step 5) |

## Step 1 (cont.) - wizard_quant_api :: get_DMI.calculate_di   (OFF 75/73, STRICT 81/79) - BOTH RULERS

* ORIG `calculate_di` co_consts: `<genexpr>` freevars `('high_now','low_now','pre_close')`,
  `('high','low')`, `('high','low')`.
* PRODUCT `calculate_di` co_consts: same first, then `('high',)` and `('low',)` - one cell SHORT,
  which is exactly the two `LOAD_CLOSURE` deletions the rulers see.

Orig `<genexpr>#3` (the `dmp = sum(...)` element) is
`A if (A > 0 and B > 0) else 0` with `A = high[-i] - high[-(i+1)]`, `B = low[-(i+1)] - low[-i]`:
offsets 52 `BINARY_OP -`, 58 `COMPARE_OP >`, **64 `POP_JUMP_FORWARD_IF_FALSE to 202`**, 104/146
`BINARY_OP -`, 150 `COMPARE_OP >`, **156 `POP_JUMP_FORWARD_IF_FALSE to 202` - a SECOND conditional
jump with the SAME target**, 158..196 recomputes A, 200 `JUMP_FORWARD to 204`, 202 `LOAD_CONST 0`,
204 `YIELD_VALUE`. `<genexpr>#4` is the mirror (`dmm`, the lost operand is A).
The landed product emits `A if A > 0 else 0` (`build_landed/…wizard_quant_apiOK.py` L262) - the
**second `and` conjunct of the ternary test is dropped**.

### ROOT CAUSE, MEASURED IN THE GENERATOR (`logs/attrib_comp.py` -> `logs/attrib_comp.out`)
```
##### wizard_quant_api.pyc
  _detect_comp_ternary: cond_jump@20(POP_JUMP_FORWARD_IF_FALSE->202) cond_instrs=[7:20] n_in_cond=13
                        EXTRA same-target cond jumps after it (i.e. boolop operands LOST) = 1 -> IfExp
  _detect_comp_ternary: cond_jump@20(POP_JUMP_FORWARD_IF_FALSE->202) cond_instrs=[7:20] n_in_cond=13
                        EXTRA same-target cond jumps after it (i.e. boolop operands LOST) = 1 -> IfExp
##### r67d6_boolop_ternary.pyc   (9-line synth, see Step 3)
  _detect_comp_ternary: cond_jump@20(POP_JUMP_FORWARD_IF_FALSE->162) cond_instrs=[7:20] n_in_cond=13
                        EXTRA same-target cond jumps after it (i.e. boolop operands LOST) = 1 -> IfExp
```
`core/cfg/comprehension_generator.py::_detect_comp_ternary` (def L1601) scans
`for idx in range(store_idx+1, append_idx)` (L1619-1651) and **`break`s at the FIRST conditional
jump**, then slices `cond_instrs = all_instrs[last_filter_end+1 : cond_jump_idx]` (L1664). The
`and`-continuation - the 24-instruction group ending in the second same-target
`POP_JUMP_FORWARD_IF_FALSE` - is therefore *never* part of the condition, and the emitted `IfExp`
carries only the first conjunct. The reading above (instrumented copy of the same loop, repo file
untouched) proves the loss is at that `break`, on both the corpus instance and the synthetic.

**=> candidate is UNLANDABLE THIS ROUND**: `h62.py` L49 asserts
`rel in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py')`; a fix for this defect
lives in a third file (`comprehension_generator.py`). Fixing it would move official 51->52 AND
strict 52->53 for one function on BOTH rulers.

## Step 2 - wizard_quant_api :: params_analysis  (OFF 133/126 hunk=1, STRICT 134/128) - BOTH RULERS

`nested_diff`: 144/137, 3 hunks, all in the outer function:
```
replace orig[10:11]=[JUMP_FORWARD J]                -> decomp[10:12]=[LOAD_CONST None, RETURN_VALUE]
replace orig[16:17]=[JUMP_FORWARD J]                -> decomp[17:19]=[LOAD_CONST None, RETURN_VALUE]
delete  orig[20:29]=[LOAD_FAST filter_type, LOAD_FAST value, LOAD_GLOBAL NULL+float,
                     LOAD_FAST value_params, PRECALL, CALL, ...]
```
Original head: `8 POP_JUMP_FORWARD_IF_FALSE to 86`, `28 JUMP_FORWARD to 48`, `30 PUSH_EXC_INFO`,
`40 JUMP_FORWARD to 48`, `48 LOAD_FAST filter_type … 84 RETURN_VALUE`. So the two `JUMP_FORWARD`s
are the *try-exit / handler-exit* edges to the join at 48; the landed text renders each of them as
an explicit `return None` inside the `except:` arm:
```
if filter_type in ('up_v', 'down_v'):
    try:
        value = value[-1]
    except:
        value = value
elif filter_type == 'region_v':
    ...
```
and consequently drops the `float(value_params)` / `BUILD_CONST_KEY_MAP` group (indices 20-28).
This is exactly the **on-record try-body JUMP_FORWARD family** (emission order at the try tail).
The brief's caution applies verbatim and is confirmed: the fix must not rewrite a try-tail `Expr`
into a value-carrying `Return`. No same-level predicate in the two landable files covers a
"JUMP_FORWARD whose target is try-exit ∪ handler-exit joins at 48" without a
cross-region containment test (forbidden as rule input). **候选：NONE.**

## Step 2 (cont.) - wizard_quant_api strict-only residues (official already PASS)

* `filter_desicion` 179/181: one extra tail `LOAD_CONST None / RETURN_VALUE` - the product's
  function ends with an explicit unreachable-epilogue shape. Same family as the try-tail above.
* `init_stock_pool_filter` `target_diff #33`: the JUMP's *target index* lands on
  `LOAD_FAST 'security_pool_info'` in orig vs `LOAD_FAST 'final_stocks'` in decomp with identical
  instruction count - i.e. a loop-rotation/jump-target ordering artifact, not a lost name. Needs a
  jump-target-aware pairing (strict gives it), not a new reduction rule.

## Step 1/2 - risk_calculation :: _save_testds_to_csv (OFF 71/68, 7 hunks; STRICT 75/68)

```
insert   decomp[16]=[NOP]
replace  orig[37]=[JUMP_BACKWARD]              -> decomp[38]=[JUMP_FORWARD]
delete   orig[58]=[LOAD_CONST 0]
delete   orig[60:62]=[IMPORT_NAME …function, IMPORT_FROM THREAD_STATUS]
delete   orig[63]=[POP_TOP]
replace  orig[66:68]=[LOAD_CONST None, RETURN_VALUE] -> decomp[63]=[JUMP_FORWARD]
delete   orig[79:81]=[LOAD_CONST None, RETURN_VALUE]
```
Landed text (`build_landed/IQEngine__…OK.py`): the function's tail is rendered as a **duplicated
spurious loop** -
```
while not self._stop_save_csv_thread:
    THREAD_STATUS = ('THREAD_STATUS',)     # <- the IMPORT_FROM materialised as a tuple assignment
    if THREAD_STATUS:
        break
    time.sleep(0.01)
break
```
i.e. `IMPORT_FROM THREAD_STATUS` (a *name load*, `POP_TOP`-discarded in orig) is re-emitted as a
`STORE_NAME` + `if`, and the enclosing `while` loses its back edge (`JUMP_BACKWARD` -> `JUMP_FORWARD`)
so the second loop is *added* instead of being the same block. Two independent reductions are
entangled here (import-as-value, rotated-while) plus the `LOAD_CONST None/RETURN_VALUE` <->
`JUMP_FORWARD` try/loop-exit swap: **the same three signatures as `_on_publish_after_trading_end`**,
i.e. the on-record family. Not one predicate; not landable in the remaining budget. **候选：NONE.**

## Step 2 - risk_calculation :: _on_publish_after_trading_end (OFF 486/481, STRICT 488/481)

Only 2 real hunks (1 is a `NOP`): the spin-loop group `JUMP_FORWARD + time.sleep(0.01) + CALL`
(8 instructions) collapses to a single `NOP` -> the sleep call and its exit edge are lost, exactly
as in `_save_testds_to_csv`. The landed `[R66-diag4 D1 augsub-continue-role]` rule (L44564 of
`region_ast_generator.py`) already landed one reduction of this family; any further predicate here
must be at a **different level** per the brief - see Step 5 for why I could not produce one that
does not regress.

## Step 2 - risk_calculation :: _on_set_positions (strict-only 297/298, OFFICIAL PASS)

2 hunks: `orig[256:258]=[EXTENDED_ARG, JUMP_BACKWARD] -> [JUMP_FORWARD]` and a later
`insert [EXTENDED_ARG, JUMP_BACKWARD]`. Same rotated-while/back-edge re-placement as
`write_logging_thread`: the loop's terminal backward edge is emitted at a different index. No
instruction is lost (only +1 from an `EXTENDED_ARG` width change). Strict-visible, official-invisible;
a value-0-for-official target.

## Step 3 - synth repros (all in `synth/`, each with its own list file; produced with `python -X utf8`)

1. `synth/r67d6_boolop_ternary.py` (v1-v4) + `.pyc` + `synth/r67d6_boolop_ternary.txt`
   - minimal `A if (A > 0 and B > 0) else 0` inside a generator, mirroring `calculate_di`.
   - landed: `dump/synth_landed.jsonl` = `4/6 [['<genexpr>',51,39,2,27], ['v1',17,16,0,14]]`.
   - v2/v3/v4 (the same shape with the conjuncts re-ordered / `or` / nested) PASS landed -> the
     defect is specific to a **second forward conditional jump that shares the first jump's target**.
2. `synth/r67d6_boolop_ternary2.py` (v5-v9) + `.pyc` + `.txt` - list-comp / nested-genexpr variants:
   landed `dump/synth2_landed.jsonl` = `3/8`; only v5 (plain generator `yield`) passes and
   `nested_diff` proves v6 (listcomp), v7/v8/v9 (genexpr) all lose the second `and` operand.
3. `synth/r67d6_whiletrue_headif.py` (14 lines) + `.pyc` + `.txt`
   - reproduces the `write_logging_thread` CFG shape: a `while True:` whose header block carries
     `q = write_queue.qsize(); if q:` (store-then-conditional-jump, then-branch and fall-through
     both inside the loop, loop continues afterwards).
   - landed: `dump/synth3_landed.jsonl` = `1/2 [['w1', 39, 39, 1, 13]]` - **same signature as the
     corpus function** (equal length, hunk=1, one moved group). The product hoists
     `if msgs: printer(msgs)` out of the `if q:` then-branch.

## Step 4/5 - the candidate I built, and its measured A/B (REJECTED)

`specs/cand_r67_whiletrue_headif.json`, arm `r67d6w1`, built with
`python -X utf8 h62.py build --spec=… --dst=build_r67d6w1` (single edit to
`core/cfg/region_analyzer.py`, anchor `count==1`, inside `_should_skip_block_for_if_region`
def L15408, at the header-block whitelist's `if not is_if_break_else_continue: return True`
L15460-61). Predicate (three-part 识别条件/归约方式/AST 映射 comment
`[R67-diag6 W1 while-True-header-mixed-if]`): same-level fields only - last instruction of the
header block is in `FORWARD_CONDITIONAL_JUMP_OPS`, BOTH successors are in `block_region.blocks`,
and the block contains a `STORE_*` before that jump.

Diagnosis that motivated it (measurement): `logs/reg_wlt.txt` shows `IfRegion@368` **is** created
(blocks `[368,372]`, child of `LoopRegion@4`), but `logs/trace_wlt.txt` shows the emission order
inside the loop body is `IfRegion@426` (trace L61) ... then `IfRegion@368` **last** (trace L107),
immediately after a `_build_effective_stmts -> list[0]`. So the scheduler demotes block 368's
`if` to plain block statements and re-emits its region at the tail -> the `delete orig[78:87] /
insert decomp[117:126]` pair the rulers see. Root: `_should_skip_block_for_if_region` returns True
for a while-True header that mixes store + conditional jump.

Measured A/B (`h62.py ab`, dumps `dump/cand.jsonl`, `dump/battery_cand.jsonl`,
`dump/canary_cand.jsonl`, `dump/synth3_cand.jsonl`, `dump/cand_strict.json`):
```
targets  SAME=2 MOVED=1   fly/logger 29/30 sha 64852de5112c7b4f -> 0db7e214af37e736
                          write_logging_thread [113,113,1,40] -> [113,41,1,107]   <-- REGRESSION
battery  SAME=30 MOVED=1  r63b5_w1.pyc sha 249a9f0d3be3b8c4 -> 369bcf493c4ac832
                          init_connection [42,41,0,25] -> [42,32,0,32]           <-- REGRESSION
canary   SAME=4           all four shas unchanged
strict   wizard 52/56, risk 34/37, logger 62/64 (counts unchanged; logger's bad entry changes
         character: seq_diff #71 -> seq_len orig=113 decomp=41)
synth3   w1 [39,39,1,13] -> [39,39,2,6]  (moves toward the target but still unmatched)
```
=> The skip-suppression does re-schedule `IfRegion@368` early, but the loop body then *re-emits*
the header block's prefix statements and stops nesting the `orelse`, so the product loses 72
instructions in the corpus and 9 in `r63b5_w1::init_connection`. **Landable only together with a
coordinated `region_ast_generator.py` change (statement-dedup of the re-emitted header prefix),
which is a second spec, not this one.** REJECTED; not submitted as an earned candidate. Spec kept
at `specs/cand_r67_whiletrue_headif.json` with this measurement so the next round does not re-try
the single-sided version.

## Step 5 - NEW lead found while completing the record: fly/logger :: check_baseFilename

`logs/nh_logger_check_baseFilename.txt`: 0 substantive hunks (34/34) -> official ruler PASS.
Strict: `target_diff #14 POP_JUMP_IF_TRUE 终点 orig=('1','LOAD_CONST') decomp=('0','LOAD_CONST')`.
Original disassembly (verified in-process):
```
102 COMPARE_OP !=            (X = self.suffix_time != time.strftime(...))
108 POP_JUMP_FORWARD_IF_TRUE to 204     -> X true  ==> LOAD_CONST 1 ; RETURN_VALUE
110 LOAD_GLOBAL os ... 188 PRECALL 192 CALL (Y = os.path.exists(baseFilename + '.' + suffix_time))
202 POP_JUMP_FORWARD_IF_TRUE to 208     -> Y true  ==> LOAD_CONST 0
204 LOAD_CONST 1 / 206 RETURN_VALUE
208 LOAD_CONST 0 / 210 RETURN_VALUE
```
=> original semantics `return 1 if (X or not Y) else 0`. Landed product:
`if not (X or Y): return 1 else: return 0` - semantics `return 1 if (not X and not Y)`.
The `not` belongs to operand **Y only** in the bytecode, but the product pushed it across the whole
`BoolOp`. This is a **genuine semantic inversion that the official ruler cannot see** (same
instruction count, only a jump target differs) - worth raising with the centre as a ruler-coverage
issue, independent of any round-67 scoreline. A landable predicate would have to live where an
`or`-chain in *statement-condition* context is folded against its jump target
(`region_ast_generator.py` `_generate_if`/`_build_ternary_boolop_condition` L33937 path), and would
need its own polarity-preserving rule; I did not have the budget to build + 4-run A/B a second
candidate this round, and a guess-and-ship version is exactly what the brief forbids.

## VERDICTS

| target | verdict |
|---|---|
| `wizard_quant_api::get_DMI.calculate_di` (fails BOTH rulers) | ROOT CAUSE PROVEN (`comprehension_generator._detect_comp_ternary` first-jump `break`, 24-instr operand lost, measured) but file is outside the two landable files (`h62.py` L49 assert) => **候选：NONE (unlandable this round)**; spec-level follow-up should be a `comprehension_generator` rule, 1 function, +1 official AND +1 strict |
| `wizard_quant_api::params_analysis` (fails BOTH) | on-record try-body JUMP_FORWARD family, 3 entangled hunks incl. a lost `float(...)` group => **候选：NONE** |
| `risk_calculation::_save_testds_to_csv` / `::_on_publish_after_trading_end` (fail BOTH) | same try/loop-exit family + `IMPORT_FROM`-as-value duplication => **候选：NONE** |
| `fly/logger::write_logging_thread` (fails BOTH) | emission-order, reproduced in 14 lines; built predicate measured to REGRESS it (113->41) and `r63b5_w1::init_connection` (41->32) => **候选：NONE** (needs a coordinated generator-side dedup; single-sided predicate rejected) |
| strict-only residues `filter_desicion`, `init_stock_pool_filter`, `_on_set_positions`, `check_baseFilename` | official-invisible (value 0 on the scoreline); `check_baseFilename` is a real logic inversion - escalated as a ruler-coverage note, **候选：NONE** this round |

Brief corrections: **none** - every step-0 pre-read (3 targets, battery 115/127 + 12 defect fns,
4 canary shas, strict 52/56 + 34/37 + 62/64) replayed byte-identically.

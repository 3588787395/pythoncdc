# R09 Test Engineer Report — backtest.pyc

## 1. Target & Status Before

- **Chosen pyc**: `site-packages/IQCommon/backtest/backtest.pyc` (IQCommon/backtest/backtest.py)
- **R08 status**: `failed` (0/2 matched, cumulative 70.90%, 27/31)
- **R09 status before fix**: `failed`
  - `<module>`: orig=83 decomp=81 jump_diffs=0 true_diffs=8
  - `handle_backtest_build`: orig=665 decomp=631 jump_diffs=19 **true_diffs=327**
  - first_diff at index 316: orig_op=LOAD_CONST `'\n# 用于打印so报错信息\nimport faulthandler\nfaulthandler.enable(open("'`, decomp_op=LOAD_CONST `',\n        "debug_port": '`
- backtestOK.py **parses OK** (no SyntaxError) — the failure is a semantic true_diff mismatch, not a crash.

## 2. Decompile + Disassembly

Full disassembly of `handle_backtest_build` dumped to `_backtest_disasm.txt` (797 lines). Key region — the `user_code` f-string assignment (bytes 1334–1456):

```
125  1332 STORE_FAST 32 (so_error_path)         # previous assignment ends
125  1334 LOAD_CONST 38 ('\n# 用于打印so报错信息\nimport faulthandler\nfaulthandler.enable(open("')
181  1336 LOAD_FAST 32 (so_error_path)
     1338 FORMAT_VALUE 1 (str)
     1340 LOAD_CONST 39 ('",\'a+\'), all_threads=True)\n...')
     ...  (20 more LOAD_CONST/LOAD_x/FORMAT_VALUE segments, 2 of which contain COMPARE_OP)
182  1398 LOAD_FAST 2 (frequency)
     1400 LOAD_CONST 30 ('tick')
     1402 COMPARE_OP 3 (!=)                      # <-- COMPARE_OP #1 inside f-string
     1408 FORMAT_VALUE 1 (str)
     ...
     1418 LOAD_FAST 27 (enable_debug)
     1420 LOAD_CONST 49 ('true')
     1422 COMPARE_OP 2 (==)                      # <-- COMPARE_OP #2 inside f-string
     1428 FORMAT_VALUE 1 (str)
     1430 LOAD_CONST 50 (',\n        "debug_port": ')
     ...
183  1448 LOAD_FAST 8 (user_variables)
     1450 FORMAT_VALUE 1 (str)
     1452 LOAD_CONST 52 (')\n')
128  1454 BUILD_STRING 25                       # 25 segments expected
     1456 STORE_FAST 33 (user_code)
```

The entire chain lives in a **single basic block** (block @ offset 1188, 97 instrs) — confirmed via `diag_dump_cfg.py`. No block split.

## 3. AST Inspection

`diag_dump_ast.py` (monkey-patches `RegionASTGenerator.generate`) shows the generated AST for `user_code`:

```
[orelse[20]] Assign target=user_code value_type=JoinedStr values_count=5
  [0] Constant ',\n        "debug_port": '        # LOAD_CONST 50
  [1] FormattedValue inner=Name (DEFAULT_PORT)
  [2] Constant ',\n    },\n    "plugin_fly_api":...'
  [3] FormattedValue inner=Name (user_variables)
  [4] Constant ')\n'
```

**Only 5 of 25 segments survive.** The first 20 segments (LOAD_CONST 38 … LOAD_CONST 49 + their FORMAT_VALUEs) are dropped. The JoinedStr starts at LOAD_CONST 50 (offset 1430), which is the first LOAD_CONST **after** the second COMPARE_OP.

## 4. Root Cause

`diag_trace_reconstruct.py` (monkey-patches `ExpressionReconstructor.reconstruct`) shows TWO reconstruct calls for the block:

1. **9 instrs** (offsets 1428–1454) → JoinedStr(5 values) — this becomes `user_code`'s value.
2. **96 instrs** (whole block) → Call (`os.path.exists(dir_path)`) — the if-condition.

The 9-instr call is the smoking gun: `reconstruct` is being fed only the tail of the f-string chain.

**Responsible code**: `_if_extract_cond_instructions` in `core/cfg/region_ast_generator.py` lines 9419–9421:

```python
if instr.opname == 'COMPARE_OP' and pre_seen_store:
    pre_instrs = []
    continue
```

This heuristic clears `pre_instrs` when a `COMPARE_OP` is seen after any STORE in the condition block. Intent: after the last pre-statement STORE, the next COMPARE_OP is assumed to be the start of the `if` condition, so stray accumulated instructions are discarded.

**Why it breaks**: `COMPARE_OP` can legitimately appear **inside an f-string FormattedValue** (e.g. `f'{a != b}'`, `f'{enable_debug == "true"}'`). When the condition block contains an f-string assignment with an embedded comparison, the heuristic fires at the first in-f-string COMPARE_OP and **discards all accumulated f-string fragments**. The f-string chain is severed; only the tail after the last COMPARE_OP reaches `BUILD_STRING`, producing a truncated JoinedStr.

In backtest.pyc, the heuristic fires twice (offsets 1402 and 1422), discarding segments 1–20 of 25. `BUILD_STRING 25` then pops only 5 available values.

## 5. Minimal Repros

14 repros in `minimal_repros/` (9 DEFECT-REPRO before fix, 5 control/OK):

| # | Name | Expected | Actual | Status |
|---|------|----------|--------|--------|
| 01 | fstring_neq_in_if_cond_block | 5 | 1 | DEFECT |
| 02 | fstring_eq_in_if_cond_block | 5 | 1 | DEFECT |
| 03 | fstring_multi_compare | 8 | 1 | DEFECT |
| 04 | fstring_long_chain_with_compare | 11 | 5 | DEFECT |
| 05 | fstring_compare_first_segment | 4 | 3 | DEFECT |
| 06 | fstring_compare_last_segment | 4 | 0 | DEFECT |
| 07 | fstring_gt_lt_compare | 8 | 1 | DEFECT |
| 08 | fstring_compare_with_method_call | 4 | 1 | DEFECT |
| 09 | fstring_two_assigns_before_if | 4 | 4 | OK |
| 10 | ctrl_no_fstring_compare_in_if | 0 | 0 | OK |
| 11 | ctrl_fstring_no_compare | 5 | 5 | OK |
| 12 | fstring_chained_compare | 4 | 0 | DEFECT |
| 13 | fstring_compare_in_elif_block | 4 | 4 | OK |
| 14 | fstring_compare_in_while_cond_block | 4 | 4 | OK |

## 6. Hypothesis

If the `COMPARE_OP` clearing heuristic is guarded so it does NOT fire when `pre_instrs` contains `FORMAT_VALUE` (a reliable marker that we are mid-f-string chain), the f-string will be preserved end-to-end and `BUILD_STRING 25` will receive all 25 stack values. Normal if-condition extraction (no FORMAT_VALUE in pre_instrs) retains the original clearing behavior.

## 7. Verification Plan

1. Apply fix to `_if_extract_cond_instructions`.
2. Re-run `verify_repros.py` → expect 0 DEFECT-REPRO.
3. Re-run `pyc_batch_verify.py single backtest.pyc` → expect `ok` or `partial`.
4. Regression: `pyc_batch_verify.py batch` → expect no degradation vs R08 (1 failed, 154 passed, 19 errors).

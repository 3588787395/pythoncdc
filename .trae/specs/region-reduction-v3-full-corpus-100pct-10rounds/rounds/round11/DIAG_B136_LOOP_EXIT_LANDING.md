# DIAG B136 — `handlers.TWHThreadController._target`: loop-exit landing never requested

Round 11 ticket **B136**. **Diagnosis only**: no `core/` edit, no git write, no 402 gate.
Scratch: `D:/Temp/r136/`. Judge: `scripts/pyc_verify.py` (compare-only).
Interpreter reading used everywhere: `python -X utf8` (PYTHONIOENCODING never set).

Working-tree state at the moment every number below was taken (re-checked before/after):

| file | sha256[:16] | note |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `e9a8f65f6451bcc8` | sealed HEAD bytes, 59108 lines |
| `core/cfg/region_analyzer.py` | `38a1d5142d132fd7` | sealed HEAD bytes |
| `git status --porcelain -- core/` | empty | no in-flight patch from B132/B133 in this tree |

(written incrementally — sections are filled as measurements land)

## 0. Established starting facts (from B127, taken as given, not re-derived blindly)

* unit diff: orig 199 instrs / prod 197, 17 hunks, exactly ONE content diff
  `delete orig[75:77] = LOAD_CONST None | RETURN_VALUE` (the other 16 = target-only shifts).
* `[G7]` (`region_ast_generator.py:51806-51812`) never runs for this unit; the all-or-nothing
  loop breaks at **G4b on `@404`** (`:51799`).
* `_r8_b121_implicit_tail_landing_sinks` is suppression-only (`:51909` emits an empty stmt list);
  forcing `{@408}` / `{@404,@408}` drops prod to 195 instrs, hunks stay 17.
* `_generate_block_statements` is claimed never to be called for `@404`; sole requester for
  `@408` is `_loop_generate_while` (stack line `:8007` = the `_if_generate_branch_stmts` fallback).

All of the above was **re-measured independently** in §1/§2 below before anything was built on it.

## 1. Q1 — real-pipeline trace (instrumented, not inferred)

TO FILL.

## 2. Q2 — semantics decision + violated principle

TO FILL.

## 3. Q3 — roster cross-check (trade_info_utils / quote / klinedata / wizard_quant_api)

TO FILL.

## 4. Q4 — battery readings (`r10g7_*`, 19 arms)

TO FILL.

## 5. Q5 — minimal repro arms compiled with local CPython 3.11.7

TO FILL.

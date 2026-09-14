# Decompile Report: jq_trans_module.pyc

## Overall Statistics

| Metric | Value |
|--------|-------|
| Total functions | 63 |
| Perfectly matched (opcode + args identical) | 58 |
| Structural diff (opcode sequence differs) | 5 |
| Match rate (perfect) | 58/63 = 92.1% |

> Note: The initial raw comparison showed 35/63 mismatched because code object identity
> (address, filename) differs between orig and recompiled. After filtering these cosmetic
> differences, only 5 functions have real structural bytecode differences.

## Structural Diffs (opcode sequence or length differs)

| # | Function | Diff Type | Orig | Recomp | First Diff Position | First Diff Detail | Region |
|---|----------|-----------|------|--------|---------------------|-------------------|--------|
| 1 | func_attribute_history_convert_code.replace_args | recomp_shorter | 389 | 384 | #102 | orig=`POP_JUMP_FORWARD_IF_FALSE` recomp=`POP_JUMP_FORWARD_IF_TRUE` | TRY |
| 2 | func_get_bars_convert_code.replace_args | recomp_shorter | 708 | 702 | #102 | orig=`POP_JUMP_FORWARD_IF_FALSE` recomp=`POP_JUMP_FORWARD_IF_TRUE` | TRY |
| 3 | func_get_price_convert_code.replace_args | recomp_shorter | 272 | 271 | #178 | orig=`SWAP(arg=2)` recomp=`POP_TOP` | TRY |
| 4 | func_history_convert_code.replace_args | recomp_shorter | 285 | 284 | #178 | orig=`SWAP(arg=2)` recomp=`POP_TOP` | TRY |
| 5 | trans_code | recomp_longer | 202 | 203 | #42 | orig=`LOAD_FAST(flag)` recomp=`JUMP_BACKWARD` | LOOP |

## Jump-Offset-Only Diffs

None. After filtering cosmetic differences (code object identity), all 58 perfectly matched
functions have identical opcode sequences AND identical jump target offsets.

## Root Cause Analysis

### RC1: try/except if-condition Polarity Error (POP_JUMP_IF_FALSE vs POP_JUMP_IF_TRUE)

- **Pattern**: In `replace_args` functions with try/except, the decompiler generates `POP_JUMP_FORWARD_IF_TRUE` where the original has `POP_JUMP_FORWARD_IF_FALSE` at the `if "'" not in stock:` condition after `except:`. This is a condition polarity inversion.
- **Effect**: The decompiled code inverts `if not condition` to `if condition` or vice versa. Specifically, `if "'" not in stock:` is decompiled as `if "'" in stock:`, changing program semantics.
- **Affected**: `func_attribute_history_convert_code.replace_args` (5 instrs shorter), `func_get_bars_convert_code.replace_args` (6 instrs shorter)
- **First diff at**: instruction #102 — `POP_JUMP_FORWARD_IF_FALSE` → `POP_JUMP_FORWARD_IF_TRUE`
- **Bytecode evidence**:
  ```
  ORIG  #102: POP_JUMP_FORWARD_IF_FALSE  (skip else when condition IS true)
  RECOMP #102: POP_JUMP_FORWARD_IF_TRUE   (skip else when condition IS false)
  ```
  The condition `if "'" not in stock:` compiles to `CONTAINS_OP(0) + POP_JUMP_FORWARD_IF_FALSE`.
  Decompiler incorrectly emits `CONTAINS_OP(0) + POP_JUMP_FORWARD_IF_TRUE`, which negates the condition.
- **Algorithm Deviation**: `region_ast_generator.py:_if_generate_branch_stmts` — When the condition expression is a negated check (`not in`, `is not None`), the `_negate_expr` function is applied in the wrong direction for `POP_JUMP_IF_FALSE`. The branch target analysis confuses the then-block and else-block, leading to inverted polarity.
- **Fix**: In `_if_generate_branch_stmts`, when the original has `POP_JUMP_IF_FALSE` after `CONTAINS_OP(0)` (which means `x not in y`), do NOT negate. Only negate for `POP_JUMP_IF_TRUE`. The current code always negates for one polarity, causing double-negation or missed-negation.

### RC2: try/except except-return SWAP/POP_TOP Stack Cleanup

- **Pattern**: Original bytecode uses `SWAP(arg=2) + POP_TOP` to preserve match_group_0 on the stack for RETURN_VALUE after except handler cleanup. Decompiler generates `POP_TOP + POP_TOP + POP_TOP + LOAD_CONST(None) + RETURN_VALUE` instead, losing the match_group_0 value.
- **Effect**: Recompiled bytecode returns `None` instead of `match_group_0` — semantically wrong. Also 1 instruction shorter (272→271, 285→284).
- **Affected**: `func_get_price_convert_code.replace_args`, `func_history_convert_code.replace_args`
- **First diff at**: instruction #178 — `SWAP(arg=2)` → `POP_TOP`
- **Bytecode evidence**:
  ```
  ORIG  #178: SWAP 2          (swap match_group_0 to top for return)
  ORIG  #179: POP_TOP          (pop the exception context)
  ORIG  #180: SWAP 2          (swap match_group_0 back)
  ORIG  #181: POP_TOP          (pop remaining context)
  ORIG  #182: RETURN_VALUE     (return match_group_0)
  
  RECOMP #178: POP_TOP         (pop match_group_0 - WRONG!)
  RECOMP #179: POP_TOP         (pop context)
  RECOMP #180: POP_TOP         (pop remaining context)
  RECOMP #181: LOAD_CONST None (push None as return value)
  RECOMP #182: RETURN_VALUE    (return None - WRONG!)
  ```
- **Algorithm Deviation**: `region_ast_generator.py:_generate_except_handler` — The except handler cleanup treats all POP_TOP and SWAP as noise to strip (base_skip = {POP_EXCEPT, RERAISE, SWAP, COPY, ...}). When SWAP is used to preserve a local variable for return, it is incorrectly stripped, causing the return value to be `None` instead of the preserved variable.
- **Fix**: Before stripping SWAP instructions in except handler cleanup, check if the SWAP is preserving a value for RETURN_VALUE. Pattern: `LOAD_FAST <var> + SWAP(2) + POP_TOP + ... + RETURN_VALUE` means `return <var>`. Track the SWAP destination to reconstruct the correct return expression.

### RC3: continue-in-for-loop Extra JUMP_BACKWARD (trans_code)

- **Pattern**: In `trans_code`, the decompiler inserts an extra `JUMP_BACKWARD` instruction at position #42 where the original has `LOAD_FAST(flag)`. This happens at the boundary of a `continue` statement inside a nested for loop.
- **Effect**: Recompiled bytecode is longer by 1 instruction (202→203).
- **First diff at**: instruction #42 — `LOAD_FAST(flag)` → `JUMP_BACKWARD(44)`
- **Bytecode evidence**:
  ```
  ORIG  #40: STORE_FAST right_num
  ORIG  #41: JUMP_BACKWARD 44    (continue: back to inner for-loop header)
  ORIG  #42: LOAD_FAST flag      (start of outer if-condition)
  
  RECOMP #40: STORE_FAST right_num
  RECOMP #41: JUMP_BACKWARD 44   (continue: back to inner for-loop header)
  RECOMP #42: JUMP_BACKWARD 44   (EXTRA: redundant back-edge!)
  RECOMP #43: LOAD_FAST flag     (start of outer if-condition, shifted by 1)
  ```
- **Algorithm Deviation**: `region_ast_generator.py:_generate_loop_stmts` — When the inner for-loop body ends with `continue` (JUMP_BACKWARD to inner loop header), the decompiler correctly emits the JUMP_BACKWARD for the inner continue. But then the outer for-loop's iteration also emits a JUMP_BACKWARD at the same point, creating a duplicate. The `_generate_continue_stmt` method or the loop-back-edge generation does not detect that a JUMP_BACKWARD was already emitted for the inner loop's continue, and emits another one for the outer loop's implicit iteration jump.
- **Fix**: After emitting `continue` (JUMP_BACKWARD for inner loop), mark the control flow as "already has back-edge" so the outer loop does not emit a duplicate JUMP_BACKWARD. Alternatively, detect that a `continue` is the last statement in the inner loop body and skip the outer loop's implicit back-edge emission.

### RC4: Compound condition in except handler reconstruction (replace_args)

- **Pattern**: In `replace_args` functions with complex except handlers containing `if/elif` chains with `in` and `not in` checks, the decompiler incorrectly reconstructs the condition polarity and the if/elif branch structure. This combines with RC1 (polarity inversion) and RC2 (SWAP stack) to produce shorter bytecode.
- **Effect**: Recompiled bytecode is 3-6 instructions shorter due to missing conditions and wrong polarity.
- **Affected**: `func_attribute_history_convert_code.replace_args` (5 shorter), `func_get_bars_convert_code.replace_args` (6 shorter)
- **Algorithm Deviation**: `region_ast_generator.py:_if_generate_branch_stmts` — When reconstructing `if x in y and z not in y:` compound conditions from bytecode, the branch target analysis incorrectly determines which block is the then-branch vs else-branch, especially when the branches contain `return` statements. The `_negate_expr` function is applied to the wrong branch, causing double-negation.
- **Fix**: In `_if_generate_branch_stmts`, for compound conditions (`and`/`or` with `CONTAINS_OP`), trace the jump targets more carefully. When `POP_JUMP_IF_FALSE` follows `CONTAINS_OP(0)` (not-in), the condition is `x not in y`, which should NOT be negated. Only negate when the jump target analysis confirms the then-block and else-block are swapped.

## Region Type Distribution

| Region Type | Count |
|-------------|-------|
| LOOP | 1 |
| TRY | 4 |

## Algorithm Deviation Points Summary

| Deviation Point | Affected Functions | Root Cause | RC |
|-----------------|---------------------|------------|-----|
| region_ast_generator.py:_if_generate_branch_stmts | replace_args (attribute_history, get_bars) | Condition polarity inversion (POP_JUMP_IF_FALSE→IF_TRUE) | RC1 |
| region_ast_generator.py:_generate_except_handler | replace_args (get_price, history) | SWAP/POP_TOP stack cleanup strips return value | RC2 |
| region_ast_generator.py:_generate_loop_stmts | trans_code | Extra JUMP_BACKWARD for continue-in-nested-loop | RC3 |
| region_ast_generator.py:_if_generate_branch_stmts | replace_args (attribute_history, get_bars) | Compound condition in except handler reconstruction | RC4 |

## Minimal Reproduction Tests

See `minimal_repros/` directory for self-contained .py files.

| Repro | Root Cause | Verified Structural Diff? |
|-------|------------|--------------------------|
| repro_01_try_except_nop_alignment.py | RC1: try/except condition polarity | NO (simple case works) |
| repro_02_except_return_swap_cleanup.py | RC2: except-return SWAP | NO (simple case works) |
| repro_03_except_nested_if_nop.py | RC1+RC4: except nested if polarity | NO (simple case works) |
| repro_04_for_else_continue_extra_jump_backward.py | RC3: continue-in-loop JUMP_BACKWARD | YES (+1 instr, JUMP_BACKWARD insertion) |
| repro_05_multi_except_handler_return_swap.py | RC2: multi except SWAP | NO (simple case works) |
| repro_06_for_loop_try_except_for_iter_offset.py | RC1+RC3: for+try offset | NO (simple case works) |
| repro_07_except_if_elif_chain_reconstruction.py | RC4: except if/elif chain | YES (-6 instrs, missing branches) |
| repro_08_bare_except_return_match_swap.py | RC2: bare except SWAP | NO (simple case works) |
| repro_09_except_complex_expr_stack_mismatch.py | RC2: complex expr SWAP | NO (simple case works) |
| repro_10_for_try_continue_jump_backward.py | RC3: for+try+continue | NO (simple case works) |
| repro_11_value_type_change_if_in_chain.py | RC1+RC4: value type change | NO (simple case works) |
| repro_12_except_dual_return_swap_pattern.py | RC2: dual return SWAP | NO (simple case works) |
| repro_13_replace_args_try_except_for_loop.py | RC1+RC2+RC4: real pattern | YES (-3 instrs, POP_JUMP_IF polarity + missing instrs) |
| repro_14_get_price_replace_args_for_loop.py | RC2: SWAP vs POP_TOP | YES (SWAP→POP_TOP opcode change) |
| repro_15_trans_code_full_pattern.py | RC3: trans_code pattern | NO (PERFECT MATCH) |
| repro_16_simple_return_match_group.py | RC2: return match_group | NO (PERFECT MATCH) |
| repro_17_nested_closure_try_except.py | RC1+RC2: nested closure | NO (PERFECT MATCH) |

## Conclusion

Of 63 functions in jq_trans_module.pyc:
- **58/63 (92.1%)** achieve PERFECT_MATCH (identical opcode sequence and arguments)
- **5/63 (7.9%)** have structural bytecode differences

The 5 structurally-different functions map to 4 root causes:

1. **RC1** (affects 2 functions): Condition polarity inversion — `POP_JUMP_IF_FALSE` → `POP_JUMP_IF_TRUE`
   - Deviation: `region_ast_generator.py:_if_generate_branch_stmts` (line ~4600)
   - Severity: **HIGH** — changes program semantics (condition negated)

2. **RC2** (affects 2 functions): SWAP/POP_TOP stack cleanup — `SWAP(2)` → `POP_TOP`
   - Deviation: `region_ast_generator.py:_generate_except_handler` (line ~4780, base_skip set includes SWAP)
   - Severity: **HIGH** — returns `None` instead of `match_group_0` (semantic error)

3. **RC3** (affects 1 function): Extra JUMP_BACKWARD for continue-in-nested-loop
   - Deviation: `region_ast_generator.py:_generate_loop_stmts` (line ~5590)
   - Severity: **LOW** — extra instruction, but semantics preserved

4. **RC4** (affects 2 functions, combined with RC1): Compound condition in except handler reconstruction
   - Deviation: `region_ast_generator.py:_if_generate_branch_stmts` (line ~4600)
   - Severity: **MEDIUM** — missing branches, but triggered only in complex except handlers

**Priority**: Fix RC1 and RC2 first (semantic errors). RC3 and RC4 are lower priority.
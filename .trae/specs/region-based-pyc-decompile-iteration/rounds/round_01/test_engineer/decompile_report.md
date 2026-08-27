# Decompile Report: Round 01 - strategy.pyc and IQCommon Batch Test

**Date:** 2026-08-27  
**Python Version:** 3.11.7  
**Decompiler:** pycdc (region mode)  
**Target:** `site-packages/IQCommon/strategy/strategy.pyc` + full IQCommon batch

---

## 1. Strategy.pyc Target Results

| Metric | Value |
|--------|-------|
| Total functions in original pyc | 2 |
| Matched functions | 1 |
| Mismatched functions | 1 |
| Match rate | 50.0% |

### Matched Functions
- `trade_strategy_add` - 314 instructions, exact match

### Mismatched Functions

#### `<module>` - 39 diffs (orig=84 instrs, decomp=75 instrs)

The decompiler entirely dropped the combined bare-import + from-import statement:
```python
import fly.common.enums
from fly.common.enums import common, enums
```

Original bytecode at offsets 90-106:
```
90  LOAD_CONST    0
92  LOAD_CONST    None
94  IMPORT_NAME   fly.common.enums
96  IMPORT_FROM   common
98  SWAP          2
100 POP_TOP
102 IMPORT_FROM   enums
104 STORE_NAME    enums
106 POP_TOP
```

The decompiled output completely omits these 9 instructions, causing all subsequent imports to shift by -9 positions. The `import X` bare import followed by `from X import Y` from the same module is a pattern where Python 3.11 combines both into IMPORT_NAME calls, but the decompiler drops the bare import when it sees a from-import from the same module.

**Root Cause:** The decompiler fails to recognize the combined bare-import + from-import pattern in Python 3.11. When `import X` and `from X import Y` appear for the same module, CPython 3.11 generates them as separate IMPORT_NAME calls, but the decompiler's region-based analysis drops the first bare import when immediately followed by a from-import from the same module.

---

## 2. Full IQCommon Batch Results

| Metric | Value |
|--------|-------|
| Total pyc files tested | 71 |
| Total functions | 944 |
| Matched functions | 821 |
| Mismatched functions | 123 |
| Match rate | 87.0% |
| Files with at least 1 mismatch | 27 |

---

## 3. Root Cause Categories

### P1: Combined bare-import + from-import dropped (2 functions)

When both `import X` and `from X import Y` exist for the same module, the decompiler drops the bare import statement. The IMPORT_NAME with None fromlist is lost.

**Affected:** `<module>` in strategy.pyc, `<module>` in const.pyc

### P2: try/except structure misreconstructed (14 functions)

The most prevalent failure. The decompiler fails to correctly reconstruct exception handlers. Specific sub-patterns:
- POP_EXCEPT/RERAISE sequence wrong
- Exception handler boundary misplaced (JUMP_FORWARD points to wrong location)
- Bare `except:` handler generates wrong bytecode sequence
- try/except/finally nesting incorrect

**Typical diff pattern:**
```
ORIG: POP_EXCEPT None        | DECOMP: JUMP_FORWARD <offset>
ORIG: LOAD_CONST 0           | DECOMP: RERAISE 1
ORIG: RETURN_VALUE None      | DECOMP: COPY 3
ORIG: RERAISE 0              | DECOMP: POP_EXCEPT None
```

**Affected:** apply_rules.decorator.api_rule_check_wrapper, Instance._init_config, Instance._get_manage_info, Instance.run, params_analysis, api_get_from_zeromq, add_process_to_cgroup, send_email, add_user_info, kill_trade_process, user_list_get, query_strategy_id, get_strategy_code_info, set_cgroup_config, format_engine, and many more

### P3: try/except/else - else clause merged into try body (5 functions)

The `else` clause of try/except/else gets absorbed into the try body or lost entirely. The compiler generates different bytecode for code in the else clause vs. code in the try body.

**Typical diff pattern:**
```
ORIG: JUMP_FORWARD <handler>  | DECOMP: LOAD_CONST None
ORIG: LOAD_FAST <var>         | DECOMP: RETURN_VALUE None
ORIG: LOAD_METHOD <m>         | DECOMP: LOAD_FAST <var>
```

**Affected:** to_pd_result, financial_statements, get_fields, get_valuation_new, get_pit_financial_date_mode, crypto_utils.aes_encrypt, crypto_utils.aes_decrypt

### P4: with statement context manager mishandled (5 functions)

The `with` statement's BEFORE_WITH/SWAP/POP_TOP sequence is incorrect. The decompiler generates wrong cleanup code for context managers.

**Typical diff pattern:**
```
ORIG: SWAP 2                  | DECOMP: POP_TOP None
ORIG: POP_TOP None            | DECOMP: LOAD_CONST None
```

**Affected:** entrust_risk_info_get, get_user_info, trade_operation, FileIO.__init__, verify_user_py_code, read_config

### P5: Condition jump polarity inversion (6 functions)

Jump instructions have their polarity inverted: `POP_JUMP_IF_NOT_NONE` vs `POP_JUMP_IF_NONE`, `JUMP_IF_TRUE_OR_POP` vs `POP_JUMP_IF_TRUE`, `POP_JUMP_IF_TRUE` vs `POP_JUMP_IF_FALSE`.

**Typical diff pattern:**
```
ORIG: POP_JUMP_FORWARD_IF_NOT_NONE <offset>  | DECOMP: POP_JUMP_FORWARD_IF_NONE <offset>
ORIG: JUMP_IF_TRUE_OR_POP <offset>           | DECOMP: POP_JUMP_FORWARD_IF_TRUE <offset>
```

**Affected:** parse_db_url, get_local_financial_date_mode.<lambda>, get_local_financial_year_mode.<lambda>, Instance.datetime, save_user_info, create_user_code_iqe

### P6: frozenset literal decompiled as tuple (3 functions)

`frozenset({...})` constant is decompiled as a plain tuple `(...)`. The compiler treats frozenset and tuple as different constant types.

**Typical diff pattern:**
```
ORIG: LOAD_CONST frozenset({'d', 'm', 'q', 'y'})  | DECOMP: LOAD_CONST ('q', 'm', 'y', 'd')
```

**Affected:** ArgumentChecker._is_valid_interval, log_request, content_trailing_handle

### P7: Closure cell variable mishandled (8 functions)

Nested function closures lose their MAKE_CELL/LOAD_CLOSURE/STORE_DEREF/COPY_FREE_VARS instructions. Entire nested functions may be missing or have wrong free variable counts.

**Typical diff pattern:**
```
ORIG: MAKE_CELL func           | DECOMP: LOAD_CONST attribute_history
ORIG: MAKE_CELL param_info     | DECOMP: STORE_FAST func
ORIG: COPY_FREE_VARS 6         | DECOMP: LOAD_CONST None
ORIG: LOAD_GLOBAL remove_space | DECOMP: RETURN_VALUE None
```

**Affected:** func_attribute_history_convert_code, func_attribute_history_convert_code.replace_args, func_get_bars_convert_code, func_get_bars_convert_code.replace_args, get_DMI.calculate_di, get_DMI.calculate_di.<genexpr>, add_end_flag, add_end_flag.<listcomp>, get_strategy_finance_factor_info, load_ini

### P8: For loop break/continue structure (6 functions)

FOR_ITER loops with break or continue statements generate wrong JUMP_BACKWARD/JUMP_FORWARD targets. The loop exit path is misrouted.

**Typical diff pattern:**
```
ORIG: JUMP_BACKWARD 176    | DECOMP: JUMP_FORWARD 1104
ORIG: POP_JUMP_IF_TRUE 262 | DECOMP: POP_JUMP_IF_TRUE 340
```

**Affected:** fill_kline_data_by_pre, fill_kline_data, func_get_fundamentals_daily_data, get_pit_financial_year_mode, get_strategy_finance_factor_info.add_to_strategy_info, get_kline_time_by_frequency_array.<listcomp>

### P9: Large function control flow drift (16 functions)

Functions over ~100 instructions show cascading jump offset drifts. Often a compound of P2/P3/P8 issues where an early mis-decompilation causes all subsequent jump offsets to shift. The instruction count difference grows with function size.

**Affected:** get_history_common, get_price_common, kline_datetime_list, get_multiminute_his_data, check_limit_common, read_config_file, backtest_download_result, creat_sheet2, FileIO.read, FileIO.write, get_backtest_list, get_last_stat, add_strategy_default, delete_cgroup_config, get_trade_list, trade_status_check_hg, ModelGraph._process_task_queue

### P10: async/await coroutine (1 function)

GET_AWAITABLE/SEND/YIELD_VALUE sequence wrong. Async functions with `await` are decompiled with wrong coroutine protocol.

**Affected:** jupyterhub_prepare

### P11: assert statement (1 function)

`assert` statement decompiled incorrectly - LOAD_ASSERTION_ERROR sequence wrong, message handling fails.

**Affected:** check_stock

### P12: Complex string slicing expression (1 function)

Multi-step string slicing with BUILD_SLICE/BINARY_SUBSCR sequence incorrect.

**Affected:** change_2str_of_time_2_datetime

---

## 4. Failure Pattern Categorization Summary

| Category | ID | Affected Functions | Severity |
|----------|-----|-------------------|----------|
| try/except structure | P2 | 14+ | CRITICAL |
| Large function drift (compound) | P9 | 16 | HIGH |
| Closure cell variables | P7 | 8 | HIGH |
| For loop break/continue | P8 | 6 | MEDIUM |
| Condition jump polarity | P5 | 6 | MEDIUM |
| try/except/else missing | P3 | 5+ | HIGH |
| with statement | P4 | 5 | MEDIUM |
| Combined import dropped | P1 | 2 | MEDIUM |
| frozenset as tuple | P6 | 3 | LOW |
| async/await | P10 | 1 | LOW |
| assert statement | P11 | 1 | LOW |
| Complex slicing | P12 | 1 | LOW |

---

## 5. Top 3 Root Cause Categories

1. **P2: try/except structure misreconstruction** - 14+ directly affected functions, and is the primary contributor to P9 (large function drift). Estimated total impact: 30+ functions (including P9 compound). The decompiler fails to correctly place exception handler boundaries, producing wrong POP_EXCEPT/RERAISE/COPY sequences.

2. **P9: Large function control flow drift** - 16 functions directly affected. This is typically a compound effect where an early P2/P3/P8 error cascades through the function, shifting all subsequent jump offsets. Fixing the underlying P2/P3/P8 patterns would resolve most P9 cases.

3. **P7: Closure cell variable mishandling** - 8 functions affected. The decompiler fails to generate correct MAKE_CELL/LOAD_CLOSURE/STORE_DEREF/COPY_FREE_VARS sequences for nested functions that close over variables. This can cause entire nested functions to be lost or have wrong free variable bindings.

---

## 6. Detailed Diff Listing for strategy.pyc `<module>`

| Offset | Original | Decompiled |
|--------|----------|------------|
| 45 | LOAD_CONST None | LOAD_CONST ('CUSTOM_STRATEGY_NAME_DICT', 'CUSTOM_STRATEGY_TYPE_DICT', 'CUSTOM_STRATEGY_NAME_TO_TYPE_NAME', 'STRATEGY_PROFILE') |
| 46 | IMPORT_NAME fly.common.enums | IMPORT_NAME IQCommon.const |
| 47 | IMPORT_FROM common | IMPORT_FROM CUSTOM_STRATEGY_NAME_DICT |
| 48 | SWAP 2 | STORE_NAME CUSTOM_STRATEGY_NAME_DICT |
| 49 | POP_TOP None | IMPORT_FROM CUSTOM_STRATEGY_TYPE_DICT |
| 50 | IMPORT_FROM enums | STORE_NAME CUSTOM_STRATEGY_TYPE_DICT |
| 51 | STORE_NAME enums | IMPORT_FROM CUSTOM_STRATEGY_NAME_TO_TYPE_NAME |
| 52 | POP_TOP None | STORE_NAME CUSTOM_STRATEGY_NAME_TO_TYPE_NAME |
| 53 | LOAD_CONST 0 | IMPORT_FROM STRATEGY_PROFILE |
| 54 | LOAD_CONST ('CUSTOM_STRATEGY_NAME_DICT', 'CUSTOM_STRATEGY_TYPE_DICT', 'CUSTOM_STRATEGY_NAME_TO_TYPE_NAME', 'STRATEGY_PROFILE') | STORE_NAME STRATEGY_PROFILE |
| 55 | IMPORT_NAME IQCommon.const | POP_TOP None |
| 56 | IMPORT_FROM CUSTOM_STRATEGY_NAME_DICT | LOAD_CONST 0 |
| 57 | STORE_NAME CUSTOM_STRATEGY_NAME_DICT | LOAD_CONST ('aes_encrypt',) |
| 58 | IMPORT_FROM CUSTOM_STRATEGY_TYPE_DICT | IMPORT_NAME IQCommon.util.crypto_utils |
| 59 | STORE_NAME CUSTOM_STRATEGY_TYPE_DICT | IMPORT_FROM aes_encrypt |
| 60 | IMPORT_FROM CUSTOM_STRATEGY_NAME_TO_TYPE_NAME | STORE_NAME aes_encrypt |
| 61 | STORE_NAME CUSTOM_STRATEGY_NAME_TO_TYPE_NAME | POP_TOP None |
| 62 | IMPORT_FROM STRATEGY_PROFILE | LOAD_CONST 0 |
| 63 | STORE_NAME STRATEGY_PROFILE | LOAD_CONST ('get_pre_half_year_date', 'get_pre_one_day_date') |
| 64 | POP_TOP None | IMPORT_NAME IQCommon.util.strategy_info_utils |

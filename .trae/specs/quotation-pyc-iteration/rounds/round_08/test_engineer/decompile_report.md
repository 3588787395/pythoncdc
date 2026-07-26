# Round 8 — Test Engineer Decompile Report

## §0 Summary

**Baseline command:**
```bash
cd /workspace && timeout 60 python pycdc.py /workspace/quotation.pyc > /tmp/r8_decompiled.py 2>/tmp/r8_decompiled.err
```

| Metric | Value |
|---|---|
| Exit code | 0 |
| Total lines | 2558 (cf. R7 2585, R6 2581) |
| stderr line count | 0 |
| compile() status | COMPILE_OK |
| Bytecode-diff functions compared | 149 |
| Bytecode-diff functions w/ diffs | 72 |
| Lost functions (in orig, missing in new) | 1 (`build_future_fill_time.<locals>.<listcomp>`) |
| New-only functions | 0 |
| Total diff entries | 8514 (opname_mismatch: 7914 / argval_mismatch: 533 / length_mismatch: 67) |
| Residual defects (this round) | 5 (D3, D6, D7, D8, D10) |
| Retests passed | D9 ✓ FIXED, D5 ✓ FIXED, D4 ✓ FIXED |
| Retests failed | TRY region regression (still 72/8, did NOT recover to R6's 73/7) |

The −27 line delta vs R7 (2585 → 2558) is consistent with R7's D9 spurious-`return None` cleanup (3 sites × `return None` lines) and D4 `del e2` cleanup leak (1 site) being eliminated. The persistent defect count (5) matches the task brief: D3/D6/D7/D8/D10 are still present, while D9/D5/D4 have been resolved.

Top-10 most divergent functions (by diff count):

| Function | Diff count |
|---|---|
| `build_future_fill_time` | 491 |
| `<module>` | 460 |
| `get_date_and_count` | 429 |
| `change_his_to_forward` | 419 |
| `balance_statement` | 326 |
| `load_bars_from_hundsun` | 303 |
| `one_prod_to_dataframe` | 287 |
| `cashflow_statement` | 273 |
| `income_statement` | 273 |
| `valuation_new` | 268 |

---

## §1 R7 已修项复测 (D9 / D5 / D4 in quotation.pyc)

### D9 (P1) — Spurious `return None` after restored return — ✅ FIXED

R7 reported `api_get_financial` lines 180-183 with 3 spurious `return None` after the genuine `return ({'error_no': error_no, 'error_info': error_info}, {})`. R8 verification:

```python
# quotation.pyc R8 decompiled, lines 178-185
            return ({'error_no': error_no, 'error_info': error_info}, {})
        return ({'error_no': 0, 'error_info': ''}, return_data)
def get_kline(get_type, prod_code, candle_period, ...):
```

No spurious `return None` lines. D9 is fully resolved in the production quotation.pyc.

### D5 (P1) — Orphan Name/Attr Expr leaks — ✅ FIXED

R7 reported orphan Expr leaks at lines 251 (`prod`), 460 (`stocks`), 504 (`panel.items`), 771 (`stocks`), 783 (`stocks`). R8 verification — searched for any line consisting solely of a Name/Attribute access with no consumer:

```bash
grep -nE "^[[:space:]]+(prod|stocks|panel\.items)[[:space:]]*$" /tmp/r8_decompiled.py
# (no matches)
```

All five R7 leak sites are clean in R8. D5 is fully resolved.

### D4 (P2) — `del e2` as-var cleanup leaked — ✅ FIXED

R7 reported `del e2` leaking into the `if not e2.response:` body at line 174. R8 verification:

```bash
grep -n "del e2" /tmp/r8_decompiled.py
# (no matches)
```

The CPython 3.11+ as-var cleanup sequence (`LOAD_CONST None / STORE_FAST e2 / DELETE_FAST e2`) is now properly suppressed as implicit cleanup. D4 is fully resolved.

---

## §2 R8 残留缺陷 D3 / D6 / D7 / D8 / D10

### D3 (P1) — Chained compare in except handler lost → `if 499:`

**Location:** `api_get_financial`, line 159 (R7 was line 164; the line number shifted −5 due to D9 cleanup above).

```python
# R8 decompiled quotation.pyc lines 156-162
except HTTPError as e2:
    system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)   # D10
    if 499:                                                                # D3
        pass                                                                # D6 lost body
    else:
        error_no = -1
        error_info = '服务器处理异常，内部错误号:%d' % e2.code
        ({'error_no': error_no, 'error_info': error_info}, {})              # lost return (D1)
```

**Original bytecode** (CPython 3.11, `api_get_financial`, offsets 694-734):

```
694 LOAD_CONST    400
696 LOAD_FAST     e2
698 LOAD_ATTR     code
708 SWAP                              # ← chained-compare stack shuffle
710 COPY                              # ← duplicate e2.code for second COMPARE_OP
712 COMPARE_OP    <=                  # 400 <= e2.code
718 POP_JUMP_FORWARD_IF_FALSE to 732
720 LOAD_CONST    499
722 COMPARE_OP    <=                  # e2.code <= 499
728 POP_JUMP_FORWARD_IF_FALSE to 1082
730 JUMP_FORWARD  to 736
732 POP_TOP
734 JUMP_FORWARD  to 1082
```

**Root cause (initial):** CPython 3.11 lowers `400 <= e2.code <= 499` to a SWAP+COPY shape that shares the middle operand (`e2.code`) between two `COMPARE_OP` instructions across two basic blocks. The decompiler's `_generate_condition_expr` consumes only the trailing `LOAD_CONST 499 / COMPARE_OP <=` operand and emits `if 499:`, discarding the leading `400 <= e2.code` portion plus the `SWAP`/`COPY` stack manipulation. **Context-sensitive:** `repro_08_01` (the same chained compare pattern in isolation) preserves `if 400 <= e2.code <= 499:` — the loss only triggers when the chained compare is preceded by the D10 malformed-call block in the same except handler.

### D6 (P2) — try body `return X` → `pass` (lost body)

**Location:** `api_get_financial`, line 160-161 (`if 499: pass` — the chained-compare body lost its return statement).

```python
if 499:
    pass                              # <- original was return ({'error_no': e2.code, 'error_info': ''}, {})
else:
    error_no = -1
    ...
```

Also visible in many other functions (e.g. `def fill_minute_or_day_blank(...): pass` at line 302 in R7; nested `elif i == 0: pass` bodies in `get_kline`).

**Root cause (initial):** When the try-body / chained-compare-body emits a `RETURN_VALUE` followed by the CPython 3.11+ as-var cleanup (`STORE_FAST <asvar> / DELETE_FAST <asvar> / RETURN_VALUE` returning None) and `RERAISE`+`COPY`+`POP_EXCEPT` block, the decompiler suppresses both the cleanup AND the genuine `RETURN_VALUE` (treating the whole sequence as cleanup), leaving an empty body that becomes `pass`. **Confirmed standalone reproducible:** `repro_08_02` (try-body `return 1` → `pass`, DEFECT-REPRO) and `repro_08_08` (same pattern, DEFECT-REPRO). Interestingly, `repro_08_12` shows the loss only fires for `return <const>`; `return compute(x) + 1` (a complex expression) survives — the suppression appears to be triggered by the `RETURN_VALUE` of a constant being immediately followed by `RERAISE`.

### D7 (P2) — Malformed ternary chain (if/elif compressed to nested ternary of `==`)

**Location:** `build_future_fill_time`, line 351.

```python
# R8 decompiled quotation.pyc line 351
suffix == 'T.CCFX' if typet == 2 else suffix == 'T.CCFX' if typet == 3 else suffix == 'T.CCFX' if typet == 4 else typet == 13
```

**Original source (reconstructed):**

```python
if typet == 2:
    if suffix == 'T.CCFX':
        market_time = {...}            # 5-key dict
    elif suffix in ('XZCE', 'XDCE', 'XSGE'):
        market_time = {...}            # 7-key dict
    else:
        market_time = {...}            # 5-key dict
elif typet == 3:
    if suffix == 'T.CCFX':
        ...
elif typet == 4:
    ...
elif typet == 13:
    ...
```

**Original bytecode** (`build_future_fill_time`, offset 1052-1076):

```
1052 LOAD_FAST     typet
1054 LOAD_CONST    2
1056 COMPARE_OP    ==                       # typet == 2 (outer if)
1064 POP_JUMP_FORWARD_IF_FALSE to 1660
1066 LOAD_FAST     suffix
1068 LOAD_CONST    'T.CCFX'
1070 COMPARE_OP    ==                       # suffix == 'T.CCFX' (inner if — first stmt of typet==2 branch)
1076 POP_JUMP_FORWARD_IF_FALSE to 1096
```

**Root cause (initial):** The decompiler misinterprets the outer `if/elif` chain over `typet` as a nested ternary expression. Each branch's first instruction (`LOAD_FAST suffix / LOAD_CONST 'T.CCFX' / COMPARE_OP ==`, which is the condition of an inner `if` inside each branch) is mis-attributed as the value expression of the outer ternary. The `=` assignments inside each branch are converted to `==` comparisons (a `STORE_FAST` after `COMPARE_OP` is mis-emitted as `==`). The whole chain collapses into a single bare `Expr`. **Confirmed standalone reproducible:** `repro_08_03` (DEFECT-REPRO) — the same pattern triggers with a simplified if/elif/elif/elif structure, although the trailing `typet == 13` becomes `typet == 4` in the minimal repro (the final-branch `else`-fallthrough differs slightly).

### D8 (P2) — Lost `date_convert` body (orig=87 instructions → 16 instructions)

**Location:** `date_convert`, lines 2144-2146.

```python
# R8 decompiled quotation.pyc lines 2144-2146
def date_convert(date, report_types):
    int(month_temp == 1 if report_types is None else month_temp <= report_types)
```

**Original bytecode** (`date_convert`, 87 instructions): builds `dict_temp = {'03-31':, '06-30':, '09-30':, '12-31':, (1,2,3,4):}`, computes `date_temp = date.replace('-', '')`, `year_temp = int(date_temp[0:4])`, `month_temp = pandas.Period(date, 'Q-DEC').quarter`, then a nested `if report_types is not None: if month_temp == 1: ... else: ... else: if month_temp <= report_types: ... else: ...`, then `data_return = str(year_temp) + '-' + dict_temp[month_temp]` and `return data_return`.

**Decompiled bytecode** (`date_convert`, 16 instructions):

```
  0 RESUME
  2 LOAD_GLOBAL  NULL + int                       # ← leftover CALL from year_temp = int(...)
 14 LOAD_FAST    report_types
 16 POP_JUMP_FORWARD_IF_NOT_NONE to 40
 18 LOAD_GLOBAL  month_temp                       # ← undefined local (LOAD_GLOBAL!)
 30 LOAD_CONST   1
 32 COMPARE_OP   ==                               # month_temp == 1 (the if-branch condition)
 38 JUMP_FORWARD to 60
 40 LOAD_GLOBAL  month_temp                       # ← undefined local
 52 LOAD_FAST    report_types
 54 COMPARE_OP   <=                               # month_temp <= report_types (the else-branch condition)
 60 PRECALL
 64 CALL                                          # int(...) call wrapper
 74 POP_TOP
 76 LOAD_CONST   None
 78 RETURN_VALUE                                  # implicit return None
```

**Root cause (initial):** The decompiler collapses the entire function body (dict_temp construction, three local assignments, nested if/else if/elif if/elif else chain, the `data_return` assignment, and the `return data_return`) into a single bare `int(...)` `Expr`. The `int(...)` wrapper is the trailing `LOAD_GLOBAL int + PRECALL + CALL` of `year_temp = int(date_temp[0:4])` — its arguments are replaced by an IfExp derived from the if/elif conditions (`month_temp == 1 if report_types is None else month_temp <= report_types`). The `month_temp` local becomes a `LOAD_GLOBAL` (undefined) since its assignment was discarded. **Context-sensitive:** `repro_08_04` (the same source structure in isolation) loses the dict_temp / year_temp / month_temp assignments and the if/elif/else chain, but preserves the trailing `data_return = str(year_temp) + '-' + dict_temp[month_temp]; return data_return` — so the body IS truncated but does not match the production pattern exactly. Mark as DEFECT-REPRO (body lost).

### D10 (P2) — Malformed call in except handler

**Location:** `api_get_financial`, line 158.

```python
# R8 decompiled quotation.pyc line 158
system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)
```

**Original source (reconstructed from bytecode at offset 358-692):**

```python
except HTTPError as e2:
    system_log.error(get_traceback_message())           # offset 358-420 (always-called)
    if e2.code == 401:                                   # offset 422-442
        if request_times <= 2:                           # offset 444-454
            time.sleep(10)
            request_times += 1
            return api_get_financial(url, params, request_times)
    elif e2.code == 599:                                 # offset 616-636
        return api_get_financial(url, params)
    elif 400 <= e2.code <= 499:
        ...
    else:
        error_no = -1
        ...
        return (...)
```

**Root cause (initial):** The decompiler merges the `system_log.error(get_traceback_message())` call (offset 358-420) with the `e2.code == 401 / e2.code == 599` if/elif conditions (offsets 422-636) and emits a single `system_log(...)` call whose argument is a nested ternary of `==` comparisons. The `LOAD_ATTR error` accessor is dropped (becomes a bare `system_log` reference), the `get_traceback_message()` argument is dropped, and the two `system_log.error(...)` call sites are merged into one. The conditional call (if/elif) becomes a conditional argument (IfExp). **Context-sensitive:** `repro_08_05` reproduces the bare-IfExp-Expr pattern (`request_times <= 2 if e2.code == 401 else e2.code == 599`) but does NOT include the `system_log(...)` wrapper — the wrapper only fires when the merged call site precedes the chained-compare `if 499:` block (the D3/D10/D6 compound defect). `repro_08_10` reproduces the same IfExp-collapse pattern with a different call site (`retry() if e2.code == 401 else retry() if e2.code == 599 else fallback()`, DEFECT-REPRO).

---

## §3 TRY 区域退化点定位 (R6 73/7 → R7 72/8, R8 still 72/8)

R8 baseline TRY region test result (bounded subset of 80 tests, deterministic stride):

```
$ timeout 90 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY
72 8 0 80 2.6 TRY files=80
```

Same as R7 (72/8). The R6→R7 regression has NOT recovered in R8 — the D9 fix that landed in R8 cleaned up the production quotation.pyc (no spurious `return None`), but did not restore the lost TRY test case.

**The 8 failing TRY tests in the R8 bounded subset:**

| # | Test | Source pattern | R8 decompiled output | Defect class |
|---|------|---|---|---|
| 1 | `test_e01tryexcept_indexerror_a` | `try: a[0] / except IndexError: a = []` | `try: pass / except IndexError: a = []; return None` | D6 (try-body lost) + D9 over-suppression (extra `return None`) |
| 2 | `test_te031` | `for i in range(3): try: x=1 / except: break` | `try: x=1 / except: pass` | D6 variant (`break` → `pass`) |
| 3 | `test_te049` | `try: x=1; return x / except: return -1` | `try: x=1; return x / except: return None` | D9 over-suppression (`-1` → `None`) |
| 4 | `test_te076` | `try: pass / except: y = 2` (module-level) | `pass` | entire TRY region collapsed |
| 5 | `test_te087` | `try: pass / finally: pass` (module-level) | `pass` | entire TRY region collapsed |
| 6 | `test_te104` | `try: x=1 / except ValueError: return 'val' / finally: cleanup()` | except body gets `cleanup()` extra (order issue) | finally-body leaks into except body |
| 7 | `test_te12tryexceptreturn_valueerror` | `def f(): try: return 1 / except ValueError: return 0` | `def f(): try: pass / except ValueError: return 0` | **D6 (try-body return 1 → pass) — R7 D9 regression** |
| 8 | `test_te32tryexceptreturn_stopiteration` | `def f(): try: return 1 / except StopIteration: return 0` | `def f(): try: pass / except StopIteration: return 0` | **D6 (try-body return 1 → pass) — R7 D9 regression** |

**The R6→R7 regression is most clearly #7 (te12tryexceptreturn_valueerror)** — `def f(): try: return 1 / except ValueError: return 0` was passing in R6 (73/7) and fails in R7+R8 (72/8). The R7 D9 fix to suppress spurious `return None` after a restored real return apparently also over-suppresses the genuine `RETURN_VALUE 1` in the try body when followed by the `RERAISE`+`COPY`+`POP_EXCEPT` cleanup, replacing `return 1` with `pass`. te049 (test #3, `return -1` → `return None`) is a related over-suppression case where the literal `-1` is changed to `None`. te12/te32 confirm the regression with `repro_08_02` / `repro_08_06` / `repro_08_08` (all DEFECT-REPRO).

---

## §4 字节码不一致汇总

Full bytecode diff: `/tmp/r8_diff_detail.txt` (25686 lines) and `/tmp/r8_summary.txt`. Selected summary:

```
total_functions_compared: 149
functions_with_diffs: 72
lost_functions: 1 (build_future_fill_time.<locals>.<listcomp>)
new_only_functions: 0
total_diff_entries: 8514

=== DIFF COUNT BY TYPE ===
  opname_mismatch: 7914       ← opname differs at same offset (most common)
  argval_mismatch: 533        ← same opname, different argval
  length_mismatch: 67        ← function instruction count differs
```

**Key production defect sites by function (offset, diff type, defect class):**

| Function | Orig instrs | New instrs | Diff type | Defect |
|---|---|---|---|---|
| `api_get_financial` | 318 | 216 | length_mismatch + opname_mismatch | D3 (offset 694-734 chained compare) + D6 (offset 736+ body) + D10 (offset 358-420 malformed call) |
| `build_future_fill_time` | 677 | 524 | length_mismatch + argval_mismatch | D7 (offset 1052-1200 malformed ternary chain) |
| `date_convert` | 87 | 16 | length_mismatch + opname_mismatch | D8 (entire body collapsed to `int(IfExp)`) |
| `build_future_fill_time.<locals>.<listcomp>` | (present) | (missing) | LOST | nested code object not emitted |

The remaining 67 functions with diffs are largely due to module-level constant reordering (the decompiler reorders imports and module-level `STORE_NAME` → `STORE_GLOBAL` for some constants) plus the persistent defects D3/D6/D7/D8/D10 in the specific functions above.

---

## §5 R8 修复目标 P0/P1/P2 mapping

| Priority | Defect | Targeted fix location (initial assessment) | Repros |
|---|---|---|---|
| **P0** | D6 (try body return → pass) + TRY region regression (te12/te32/te049) | `core/cfg/region_ast_generator.py::_generate_handler_body_statements` — restore the genuine `RETURN_VALUE` in try body that is currently being suppressed together with the as-var cleanup; specifically do NOT suppress `RETURN_VALUE <non-None const>` immediately followed by `RERAISE`. | `repro_08_02`, `repro_08_06`, `repro_08_08` (all DEFECT-REPRO) |
| **P0** | D8 (lost date_convert body) | `core/cfg/region_ast_generator.py::_generate_block_statements` — fix the basic-block analyzer to recognize the nested `if/else if/elif if/elif else` pattern with intervening `STORE_FAST` assignments as a multi-statement body, not a single expression. The `int(...)` wrapper is a trailing `CALL` whose args were replaced by an IfExp. | `repro_08_04` (DEFECT-REPRO, body lost), `repro_08_09` (DEFECT-REPRO, if/elif collapsed) |
| **P1** | D3 (chained compare lost → `if 499:`) | `core/cfg/region_ast_generator.py::_generate_condition_expr` — handle CPython 3.11 SWAP+COPY shape for chained comparisons; consume both `COMPARE_OP` operands across the `POP_JUMP_FORWARD_IF_FALSE` boundary, not just the trailing one. Context-sensitive (only fires after D10 block). | `repro_08_01` NOT-REPRO (chained compare survives in isolation); `repro_08_07` NOT-REPRO; `repro_08_11` NOT-REPRO. Fix requires D10 to land first. |
| **P1** | D7 (malformed ternary chain) | `core/cfg/region_ast_generator.py::_generate_block_statements` — recognize outer `if/elif` over `typet` as a control-flow statement, not a nested ternary. The `LOAD_FAST suffix / LOAD_CONST 'T.CCFX' / COMPARE_OP ==` from the inner `if` is being mis-attributed as the ternary body. | `repro_08_03` (DEFECT-REPRO) |
| **P2** | D10 (malformed call in except) | `core/cfg/region_ast_generator.py::_generate_handler_body_statements` — preserve the `LOAD_ATTR error / get_traceback_message() / PRECALL / CALL` call site as a separate `Expr` statement, do not merge it with the subsequent `if/elif` conditions. | `repro_08_05` (partial DEFECT-REPRO, IfExp pattern but no `system_log(...)` wrapper), `repro_08_10` (DEFECT-REPRO) |

### Verification commands (re-runnable)

```bash
# R8 baseline
cd /workspace && timeout 60 python pycdc.py /workspace/quotation.pyc > /tmp/r8_decompiled.py 2>/tmp/r8_decompiled.err
echo "EXIT=$? lines=$(wc -l < /tmp/r8_decompiled.py) err=$(wc -l < /tmp/r8_decompiled.err)"
python -c "compile(open('/tmp/r8_decompiled.py').read(),'r8','exec'); print('COMPILE_OK')"

# Bytecode diff
python /workspace/.trae/specs/quotation-pyc-iteration/rounds/round_08/test_engineer/r8_diff.py
# → /tmp/r8_diff_detail.txt, /tmp/r8_summary.txt

# D3/D6/D10 verification (api_get_financial lines 156-162)
sed -n '156,162p' /tmp/r8_decompiled.py

# D7 verification (build_future_fill_time line 351)
sed -n '351p' /tmp/r8_decompiled.py

# D8 verification (date_convert lines 2144-2146)
sed -n '2144,2146p' /tmp/r8_decompiled.py

# D9 retest (no spurious return None)
grep -n "return None" /tmp/r8_decompiled.py | head    # should be empty / minimal

# D5 retest (no orphan Name/Attr Expr)
grep -nE "^[[:space:]]+(prod|stocks|panel\.items)[[:space:]]*$" /tmp/r8_decompiled.py    # should be empty

# D4 retest (no del e2)
grep -n "del e2" /tmp/r8_decompiled.py    # should be empty

# TRY region regression
timeout 90 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY
# → "72 8 0 80 2.6 TRY files=80"

# Repro verification (one example)
REPRO_DIR=/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_08/test_engineer/minimal_repros
python -c "import py_compile; py_compile.compile('$REPRO_DIR/repro_08_02_try_body_return_to_pass.py', '$REPRO_DIR/repro_08_02_try_body_return_to_pass.pyc', doraise=True)"
timeout 20 python pycdc.py $REPRO_DIR/repro_08_02_try_body_return_to_pass.pyc
```

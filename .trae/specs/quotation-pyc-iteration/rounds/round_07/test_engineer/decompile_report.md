# Round 7 — Test Engineer Decompile Report

**Baseline:** `cd /workspace && timeout 60 python pycdc.py /workspace/quotation.pyc > /tmp/r7_decompiled.py 2>/tmp/r7.err`
- EXIT=0
- COMPILE_OK (`ast.parse` succeeds on the full output)
- 2585 lines (cf. R6 baseline 2581 lines)
- 0 stderr lines

The +4-line delta vs R6 is consistent with R6's lost-return bare-Expr sites in
`api_get_financial` now emitting additional `del e2` / `return None` cleanup
artifacts (D4 + D9) rather than restored `return` statements — the R6 D1
"lost return" defect has morphed into R7's D9 "spurious `return None` after
restored return" + persistent D4 `del e2` leak.

## Defects found in `/workspace/r7_decompiled.py` (R6 residuals D3-D10)

### D3 (P1) — Chained compare in except handler lost → `if 499:`

**Location:** line 164 (`api_get_financial`, `except HTTPError as e2:` handler).

```python
except HTTPError as e2:
    system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)   # D10
    if 499:                                                                  # D3
        pass                                                                 # D6 lost body
    else:
        error_no = -1
        error_info = '服务器处理异常，内部错误号:%d' % e2.code
        ({'error_no': error_no, 'error_info': error_info}, {})               # D1 lost return
    return None                                                              # D9 spurious
```

**Root cause:** The CPython 3.11 chained-compare bytecode
(`LOAD_CONST 400 / LOAD_FAST e2 / LOAD_ATTR code / COMPARE_OP '<=' /
POP_JUMP_IF_FALSE / LOAD_CONST 499 / COMPARE_OP '<=' / POP_JUMP_IF_FALSE`)
is split across multiple basic blocks. The decompiler's
`_generate_condition_expr` consumes only the trailing `LOAD_CONST 499`
operand and discards the leading `400 <= e2.code <=` portion, emitting
`if 499:`. The defect is context-sensitive — in isolation the chained
compare survives (see `repro_07_01`, NOT-REPRO), so the surrounding
except-handler control flow is what triggers the loss.

### D4 (P2) — `del e2` as-var cleanup leaked into handler body

**Location:** line 174 (`del e2` inside `if not e2.response:` body).

**Root cause:** CPython 3.11+ emits as-var cleanup as
`LOAD_CONST None / STORE_FAST e2 / DELETE_FAST e2` immediately before
the handler's `RETURN_VALUE`/`RERAISE`. When the cleanup is in a
fall-through block (no immediate terminator in the same block), the
`DELETE_FAST e2` is rendered as a `del e2` statement instead of being
suppressed as implicit cleanup. Confirmed in `repro_07_04` (DEFECT-REPRO).

### D5 (P1) — Orphan Name/Attr Expr leaks (LOAD_FAST/LOAD_ATTR with no consumer)

**Locations:** line 251 (`prod`), line 460 (`stocks`), line 504 (`panel.items`),
plus line 771 (`stocks`) and line 783 (`stocks`).

```python
prod = data.get(prod_code)
prod                                            # <- orphan LOAD_FAST Expr
for item in prod:
    ...
```

**Root cause:** A `LOAD_FAST`/`LOAD_ATTR`/`LOAD_SUBSCR` whose TOS result is
discarded (no following `STORE`/`CALL`/`RETURN`/`POP_TOP` absorption) leaks
as an orphan `Expr` statement. The decompiler's statement-boundary detector
fails to suppress these because the trailing `POP_TOP` is in a separate
basic block from the `LOAD_*`. Confirmed in `repro_07_02` (orphan Name,
DEFECT-REPRO — note the leak is *duplicated*, two `prod` Exprs emitted for
one source statement) and `repro_07_03` (orphan Attr `panel.items`,
DEFECT-REPRO — also duplicated).

### D6 (P2) — Lost function body / nested-if return → `pass`

**Locations:** line 165 (`pass` for the `if 499:` body in `api_get_financial`),
lines 266-279 (8 consecutive `elif i == 0: pass` whose `index.append(...)`
bodies are lost), line 302 (`def fill_minute_or_day_blank(...): pass`), lines
492/505/566 (`pass` for non-trivial bodies). Confirmed in `repro_07_05`
(try-body `return 1` → `pass`, DEFECT-REPRO). The nested-if/elif variant
(`repro_07_06`) does NOT reproduce — all branch returns are preserved when
the if/elif is a pure decision tree without surrounding try/except.

### D7 (P2) — Malformed ternary chain (line 363)

```python
suffix == 'T.CCFX' if typet == 2 else suffix == 'T.CCFX' if typet == 3 else suffix == 'T.CCFX' if typet == 4 else typet == 13
```

**Root cause:** A series of `if/elif` assignments
(`suffix = 'T.CCFX' if typet == 2 elif typet == 3 elif typet == 4 else 13`)
is reduced to a single nested ternary of `==` comparisons. The `=`
assignments become `==` comparisons (a `STORE_FAST` after `COMPARE_OP` is
mis-emitted as `==`), and the whole expression becomes a bare `Expr`.
Not reproduced minimally (`repro_07_07`, NOT-REPRO) — depends on the specific
control flow of `get_trade_calendar` where the assignment target is shared
across branches.

### D8 (P2) — Lost statement in `date_convert` (lines 2168-2169)

```python
def date_convert(date, report_types):
    int(month_temp == 1 if report_types is None else month_temp <= report_types)
```

**Root cause:** The function body (an if/elif/else chain over `month_temp`
and `report_types`) is compressed to a single bare `int(...)` `Expr`. The
`month_temp` local is undefined at the point of emission, indicating the
preceding `month_temp = int(date[5:7])` assignment and the if/elif branches
were collapsed into a single IfExp wrapped in a stray `int()` call — the
`int()` is the trailing `CALL_FUNCTION` of the assignment target, mis-emitted
as an Expr wrapper. Not reproduced minimally (`repro_07_08`, NOT-REPRO).

### D9 (P1, NEW) — Spurious `return None` after restored return in except handler

**Locations:** `api_get_financial` lines 180-183.

```python
            return ({'error_no': error_no, 'error_info': error_info}, {})   # line 180 — real return
            return None                                                     # line 181 — spurious
            return None                                                     # line 182 — spurious
            return None                                                     # line 183 — spurious
        except BaseException as e3:
```

**Root cause:** This is a NEW defect surfaced in R7. The R6 D1 "lost return"
treatment now restores the genuine `return (...)` (line 180), but the
as-var cleanup blocks that follow (`STORE_FAST e2 / DELETE_FAST e2 /
RETURN_VALUE` returning `None`) are not suppressed. Each cleanup block
re-emits its `RETURN_VALUE None` as a stray `return None` statement.
Confirmed in `repro_07_09` (DEFECT-REPRO — line 44 emits `return None`
after the lost-return bare Expr on line 42). The defect compounds with D1:
when the genuine return is restored as a real `return (...)`, the trailing
`return None`s are dead code; when it leaks as a bare Expr (D1), the trailing
`return None` becomes the *effective* control flow, masking the lost return.

### D10 (P2) — `system_log(...)` call malformed (line 163)

```python
system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)
```

**Root cause:** The handler's `if e2.code == 401: system_log(...) / elif
e2.code == 599: system_log(...)` control flow is reduced to a single
`system_log(...)` call whose argument is a nested ternary of `==`
comparisons (`request_times <= 2 if e2.code == 401 else e2.code == 599`).
The two `system_log(...)` call sites are merged and the conditional call
becomes a conditional argument. Not reproduced minimally (`repro_07_10`,
NOT-REPRO) — the if/elif call structure survives in isolation, so the
malformation depends on the broader except-handler block layout.

## Minimal repros created (10)

`/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_07/test_engineer/minimal_repros/`

| Repro | Defect | DEFECT-REPRO | Notes |
|-------|--------|:------------:|-------|
| repro_07_01_chained_compare_in_except.py | D3 chained cmp in except | ❌ NOT-REPRO | Chained `400 <= e2.code <= 499` preserved in isolation; D1 lost-return + D4 `del e2` leak visible instead |
| repro_07_02_orphan_name_expr.py | D5 orphan Name | ✅ DEFECT-REPRO | `prod` orphan Expr emitted (duplicated — two `prod` Exprs for one source stmt) |
| repro_07_03_orphan_attr_expr.py | D5 orphan Attr | ✅ DEFECT-REPRO | `panel.items` orphan Attr Expr emitted (duplicated — two leaks) |
| repro_07_04_del_asvar_leak.py | D4 `del e2` leak | ✅ DEFECT-REPRO | `del e2` leaks inside `if not e2.response:` body (line 23 of output) |
| repro_07_05_try_body_return_lost.py | D6 try-body return lost | ✅ DEFECT-REPRO | `return 1` in try body → `pass` (te12 regression confirmed) |
| repro_07_06_nested_if_return_lost.py | D6 nested-if return lost | ❌ NOT-REPRO | All if/elif branch returns preserved in pure decision tree |
| repro_07_07_malformed_ternary.py | D7 malformed ternary | ❌ NOT-REPRO | if/elif assignment chain preserved; needs `get_trade_calendar` CFG |
| repro_07_08_lost_func_body.py | D8 lost func body | ❌ NOT-REPRO | if/elif/else body preserved; needs `date_convert` IfExp nesting |
| repro_07_09_spurious_return_none.py | D9 spurious `return None` | ✅ DEFECT-REPRO | `return None` emitted after lost-return bare `({...})` Expr (line 44 of output) |
| repro_07_10_malformed_call_in_except.py | D10 malformed call arg | ❌ NOT-REPRO | if/elif `system_log(...)` call structure preserved; D1+D4 visible instead |

**Confirmed exhibiting:** 5 repros (02, 03, 04, 05, 09).
**Not reproduced:** 5 repros (01, 06, 07, 08, 10) — all context-sensitive
(defects depend on the broader except-handler / function CFG of
`api_get_financial`, `get_trade_calendar`, `date_convert` and do not
trigger in minimal standalone form).

## Fix priority for Phase 2

1. **D9 spurious `return None` after restored return (P1, NEW)** — highest
   priority. R6's D1 "lost return" morphed into R7's D9: the genuine return
   is now restored, but the trailing as-var cleanup `RETURN_VALUE None`
   blocks are not suppressed, emitting dead `return None` statements that
   mask the restored return when D1 also fires. 1 repro (09) + 3 sites in
   quotation.pyc (lines 181-183). Fix: in
   `core/cfg/region_ast_generator.py::_generate_handler_body_statements`,
   suppress cleanup-block `RETURN_VALUE None` when a preceding `Return`
   has already been emitted for the same handler.
2. **D5 orphan Name/Attr Expr leak (P1)** — 2 repros (02, 03) + 5 sites in
   quotation.pyc (lines 251, 460, 504, 771, 783). Both repros show the
   leak is *duplicated* (one source orphan → two emitted Exprs), pointing
   to a statement-boundary / POP_TOP absorption bug in
   `_generate_block_statements` rather than a clean suppression issue.
3. **D4 `del e2` as-var cleanup leak (P2)** — 1 repro (04) + 1 site
   (line 174). Clean fix: suppress `DELETE_FAST <asvar>` when it is part
   of the CPython 3.11+ as-var cleanup sequence (`LOAD_CONST None /
   STORE_FAST <asvar> / DELETE_FAST <asvar>`) preceding a terminator.
4. **D6 lost try-body return (P2)** — 1 repro (05). The te12 regression
   (`return 1` → `pass` in try body) is a clean standalone repro; attempt
   after D9 since both touch except/try handler body generation.
5. **D3 chained compare lost (P1)** — 0 standalone repros (context-sensitive);
   attempt only as part of the broader `api_get_financial` handler rewrite.
6. **D7 / D8 / D10 (P2)** — 0 standalone repros; defer to context-specific
   fixes in `get_trade_calendar` / `date_convert` / `api_get_financial`
   once D9 + D5 land and the baseline stays green.

## Verification commands (re-runnable)

```bash
# R7 baseline
cd /workspace && timeout 60 python pycdc.py /workspace/quotation.pyc > /tmp/r7_decompiled.py 2>/tmp/r7.err
echo "EXIT=$? lines=$(wc -l < /tmp/r7_decompiled.py) err=$(wc -l < /tmp/r7.err)"
python -c "import ast; ast.parse(open('/tmp/r7_decompiled.py').read()); print('COMPILE_OK')"

# Repro verification (one example)
REPRO_DIR=/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_07/test_engineer/minimal_repros
python -c "import py_compile; py_compile.compile('$REPRO_DIR/repro_07_09_spurious_return_none.py', '$REPRO_DIR/repro_07_09_spurious_return_none.pyc', doraise=True)"
timeout 20 python pycdc.py $REPRO_DIR/repro_07_09_spurious_return_none.pyc
```

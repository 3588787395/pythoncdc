# Round 6 — Test Engineer Decompile Report

**Baseline:** `python pycdc.py /workspace/quotation.pyc` → EXIT=0, COMPILE_OK, 2581 lines, 0 stderr.

## Defects found in `/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_06/r6_decompiled.py`

### D1 — Lost `return` keyword in except handler (R5 deferred Fix 3)

**Locations:** lines 161, 169, 179, 184 (function `api_get_financial`).

```python
except ConnectionRefusedError as e1:
    system_log.error(get_traceback_message())
    error_no = -1
    error_info = e1
    ({'error_no': error_no, 'error_info': error_info}, {})   # <- bare Expr, missing `return`
```

**Root cause:** In `core/cfg/region_ast_generator.py::_generate_handler_body_statements`, the
handler body is split across multiple basic blocks:
- block@234: `LOAD ... BUILD_TUPLE 2` (the return value)
- block@318: `SWAP 2`
- block@320: `POP_EXCEPT + LOAD_CONST None/STORE_FAST e1/DELETE_FAST e1 + RETURN_VALUE`

The early-fallback guard at L14079 `if len(_user_store_indices) >= 2 and not _has_return_chain:`
calls the **bool** overload of `_find_return_through_cleanup_chain` (defined at L13952, which
overrides the list-walking version at L13887). The bool version only inspects the **current**
block; block@234 has no `POP_EXCEPT` so it returns `False`, triggering the fallback to
`_generate_block_statements`, which emits the trailing `BUILD_TUPLE 2` as a bare `Expr` (the
`(...)` we see). The same defect produces bare ternary `Expr` in `repro_06_15`.

### D2 — Lost parens around Compare in low-precedence BinOp (R5 deferred Fix 4)

**Locations:** none directly in quotation.pyc (no `&`/`|`/`^` over Compare), but the code path
is exercised by `repro_06_02`. The `BinOp(BitAnd, Compare(>=), Compare(<=))` AST serialises
without operand parens, producing `a >= b & c <= d` (semantically wrong: BitAnd binds
tighter than Compare).

### D3 — Bare number as if condition (R4 deferred Fix 2 coverage gap)

**Location:** line 164 (`if 499:`).

Actual bytecode (offsets 694-728) is a **chained comparison** `400 <= e2.code <= 499`:

```
694 LOAD_CONST 400
696 LOAD_FAST 'e2'
698 LOAD_ATTR 'code'
708 SWAP 2 / 710 COPY 2 / 712 COMPARE_OP '<='
718 POP_JUMP_FORWARD_IF_FALSE 732
720 LOAD_CONST 499
722 COMPARE_OP '<='
728 POP_JUMP_FORWARD_IF_FALSE 1082
```

The decompiler drops the chained comparison and keeps only the final `LOAD_CONST 499`,
emitting `if 499:`. Confirmed in `repro_06_14` (`elif 400 <= e2 <= 499:` — also lost `e2.code`).

### D4 — `del e2` as-var cleanup leaked into handler body

**Location:** line 173 (`del e2` inside `if not e2.response:` body).

The CPython 3.11+ as-var cleanup (`LOAD_CONST None / STORE_FAST e2 / DELETE_FAST e2`) leaks as
a `del e2` statement when the cleanup is followed by a fall-through (no immediate
RETURN_VALUE/RERAISE in the same block). Confirmed in `repro_06_14` (`del e2` after the
return-Expr).

### D5 — Orphan attribute expression leaks as Expr

**Locations:** line 247 (`prod`), line 456 (`stocks`), line 500 (`panel.items`), line 546
(`datass_list[-count:]`), line 557 (`numpy.nan`), line 558 (`stock_df.ix[...]['money'].sum()`).

A `LOAD_FAST`/`LOAD_ATTR`/`LOAD_SUBSCR` whose result is discarded (no following
`STORE`/`CALL`/`RETURN`) leaks as an orphan `Expr` statement. The minimal repros are sensitive
to surrounding context — `repro_06_04` and `repro_06_13` instead lose the *preceding*
assignment, indicating the defect is intertwined with statement-boundary detection rather
than a clean suppression issue.

### D6 — Lost function body / nested-if return (R4 deferred Fix 3 coverage gap)

**Locations:** lines 266-279 (8 consecutive `elif i == 0: pass` whose `index.append(...)`
bodies are lost), line 302 (`def fill_minute_or_day_blank(...): pass` — entire body lost),
lines 492/505 (`pass` for non-trivial bodies), line 566 (`if typet == 7: pass` — return
lost). Confirmed in `repro_06_06` (`is_same_type`: `return True`/`return False` lost → `pass`,
`elif typet == 9:` body truncated).

### D7 — Malformed ternary chain (line 359)

```python
suffix == 'T.CCFX' if typet == 2 else suffix == 'T.CCFX' if typet == 3 else ...
```

A series of `if/elif` assignments is reduced to a nested ternary of `==` comparisons
(should be `=` assignments). Not reproduced minimally — depends on the specific control
flow.

### D8 — Lost statement in `date_convert` (line 2165)

```python
def date_convert(date, report_types):
    int(month_temp == 1 if report_types is None else month_temp <= report_types)
```

`month_temp` is undefined; the function body is reduced to a bare `int(...)` Expr with a
ternary that has no source analogue.

## Minimal repros created (15)

`/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_06/test_engineer/minimal_repros/`:

| Repro | Defect | Exhibits |
|-------|--------|----------|
| repro_06_01_except_return_lost.py | D1 lost return in except | ✅ `({...}, {})` bare Expr |
| repro_06_02_binop_compare_parens.py | D2 lost parens | ✅ `a >= b & c <= d` |
| repro_06_03_bare_num_if.py | D3 bare num if | ❌ (simple compare preserved) |
| repro_06_04_bare_name_expr.py | D5 orphan Name | ❌ (preceding assign lost) |
| repro_06_05_duplicate_stmts.py | duplicate stmts | ❌ (not reproduced) |
| repro_06_06_lost_function_body.py | D6 lost body/return | ✅ `pass` instead of return |
| repro_06_07_orphan_attr_expr.py | D5 orphan Attr | ❌ (attr + assign lost) |
| repro_06_08_boolop_precedence.py | boolop parens | ❌ (parens preserved) |
| repro_06_09_del_asvar_leak.py | D4 del e leak | ❌ (cleanup filtered) |
| repro_06_10_lost_compare_in_or.py | compare in or | ❌ (preserved) |
| repro_06_11_chained_compare_lost.py | D3 chained compare | ❌ (preserved in isolation) |
| repro_06_12_del_asvar_in_handler.py | D4 del e leak | ❌ (cleanup filtered) |
| repro_06_13_orphan_attr_expr.py | D5 orphan Attr | ❌ (attr lost, not orphan) |
| repro_06_14_except_if_return_lost.py | D1+D3+D4 combo | ✅ bare Expr + del e2 + chained cmp lost |
| repro_06_15_nested_if_return_lost.py | D1 ternary return | ✅ bare ternary Expr |

**Confirmed exhibiting:** 01, 02, 06, 14, 15 (5 repros).

## Fix priority for Phase 2

1. **D1 lost return in except** — clearest root cause (bool-overload override of
   `_find_return_through_cleanup_chain`); 3 repros (01, 14, 15) + 4 sites in quotation.pyc.
2. **D2 lost parens in BinOp+Compare** — clean AST-precedence fix; 1 repro (02).
3. D3-D6 — context-sensitive; attempt only if D1+D2 leave baseline green.

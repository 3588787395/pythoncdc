# Round 5 Test Engineer — Decompile Report

- **Decompiler under test:** `python pycdc.py <file.pyc>` (HEAD = d79e744, R1–R4 applied)
- **Target:** `/workspace/quotation.pyc` (Python 3.11)
- **Decompiled output:** 2677 lines, `COMPILE_OK`, 0 warnings (`/tmp/r5_decompiled.py`, copy at `/workspace/r5_decompiled.py`)
- **Repro dir:** `/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_05/test_engineer/minimal_repros/`
- **Repros created:** 14 (all compile with `py_compile` and decompile cleanly; each exhibits the listed defect)

> Note: R1–R4 reduced the *warning count* to 0, but the decompiled text still contains many semantic defects (lost statements, lost branches, spurious else, lost assignments). These are invisible to the warning pass because they produce syntactically valid Python. The repros below isolate each defect class.

---

## 1. Defect inventory (function, line, description, bytecode pattern)

| # | Function (quotation.pyc) | Line(s) | Defect | Bytecode / AST pattern |
|---|--------------------------|---------|--------|-------------------------|
| D1 | `api_get_financial` | 163–169 | Except-handler `if e2.code == 499:` Compare lost → `if 499: pass`; preceding `system_log(<ternary>)` Call wrapping lost / statement lost; handler `return (tuple,)` lost | `COMPARE_OP` result dropped in handler body; `CALL` wrapping ternary arg discarded; `RETURN_VALUE` dropped |
| D2 | `api_get_financial` | 161, 169, 179, 184 | `return ({'error_no':..}, {})` → bare `({'error_no':..}, {})` (return keyword lost) in 4 except handlers | `RETURN_VALUE` stripped; tuple Expr left as statement |
| D3 | `load_get_price` | 506, 513 | `panel[stock] = data` → bare `stock` (STORE_SUBSCR lost) in both `fq=='pre'` and `fq=='post'` loops | `STORE_SUBSCR` not emitted; `LOAD_NAME stock` left as ExprStmt |
| D4 | `load_get_price` | 509–515 | `panel.items` bare Expr + duplicated `exrights_data = ...` + spurious `else: pass` after for | lost `FOR_ITER` target / duplicated `STORE_FAST`; `ELSE` region mis-attached |
| D5 | `one_prod_to_dataframe` | 246–249, 284–291 | Spurious for-else: `prod = data.get(prod_code)` and `columns = []`/`for item in fields:` wrongly attached as `else:` of preceding for | post-loop sequential statements merged into `else` block of `FOR` region |
| D6 | `one_prod_to_dataframe` | 251–252, 270–282 | Duplicated `i = 0`; 7× `elif i == 0: pass` (lost `index.append(...)` body) | `CALL`/`STORE_SUBSCR` body of elif branches dropped → `pass` |
| D7 | `fill_minute_or_day_blank` | 305–306 | Entire function body → `pass` (lost for+if+nested body) | function `Code` body not generated; only `pass` emitted |
| D8 | `change_his_to_forward` | 628–635 | Truncation after else: `tmpstartindex` referenced but never assigned; `elif ...: pass` body lost; spurious `else: tmpdata = tmpdata.append(...)` after for | post-else sequential `STORE_FAST tmpstartindex` lost; `else` of for mis-attached |
| D9 | `change_his_to_forward` / `change_his_to_backward` | 642, 647, 655, 729 | `elif list(...): pass`; `tmpdata = tmpdata` / `tmp = tmp` self-assignment; `if len(...): pass` | branch body dropped; `STORE_FAST` target = same name (lost RHS) |
| D10 | `_is_same_type_date` | 583–584 | `if typet == 7: pass` (inner `if len(day1) == 8: ...` lost) | nested `if` body in first elif branch dropped → `pass` |
| D11 | `load_get_index_stocks` / `load_get_industry_stocks` | 789–796, 803–810 | Duplicated `stockslist = []`, bare `stocks` Name, spurious for-else `return data.sort(...)` | `STORE_FAST` duplicated; `LOAD_NAME` left as Expr; `else` of for mis-attached |
| D12 | `load_get_exrights` (inner `choose_data_from_dict`) | 763–766 | `for stock in stocks: stock` (lost `retdata[stock] = ...`); spurious for-else `return retdata` | `STORE_SUBSCR` lost → bare Name; `else` of for mis-attached |
| D13 | `load_get_exrights` | 770 | `isinstance(stocks, str) if os.path.exists(...) else isinstance(stocks, str)` — degenerate ternary, both branches identical; `exrightdict` referenced undefined | if/else mis-folded into ternary with identical branches; `LOAD_NAME exrightdict` left but def lost |
| D14 | `get_holiday_online` | 221–225 | `if load_count > 5: pass else: holiday.extend(...); raise ValueError(...)` — `raise` misplaced outside if; `if` body lost | `RAISE_VARARGS` moved out of branch; `pass` substituted |
| D15 | `get_kline`-area `fill_*` | 352–354 | Spurious for-else: `if typet == 5 or typet == 1: pass` wrongly attached as `else:` of `for item in all_days` | post-loop `if` merged into `else` of `FOR`; `if` body → `pass` |
| D16 | `get_history` | 873 | `nd_array = FREQUENCYNAME_DICT(query_date is None if frequency in OVER_WEEK_FREQUENCY else query_date is None)` — degenerate ternary, both branches identical; `.get()` lost | if/else mis-folded into ternary; method `CALL` → bare name `FREQUENCYNAME_DICT(...)` |
| D17 | `get_date_and_count` | 898–924, 957–982 | Spurious while-else ×3: `if month in (10,11,12): start_date = ...` wrongly attached as `else:` of `while`; `start_date` overwritten by trailing sequential assignment | post-while `if` merged into `else` of `WHILE` region |
| D18 | `get_fundamentals` / `valuation_new` | 1123–1128, 1617–1622 | 4-branch elif chain collapses to nested `if` with 4× `elif ...: pass` (branch bodies lost) | `STORE_SUBSCR params[...]` bodies of elif branches dropped → `pass` |
| D19 | `get_str_data` | 546, 560, 562–575 | `j = (i := 0)` walrus artifact; `datass_list[-count:]` bare Expr; duplicated `is_all_nan=…/not_nan_icount=0/data_is_nan=0`; bare ternary `numpy.nan if … else …sum()`; bare `numpy.nan`; bare `stock_df.ix[...].sum()`; bare `stock` | `STORE_SUBSCR`/`STORE_FAST` targets lost → bare Expr; `:=` from `while` init |
| D20 | `get_stock_exrights` | 2302–2310 | `if exrights.empty: pass` (was `return exrights`); `exrights.rename(...)` Call lost; nested `if date is None:` promoted to `elif` | `RETURN_VALUE` in if-branch dropped → `pass`; `CALL` statement in else dropped |
| D21 | `get_opt_objects` / `get_opt_last_dates` / `get_opt_contracts` | 2450, 2460, 2470 | `elif len(date) != 8 and len(date) != 10: pass` (×3, lost `raise`/`return`) | `RAISE_VARARGS` body of elif dropped → `pass` |
| D22 | `change_his_to_backward` / `get_str_data` | 519, 858 | `(idx >= nowstart) & (idx <= nowend)` → `idx >= nowstart & idx <= nowend` (parens lost, precedence broken); `datetime.now() + qdt.timedelta(-1).strftime(...)` (parens lost) | `BINARY_OP &` emitted without parens around `COMPARE_OP` operands |
| D23 | `valuation_new` | 1022–1029 | `data` bare Name + duplicated `data_out = []`; spurious for-else `returnDf = pandas.DataFrame(...)` | `STORE_FAST` duplicated; `LOAD_NAME` bare Expr; `else` of for mis-attached |
| D24 | `get_valuation_info` | 1889–1890 | `case _: pass` (lost body); spurious for-else after nested for: `error_return, data_return = valuation_new(...)` mis-attached | `MATCH` wildcard case body dropped; post-for statements merged into `else` |

**Defect totals observed in quotation.pyc:** ~24 distinct defect sites across 17 functions, grouped into 14 defect classes.

---

## 2. Minimal repros → defect mapping

| Repro file | Reproduces | Verified output (key lines) |
|------------|------------|------------------------------|
| `repro_05_01_except_if_cond_lost.py` | D1 — except-handler `if e2.code==499:` block lost + `log(ternary)` Call lost | `request_times <= 2 if e2.code == 401 else e2.code == 599` (bare); `if e2.code == 499:` block + final return gone |
| `repro_05_02_loop_store_subscr_lost.py` | D3 + D4 + D11 — `panel[stock]=data` → bare `stock`; dup `exrights_data=...`; spurious `else: return panel` | `data = change_forward(...); stock` (×2); `panel.items` bare; spurious `else: return panel`; top-level `return panel` lost |
| `repro_05_03_spurious_for_else.py` | D5 + D6 — spurious for-else + bare Name + dup | `for item in fields: ... else: prod = data.get(prod_code); prod`; `for item in prod: item; else: return df` |
| `repro_05_04_func_body_to_pass.py` | D7 (same source) — `or`-boolop condition inverted, lost assignment, lost parens, spurious for-else | `if klines is not None:` (inverted); `stocks` bare; `filled = filled[idx >= nowstart & idx <= nowend]`; `else: return klines` |
| `repro_05_05_func_body_trunc_after_else.py` | D8 (same source) — post-else seq stmts copied into else + duplicated + spurious for-else | `else: ...; tmpstartindex=...; list(...)`; duplicated `preindex=None; tmpstartindex=...`; `for n in ...: ... else: return tmpdata` |
| `repro_05_06_nested_if_inner_lost.py` | D10 — nested if with `and/or` boolop flattened into outer condition (precedence lost) + `and`-branch body → `pass` | `if typet == 7 and len(day1) == 8 or len(day1) == 10:`; `if typet == 8: pass` |
| `repro_05_07_lost_return_keyword.py` | D2 — `return (tuple,)` → bare `(tuple,)` in 3 except handlers | `({'error_no': error_no, 'error_info': error_info}, {})` ×3 (no `return`) |
| `repro_05_08_spurious_while_else.py` | D17 — spurious while-else + trailing assignment detached | `while count > 0: ... else: if month in (10,11,12): start_date = ...`; `start_date = str(year)+'0'+...` detached |
| `repro_05_09_elif_chain_body_to_pass.py` | D18 — 4-branch elif chain → nested if with 4× `elif ...: pass` | `elif start_year is None: pass` / `elif start_year is not None: pass` / `elif start_year == None and end_year == None: pass` |
| `repro_05_10_bare_ternary_lost_assign.py` | D19 — loop-body assignment target lost (`data_is_nan=...` lost) + `result[datas]=...` → bare `result` + spurious for-else | `vol = numpy_nan if data_is_nan == 1 else ...` (data_is_nan undefined); `result`; `else: return result` |
| `repro_05_11_if_branch_body_to_pass.py` | D20 — else-block first `Call` statement lost + nested if promoted to elif | `if exrights.empty: return exrights; elif date is None: return exrights` (rename() lost) |
| `repro_05_12_lost_parens_binop_compare.py` | D22 — `(a >= b) & (c <= d)` → `a >= b & c <= d` (parens lost) | `mask = idx >= nowstart & idx <= nowend` |
| `repro_05_13_dup_stmt_bare_name_for_else.py` | D11 — dup `stockslist=[]`, bare `stocks`, spurious for-else | `stockslist = []; stocks; stockslist = []; for s in stocks: ...; else: data = list(set(...)); return data.sort(...)` |
| `repro_05_14_lost_call_wrapping_ternary.py` | D1 (variant) — `log(ternary)` statement lost + `return` keyword lost | `except HTTPError as e2: error_no = e2.code; ({'error_no': error_no}, None)` (log() + return gone) |

All 14 repros verified: `py_compile` succeeds; `pycdc` exits 0; each output contains the listed defect.

---

## 3. Root-cause hypotheses (by responsible region method)

Hypotheses are stated against `core/cfg/region_analyzer.py` (`_identify_*_regions`) and `core/cfg/region_ast_generator.py` (`_generate_*`). These are **not** fixes — only likely responsible code paths for the fix engineer to investigate.

| Defect class | Likely responsible method(s) | Hypothesis |
|---|---|---|
| Spurious for-else / while-else (D5, D8, D11, D12, D15, D17, D23, D24) | `_identify_loop_regions` (region_analyzer.py:2691) + `_generate_loop` (region_ast_generator.py:2731) | The loop region's `else` exit is being populated with **post-loop sequential statements** that fall through after `FOR_ITER` exhaustion. The region boundary for the `else` clause is too greedy: it consumes trailing fall-through basic blocks instead of stopping at the loop's natural exit. A `break`-free loop should not absorb following statements into `else`. |
| Branch body → `pass` (D6, D9, D10, D14, D18, D20, D21, D24) | `_identify_conditional_regions` (region_analyzer.py:10415) + `_generate_if` (region_ast_generator.py:6668) + `_generate_block_statements` (region_ast_generator.py:25890) | When an `if`/`elif` branch body ends in `RETURN_VALUE`/`RAISE_VARARGS` (no fall-through) **or** the branch contains a nested boolop/ternary region, the branch's statement list is emitted empty and backfilled with `pass`. The branch-body generator is dropping instructions between the conditional jump and the branch exit. The `and`/`or` boolop region overlay (`_identify_boolop_regions`, region_analyzer.py:14358) appears to **steal** the Compare/body instructions of the surrounding `if`. |
| STORE_SUBSCR / assignment target lost → bare Name Expr (D3, D11, D12, D19, D23) | `_generate_block_statements` (region_ast_generator.py:25890) + `_generate_stmts_from_instrs` (region_ast_generator.py:28368) | A trailing `STORE_SUBSCR`/`STORE_FAST` whose value was produced by a `CALL` (or consumed by a following region) is not matched back to its producer; the producer `CALL` becomes an ExprStmt and the `STORE_SUBSCR` is dropped, leaving the bare store-target Name as an ExprStmt. Worse inside loops where the loop variable is reused as the store target (`panel[stock] = …` → `stock`). |
| `return` keyword lost → bare tuple Expr (D2, D14-variant) | `_generate_return_ast` (region_ast_generator.py:29443) + `_generate_handler_body_statements` (region_ast_generator.py:13963) | Inside `except` handler bodies, `RETURN_VALUE` whose operand is a tuple/dict literal is not recognised as a return; the operand Expr is emitted as a bare statement. Suggests `_generate_handler_body_statements` bypasses `_generate_return_ast` for the terminal instruction, or the `RETURN_VALUE` is treated as cleanup (`del e`) rather than a real return. |
| Except-handler `if e2.code == N:` Compare lost (D1) | `_generate_handler_body_statements` (region_ast_generator.py:13963) + `_identify_ternary_regions` (region_analyzer.py:12108) | A ternary-in-call-arg Compare (`system_log(t if e2.code==401 else e2.code==599)`) immediately preceding an `if e2.code == N:` causes the ternary region detector to **absorb** the following `if`'s `COMPARE_OP` into the ternary's operand pool. The `if` is then left with a bare constant (`499`) or an empty body. The two regions overlap in the same basic blocks and are not disjoint. |
| Nested if with boolop flattened into outer condition (D10-repro) | `_identify_boolop_regions` (region_analyzer.py:14358) + `_generate_if` (region_ast_generator.py:6668) | `if T: if A or B: …` is being linearised into `if T and A or B: …`. The boolop region for `A or B` is being merged with the outer `T` Compare without inserting parentheses / preserving the nested `if` boundary. Precedence is lost (`T and A or B` ≠ `T and (A or B)`). |
| Lost parens around `(compare) & (compare)` (D22) | `_identify_chained_compare_regions` (region_analyzer.py:10121) + `_identify_boolop_regions` (region_analyzer.py:14358) | A `BINARY_OP &` whose operands are `COMPARE_OP` results does not re-insert parentheses on emission. The AST generator prints `a >= b & c <= d` instead of `(a >= b) & (c <= d)`. Needs parenthesisation whenever a `Compare` is an operand of a lower-precedence `BinOp`. |
| Degenerate ternary (both branches identical) (D13, D16) | `_identify_ternary_regions` (region_analyzer.py:12108) + `_generate_ternary` (region_ast_generator.py:19131) | An `if/elif` (or `if/else` with `STORE` to same target) is being matched as a `TernaryRegion` even when the two arms produce **different** RHS. The body expressions get normalised to the same textual form (e.g. both arms reduced to `isinstance(stocks, str)` / `query_date is None`), losing the real branch difference. Likely an over-eager store-target match in `_identify_ternary_regions`. |
| Function body → `pass` (D7) | `_generate_region` (region_ast_generator.py:1972) + `_generate_basic_region` (region_ast_generator.py:25817) | For a function whose body is a single complex region tree (`for`+`if`+boolop+nested assign), the top-level region generator returns an empty statement list and the emitter backfills `pass`. The region tree is built but its statements are not lowered — consistent with D6/D10 affecting the *entire* body rather than one branch. |
| Duplicated statements after else (D4, D5, D8, D19, D23) | `_generate_if` (region_ast_generator.py:6668) + `_generate_block_statements` (region_ast_generator.py:25890) | Post-`else` fall-through basic blocks are emitted **both** inside the `else` body **and** as trailing sequential statements (double emission). Indicates the `else` region and the post-if sequential region share basic-block ownership and neither deduplicates. |

---

## 4. Top 3 most impactful defects (by frequency in quotation.pyc)

1. **Spurious for/while-else** (D5, D8, D11, D12, D15, D17, D23, D24) — ~15+ instances across `one_prod_to_dataframe`, `load_get_price`, `load_get_*_stocks`, `change_his_to_forward`, `get_exrights_data`, `get_kline`-area, `get_date_and_count` (×3 while-else), `valuation_new`, `get_valuation_info`. This is the single most frequent defect and silently corrupts control flow by moving sequential code into unreachable `else` clauses. Repros: 02, 03, 05, 08, 13 (+ 04, 10, 14 indirectly).

2. **Branch body → `pass`** (D6, D9, D10, D14, D18, D20, D21, D24) — ~24 `pass` sites in quotation.pyc, of which ~20 are real body losses (the rest are legitimate empty excepts). Concentrated in `one_prod_to_dataframe` (7×), `get_fundamentals`/`valuation_new` (8×), `get_opt_*` (3×), `_is_same_type_date`, `get_stock_exrights`, `change_his_to_*`. Each loses a real `index.append` / `raise` / `return` / assignment. Repros: 04, 06, 09, 11.

3. **STORE_SUBSCR / assignment target lost → bare Name Expr** (D3, D11, D12, D19, D23) — ~10+ instances: `load_get_price` (`stock` ×2), `get_str_data` (`stock`, `datass_list[-count:]`, `stock_df.ix[...].sum()`, `numpy.nan`), `load_get_index_stocks`/`load_get_industry_stocks` (`stocks`), `choose_data_from_dict` (`stock`), `valuation_new` (`data`). Each loses a real assignment, leaving the store target as a useless bare expression. Repros: 02, 10, 13.

Honourable mentions: **lost `return` keyword** (D2, 4 instances in `api_get_financial`), **lost parens / precedence** (D22, ≥2 instances, breaks `&` chains and `+ timedelta().strftime()`), **degenerate ternary** (D13, D16, 2 instances, makes both branches identical).

---

## 5. Notes for the fix engineer

- All 14 repros are **minimal** (5–30 lines) and **self-contained at the bytecode level**: they compile with `py_compile` (undefined names are fine — `py_compile` does not resolve them) and reproduce on the current HEAD without touching `core/cfg/`. Use them as regression cases.
- The 0-warning status is misleading: every defect here produces syntactically valid Python, so the warning pass does not flag them. A semantic / dataflow check (undefined-name use, unreachable-else, `pass` in non-empty branch) would catch most.
- The strongest single lever is **`_identify_loop_regions` / `_generate_loop`**: fixing the spurious for/while-else alone would resolve ~15+ sites and 6 of the 14 repros (02, 03, 05, 08, 13, and partially 04/10).
- The D1 (except-handler Compare loss) and D10 (nested-if boolop flatten) defects both point at **`_identify_boolop_regions` / `_identify_ternary_regions`** stealing instructions from sibling `if` regions — the region disjointness invariant looks violated when a boolop/ternary region and an `if` region share basic blocks.

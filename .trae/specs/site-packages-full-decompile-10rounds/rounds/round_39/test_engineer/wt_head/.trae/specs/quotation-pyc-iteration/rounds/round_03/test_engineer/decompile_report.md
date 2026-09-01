# Round 3 测试工程师报告（decompile_report.md）

> 目标文件：`/workspace/quotation.pyc`
> 测试工程师产物路径：`rounds/round_03/test_engineer/`
> 反编译依据：R2 修复后代码（`core/cfg/*` 当前 HEAD 状态，禁止修改 core/ 源码）
> 字节码基线：`baseline/original_bytecode.txt`（150 code objects）
> 关联文档：`rounds/round_02/test_engineer/decompile_report.md` + `rounds/round_02/repair_engineer/fix_report.md`

## 0. 总体结论

| 指标 | R2 基线（fix_report.md §0） | Round 3 测试复测 | 变化 |
|------|-----------------------------|------------------|------|
| 反编译产物总行数 | 2544 | 2547 | +3 |
| stderr 警告数 | 0 | **0** | 持平 ✓ |
| 编译验证 | COMPILE_OK（孤儿 try 修复后） | **COMPILE_OK** ✓ | 持平 |
| code objects 总数 | 146（基线 150，缺失 4） | **146**（缺失 4） | 持平（未恢复） |
| 字节码不一致函数数 | 81 | **81** | 持平 |
| 签名不匹配函数数 | 70（R2 fix_report §0 记录） | **41** | -29（签名路径已部分修复） |
| 缺失 code objects | 4（1 listcomp + 3 lambda） | **4**（同 R2） | 持平 |
| 截断函数（>50% loss） | 18 | **18** | 持平 |
| R2 已声称修复点（repro_13/14/15/02/16 + 孤儿 try） | 6 项 | **5 项复现通过 / 1 项复测仍存在** | repro_14 在 quotation.pyc 仍截断 |
| 反模式前缀方法新增 | 0 | **0** | G3 持平 ✓ |

### 0.1 重点验证结论（用户指定）

| repro | R2 fix_report 声称状态 | R3 实测结论 | 证据 |
|-------|-------------------------|-------------|------|
| **repro_10**（if 块泄漏为下一函数 `@((...))` 装饰器） | 「`@((...))` 已消失；`and query_date is None` 残留」 | **`@((...))` 装饰器泄漏已修复 ✓**；条件残留仍属 repro_06 范畴 | `grep -c '@(' /tmp/r3_decompiled.py` = **0**；全文件无 `@((...))` 形态 |
| **repro_04**（file 赋值丢失 + STORE_SUBSCR 退化） | 「get_market_detail 内 `file = '...' % finance_mic` 赋值仍缺失（属 repro_04/08 同源）」 | **缺陷仍存在 ✗**（line 1994-2010 反编译产物中 `file` 未定义即被 `with open(file, ...)` 引用） | `def get_market_detail` 函数体 try 块前缺 `file = '...' % finance_mic` 整段赋值 |

### 0.2 R2「已修复」声明复测：repro_14 在 quotation.pyc 仍截断（**重大发现**）

R2 fix_report §0.1 与 Fix 02 (repro_14, P0) 声称「9 个财务函数体不再截断 ✓」。R3 实测：**该修复仅对简化版 minimal repro 生效，对实际 quotation.pyc 中的 9 个财务函数仍截断**。

证据（`/tmp/r3_summary.txt` 截断清单前 9 项均为 R2 声称已修复的财务函数）：
```
get_balance_statement:       orig=469 new=64  (loss=405)   ← R2 声称已修复，R3 实测仍截断
get_cashflow_statement:      orig=461 new=64  (loss=397)   ← 同上
get_income_statement:        orig=461 new=64  (loss=397)   ← 同上
get_cash_collection_ability: orig=458 new=64  (loss=394)   ← 同上
get_debt_paying_ability:     orig=458 new=64  (loss=394)   ← 同上
get_eps:                     orig=458 new=64  (loss=394)   ← 同上
get_growth_ability:          orig=458 new=64  (loss=394)   ← 同上
get_operating_ability:       orig=458 new=64  (loss=394)   ← 同上
get_profit_ability:          orig=458 new=64  (loss=394)   ← 同上
```

`/tmp/r3_decompiled.py` line 1552-1564 实际反编译产物（get_balance_statement）：
```python
def get_balance_statement(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None, merge_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
# ← 函数体在 elif 后整段截断，无后续 for/return/except 等指令
```

**根因初判**：R2 在 `_identify_conditional_regions` / `_build_elif_region` 的修复（扩展 `_structural_region_entries` 含 setup/header/body）对 minimal repro 的简化 CFG 生效，但 quotation.pyc 实际 CFG 中 elif 链后跟随更复杂的嵌套（for + try + return + 多层 if），ipdom 链遍历在更深层级仍误判 merge 点，把后续语句吸收为不可达子区域。

**违反的算法原则**：自底向上归约（elif 归约后 fall-through 应作为函数体顺序子节点保留）+ 每块唯一归属。

---

## 1. 反编译产物概览

### 1.1 反编译执行
- 命令：`python pycdc.py /workspace/quotation.pyc`
- 产物：`/tmp/r3_decompiled.py`（2547 行）
- stderr：0 行（`MatchSingleton` 警告维持 R2 清零状态）
- 编译验证：`python3 -c "compile(open('/tmp/r3_decompiled.py').read(), 'r3', 'exec')"` → **COMPILE_OK** ✓

### 1.2 与 R2 基线对比
- 总行数：2544 → 2547（+3 行，主要来自 check_stocks 等函数 elif 分支的细微展开）
- 编译状态：COMPILE_OK → COMPILE_OK（持续通过）
- stderr 警告数：0 → 0（持续清零）

---

## 2. 字节码 diff 分析

### 2.1 diff 工具与产物
- diff 脚本：`/tmp/r3_diff.py`（基于 R2 `r2_diff.py` 演进，对照 `baseline/original_bytecode.txt` 与 R3 反编译产物重编后的 dis 输出）
- 详细 diff：`/tmp/r3_diff_detail.txt`（81 函数指令级不一致，~380KB）
- 摘要：`/tmp/r3_summary.txt`

### 2.2 总体统计（vs R2 基线）

| 指标 | R2 基线 | R3 实测 | 变化 |
|------|---------|---------|------|
| orig code objects | 150 | 150 | — |
| new code objects | 146 | 146 | — |
| missing in new | 4 | 4 | — |
| extra in new | 0 | 0 | — |
| common | 146 | 146 | — |
| signature mismatches | 70 | **41** | **-29**（签名路径改善） |
| instruction mismatches | 81 | **81** | 持平 |
| 截断函数（>50% loss） | 18 | 18 | 持平 |
| 扩展函数（instr gain） | 8 | 8 | 持平 |

### 2.3 缺失 code objects（4，全部为 lambda/listcomp）

| 缺失 code object | 所属函数 | 类型 |
|------------------|----------|------|
| `build_future_fill_time.<listcomp>` | build_future_fill_time | LISTCOMP |
| `get_fundamentals_daily_info.<lambda>` | get_fundamentals_daily_info | LAMBDA |
| `get_valuation_info.<lambda>` | get_valuation_info | LAMBDA |
| `get_valuation_new_info.<lambda>` | get_valuation_new_info | LAMBDA |

> **新发现的 R3 缺陷模式**：`get_valuation_info` / `get_valuation_new_info` 在 R3 反编译产物中只剩 21 条指令（orig=121），函数体被截断到只剩外层 if/elif，内层含 lambda 表达式 + return 的整段丢失，导致 3 个 lambda code objects 在 R3 产物中缺失。

### 2.4 截断函数清单（>50% 指令损失，18 项）

按损失指令数排序：

| 函数 | orig | new | loss | 关联缺陷 |
|------|------|-----|------|----------|
| change_his_to_forward | 597 | 239 | 358 | R3-04/08（loop body 赋值丢失） |
| load_bars_from_hundsun | 504 | 250 | 254 | R3-08（loop bare Name + 重复） |
| get_balance_statement | 469 | 64 | 405 | **R3-14（elif 链后函数体截断）** |
| get_cashflow_statement | 461 | 64 | 397 | R3-14 |
| get_income_statement | 461 | 64 | 397 | R3-14 |
| get_cash_collection_ability | 458 | 64 | 394 | R3-14 |
| get_debt_paying_ability | 458 | 64 | 394 | R3-14 |
| get_eps | 458 | 64 | 394 | R3-14 |
| get_growth_ability | 458 | 64 | 394 | R3-14 |
| get_operating_ability | 458 | 64 | 394 | R3-14 |
| get_profit_ability | 458 | 64 | 394 | R3-14 |
| get_price | 202 | 50 | 152 | R3-14 + R3-12 |
| api_get | 137 | 37 | 100 | R3-14（elif 后截断） |
| get_fundamentals_daily_info | 121 | 21 | 100 | R3-14 + lambda 丢失 |
| get_valuation_info | 121 | 21 | 100 | R3-12 + R3-14 + lambda 丢失 |
| get_valuation_new_info | 121 | 21 | 100 | R3-12 + R3-14 + lambda 丢失 |
| _is_same_type_date | 99 | 9 | 90 | R3-14 |
| change_future_real_date | 98 | 42 | 56 | R3-09（spurious for-else） |

**结论**：18 个截断函数中，11 个为 R3-14 elif 链截断（含 R2 声称已修复的 9 个财务函数），4 个为 R3-12 嵌套 if 丢失 + 截断，2 个为 R3-04/08 loop 赋值丢失，1 个为 R3-09 spurious for-else。

### 2.5 扩展函数清单（指令增加，8 项）

| 函数 | orig | new | gain | 备注 |
|------|------|-----|------|------|
| one_prod_to_dataframe | 452 | 469 | +17 | for-else 多展开 + spurious 重复语句 |
| check_frequency | 96 | 101 | +5 | 6 路 BoolOp `and` 翻转（repro_15 quotation.pyc 仍复现） |
| get_cb_calender_info | 383 | 387 | +4 | for-else 误展开 |
| load_get_index_stocks | 63 | 67 | +4 | spurious for-else |
| load_get_industry_stocks | 61 | 65 | +4 | spurious for-else |
| check_stocks | 71 | 73 | +2 | elif 分支 `l` 裸 Name（repro_11） |
| get_index_stocks | 73 | 74 | +1 | spurious for-else |
| get_industries | 61 | 62 | +1 | spurious for-else |

---

## 3. R2 残留缺陷追踪（逐项复测）

### 3.1 R2 已声称修复 — 复测通过（5 项）

| R2 repro | R2 声称 | R3 实测 | 证据 |
|----------|---------|---------|------|
| repro_13（FUNCTION_DEF defaults→装饰器泄漏 `@((...))`） | 完全修复 | ✓ 通过 | 全文件 `@(` 计数=0 |
| repro_15（BoolOp or→and 翻转，**仅 minimal repro**） | 完全修复 | ✓ 通过（minimal repro 路径） | repro_15 minimal 反编译 6 路 `or` 正确 |
| repro_02 + repro_16（IS_OP→`== None`、`not in`→`in`） | 完全修复 | ✓ 通过 | quotation.pyc 中 `is None` + `not in` 正确保留 |
| repro_15 quotation.pyc 路径（**未声明**） | — | **✗ 仍复现** | `check_frequency` 6 路 `and` 翻转（line 1922） |
| 孤儿 try（get_market_detail） | 完全修复 | ✓ 通过 | `compile()` COMPILE_OK |

### 3.2 R2 已声称修复 — 复测仍存在（1 项，重大发现）

| R2 repro | R2 声称 | R3 实测 | 证据 |
|----------|---------|---------|------|
| **repro_14**（elif A and B: 后函数体截断） | 完全修复（9 个财务函数不再截断） | **✗ 仍截断**（9 个财务函数 orig 458~469 → new 64，loss 394~405） | `/tmp/r3_decompiled.py` line 1552-1564 `get_balance_statement` 函数体在 elif 后整段丢失 |

> **详见 §0.2**：R2 修复仅对 minimal repro 生效，对实际 quotation.pyc 中的 elif + 嵌套 for/try/return 复杂场景仍失效。归档为 R3 新增 `repro_03_elif_chain_func_body_truncation.py`。

### 3.3 R2 已记录残留 — R3 仍复现（8 项）

| R2 repro | R2 残留声明 | R3 实测 | 关联 R3 repro |
|----------|-------------|---------|----------------|
| repro_01（case None→case _ + 重复 case _） | 待后续轮次 | ✗ 仍复现（quotation.pyc::process line 1712-1714 `match date: case _:`） | repro_03_match_case_none_to_wildcard.py |
| repro_04（STORE_SUBSCR→变量注解 + spurious break） | 待后续轮次 | ✗ 仍复现（quotation.pyc::get_fundflow_day line 2179-2182 `returninfo[item]: returninfo = ...; break`） | repro_03_loop_store_subscr_to_annotation.py |
| repro_04b（**用户重点验证**：get_market_detail file 赋值丢失） | R2 §9.5 残留 | ✗ 仍复现（quotation.pyc::get_market_detail line 1994-2010 `file` 未定义即被 `with open(file, ...)` 引用） | **repro_03_repro04_file_assignment_lost.py** |
| repro_06（IfExp 实参→and + docstring 体） | 待后续轮次 | ✗ 仍复现（quotation.pyc::get_quote line 87-90 `if quote is None and is_trade: """trade"""`） | repro_03_if_ifexp_arg_to_and_docstring.py |
| repro_07（except handler 内 isinstance 丢失） | 待后续轮次 | ✗ 仍复现（quotation.pyc::api_get_financial line 141-150 `if HTTPError: pass else: if BaseException: pass`） | repro_03_try_except_handler_if_cond_lost.py |
| repro_08（循环体 STORE_FAST var 丢失→裸 Name + 重复） | 待后续轮次 | ✗ 仍复现（quotation.pyc::load_get_price 风格） | repro_03_loop_bare_name_and_dup.py |
| repro_09（双层 spurious for-else + match case 体内 for） | 待后续轮次 | ✗ 仍复现（quotation.pyc::fill_missing_stock_data 双层 for 后 `else:` + `one_prod_to_dataframe` 多处 spurious for-else） | repro_03_loop_spurious_for_else_double.py |
| repro_10（if 块泄漏为下一函数 `@((...))` 装饰器，**用户重点验证**） | 部分修复（`@((...))` 已消失） | **✓ 装饰器泄漏已修复**（`@(` 全文计数=0）；条件残留 `and query_date is None` 属 repro_06 范畴 | 见 §0.1 |
| repro_11（elif 分支首条赋值 RHS 丢失→裸 Name） | 待后续轮次 | ✗ 仍复现（quotation.pyc::check_stocks line 1910-1911 `elif isinstance(l, list) or isinstance(l, tuple): l`） | repro_03_if_elif_bare_name.py |
| repro_12（嵌套 `if A: S; if B:` 内层 if 丢失） | 部分修复（语句提升解除） | ✗ 仍复现（quotation.pyc::get_valuation_info line 2216-2221 内层 if + return 整段丢失，函数 orig=121 → new=21） | repro_03_if_nested_inner_lost.py |

### 3.4 R2 quotation.pyc 路径与 minimal repro 路径修复不一致（**新发现**）

| R2 repro | minimal repro 路径 | quotation.pyc 路径 | 差异说明 |
|----------|---------------------|---------------------|----------|
| repro_14 | ✓ 完全修复（minimal 函数体保留） | **✗ 仍截断**（9 个财务函数 469→64） | minimal CFG 简化（elif + 单一 for），quotation.pyc 实际 CFG 含 elif + 嵌套 for + try + 多 return，修复未覆盖复杂场景 |
| repro_15 | ✓ 完全修复（minimal 6 路 `or`） | **✗ 仍翻转**（`check_frequency` 6 路 `and`） | minimal BoolOp 路径已修，quotation.pyc 路径仍走旧的 `_boolop_expression` 分支 |

**根因初判**：R2 修复在 `_identify_conditional_regions` / `_boolop_expression` 中针对 minimal repro 的简化 CFG 模式生效，但 quotation.pyc 实际 CFG 包含的额外结构（嵌套 for + try + 多 return + 多层 if）触发了未被 minimal repro 覆盖的代码路径，修复未生效。

**违反的算法原则**：每块唯一归属（不同 CFG 形态下区域归约结果不一致，未保证算法通用性）。

---

## 4. R3 新增缺陷清单

### 4.1 R3 新增缺陷模式（在 R2 repro 之外的新发现）

| R3 编号 | 缺陷类型 | 触发位置 | 关联 R3 repro |
|---------|----------|----------|----------------|
| R3-14 | IF/ELIF：elif 链后函数体截断（quotation.pyc 路径，R2 声称已修但实测仍截断） | quotation.pyc::get_balance_statement 等 9 个财务函数 | repro_03_elif_chain_func_body_truncation.py |
| R3-04b | IF/TRY：try 块前 `file = ...` 顺序赋值被 TryExcept 吞并为 setup（R2 §9.5 残留，R3 重点验证） | quotation.pyc::get_market_detail | repro_03_repro04_file_assignment_lost.py |
| R3-15quotation | BOOLOP：`check_frequency` 6 路 `or` 在 quotation.pyc 路径仍翻转为 `and`（R2 minimal 已修，quotation.pyc 未修） | quotation.pyc::check_frequency line 1922 | （沿用 repro_03_if_elif_bare_name.py 同源根因，未单独归档） |

### 4.2 R3 残留缺陷完整清单（10 个 repro 归档）

| R3 repro 文件 | 关联 R2 repro | 触发区域 | 根因初判 |
|----------------|----------------|----------|----------|
| repro_03_match_case_none_to_wildcard.py | repro_01 | MATCH | `pattern_parser.py` / `_generate_match` 未把 `COMPARE_OP is None` 重建为 `MatchSingleton(None)`，回退 `MatchAs(None)`（`case _`），导致 wildcard 重复 SyntaxError |
| repro_03_loop_store_subscr_to_annotation.py | repro_04 | LOOP + STORE_SUBSCR | `_generate_loop` / `_build_effective_stmts` 把 `STORE_SUBSCR`（d[k]=call）误判为 `STORE_ANNOTATION`（PEP 526 变量注解），发射 `d[k]: d = call(...)`；并出现 spurious break |
| repro_03_repro04_file_assignment_lost.py | repro_04b（**R2 §9.5 残留，R3 重点验证**） | IF + TRY | `_generate_try` / `_build_effective_stmts` 在 TryRegion 与外层 IfRegion else 分支挂接时，把 try 入口前的顺序赋值（`file = ... % finance_mic`）误识别为 TryExcept setup 块而吞并 |
| repro_03_if_ifexp_arg_to_and_docstring.py | repro_06 | IF + BOOLOP + TERNARY | `_generate_if` 把 IfExp 求值序列（`is_trade; POP_JUMP_IF_FALSE; 'trade'; JUMP; 'backtest'`）误并入 if 条件 `and is_trade`，IfExp 两支字符串常量被误发射为 docstring |
| repro_03_try_except_handler_if_cond_lost.py | repro_07 | TRY/EXCEPT | `_generate_try` 把 except handler 内 `LOAD_GLOBAL isinstance + LOAD_FAST e + CALL` 完整 Call 节点丢失，只保留 `LOAD_GLOBAL cls` 裸 Name 作 If 条件（`if HTTPError:` 而非 `if isinstance(e2, HTTPError):`） |
| repro_03_loop_bare_name_and_dup.py | repro_08 | LOOP + IF | `_generate_if` / `_generate_loop` / `_build_effective_stmts` 把 `STORE_FAST var` 赋值目标丢失（仅剩 receiver `LOAD_FAST var` 作孤立 Expr），并去重前驱语句失败导致重复 |
| repro_03_loop_spurious_for_else_double.py | repro_09 | LOOP（双层 for + match case 内 for） | `_identify_loop_regions` 的 else 归属判定把循环后顺序语句误识别为 for-else body，双层嵌套 for + match case 内 for 均触发 |
| repro_03_if_elif_bare_name.py | repro_11 | IF/ELIF | `_generate_if` 把 elif 分支首条 `l = l.replace(...)` 的 Call 节点 RHS 丢失，只保留 receiver `LOAD_FAST l` 作孤立 Expr |
| repro_03_if_nested_inner_lost.py | repro_12 | IF（嵌套 if） | `_identify_if_regions` 把外层 if 与内层 if 合并为 `if A and B:`（minimal 形态）；quotation.pyc 路径下内层 if + return 整段丢失（与 repro_14 截断同源） |
| repro_03_elif_chain_func_body_truncation.py | **repro_14（R2 声称已修，实测仍存在）** | IF/ELIF | `_identify_conditional_regions` / `_build_elif_region` 在 quotation.pyc 实际 CFG（elif + 嵌套 for + try + 多 return）下，ipdom 链遍历仍误判 merge 点，把 elif 后续语句吸收为不可达子区域 |

---

## 5. ≥10 最小复现实例清单

10 个最小复现实例已归档至 `rounds/round_03/test_engineer/minimal_repros/`，全部通过 `py_compile` 独立编译验证（OK=10 / FAIL=0）：

| # | 文件名 | 关联缺陷 | 触发区域 | py_compile |
|---|--------|----------|----------|------------|
| 1 | repro_03_match_case_none_to_wildcard.py | R3-01（R2 repro_01 残留） | MATCH | OK ✓ |
| 2 | repro_03_loop_store_subscr_to_annotation.py | R3-04（R2 repro_04 残留） | LOOP + STORE_SUBSCR | OK ✓ |
| 3 | repro_03_repro04_file_assignment_lost.py | R3-04b（**R2 §9.5 残留，R3 重点验证**） | IF + TRY | OK ✓ |
| 4 | repro_03_if_ifexp_arg_to_and_docstring.py | R3-06（R2 repro_06 残留） | IF + BOOLOP + TERNARY | OK ✓ |
| 5 | repro_03_try_except_handler_if_cond_lost.py | R3-07（R2 repro_07 残留） | TRY/EXCEPT | OK ✓ |
| 6 | repro_03_loop_bare_name_and_dup.py | R3-08（R2 repro_08 残留） | LOOP + IF | OK ✓ |
| 7 | repro_03_loop_spurious_for_else_double.py | R3-09（R2 repro_09 残留） | LOOP（双层 for） | OK ✓ |
| 8 | repro_03_if_elif_bare_name.py | R3-11（R2 repro_11 残留） | IF/ELIF | OK ✓ |
| 9 | repro_03_if_nested_inner_lost.py | R3-12（R2 repro_12 残留） | IF（嵌套 if） | OK ✓ |
| 10 | repro_03_elif_chain_func_body_truncation.py | R3-14（**R2 声称已修，实测仍存在**） | IF/ELIF | OK ✓ |

每个 repro 包含：
- 关联 R1/R2 repro 编号 + R3 复现状态
- quotation.pyc 实际触发位置（函数名 + 行号）
- 触发区域类型
- 根因初判（涉及方法 + 4 原则违反项）
- 最小字节码模式（Python 3.11）
- R3 反编译产物（错误）vs 期望产物
- 验证命令（py_compile + pycdc）

---

## 6. 根因初判汇总

### 6.1 涉及的核心方法（按出现频次）

| 方法 | 文件 | 涉及 repro | 4 原则违反项 |
|------|------|------------|---------------|
| `_generate_if` | region_ast_generator.py | R3-06/08/11/12 | 嵌套即抽象节点 + 入口引用语义 |
| `_generate_loop` / `_build_effective_stmts` | region_ast_generator.py | R3-04/04b/08/09 | 自底向上归约 + 每块唯一归属 |
| `_generate_try` | region_ast_generator.py | R3-04b/07 | 每块唯一归属 |
| `_identify_conditional_regions` / `_build_elif_region` | region_analyzer.py | R3-12/14 | 自底向上归约 + 每块唯一归属 |
| `_identify_loop_regions` | region_analyzer.py | R3-09 | 每块唯一归属 |
| `_boolop_expression` | region_ast_generator.py | R3-15quotation | 入口引用语义 |
| `_generate_match` / `pattern_parser.py` | region_ast_generator.py / pattern_parser.py | R3-01 | 嵌套即抽象节点 |

### 6.2 4 原则违反项统计

| 原则 | 违反次数 | 涉及 repro |
|------|----------|------------|
| 自底向上归约 | 4 | R3-04/04b/09/14 |
| 每块唯一归属 | 6 | R3-04/04b/07/08/09/12/14 |
| 嵌套即抽象节点 | 4 | R3-01/06/08/12 |
| 入口引用语义 | 3 | R3-06/11/15quotation |

### 6.3 重大根因发现：minimal repro 与 quotation.pyc 路径修复不一致

R2 修复在以下两个 repro 上仅对 minimal repro 路径生效，对 quotation.pyc 实际路径未生效：

1. **repro_14**（elif 链后函数体截断）：minimal repro 修复 ✓，quotation.pyc 9 个财务函数仍截断 ✗
2. **repro_15**（BoolOp or→and 翻转）：minimal repro 修复 ✓，quotation.pyc::check_frequency 6 路 `and` 仍翻转 ✗

**根因初判**：R2 修复针对 minimal repro 的简化 CFG 模式（单一 elif + 单一 for / 单一 6 路 BoolOp），但 quotation.pyc 实际 CFG 包含的额外结构（嵌套 for + try + 多 return + 多层 if / BoolOp 嵌套在 if 条件中）触发了未被 minimal repro 覆盖的代码路径。

**修复建议**：R3 修复工程师应直接以 quotation.pyc 实际反编译产物为验证目标（不仅依赖 minimal repro），确保修复对 minimal repro 与 quotation.pyc 路径同时生效。

---

## 7. 修复建议优先级（供修复工程师参考）

| 优先级 | R3 repro | 缺陷类型 | 修复建议 | 算法依据 |
|--------|----------|----------|----------|----------|
| **P0**（影响 9 个财务函数 + R2 声称已修但实测未修） | repro_03_elif_chain_func_body_truncation.py | elif 链后函数体截断（quotation.pyc 路径） | 扩展 `_identify_conditional_regions` / `_build_elif_region` 的 ipdom 链遍历，覆盖 elif + 嵌套 for + try + 多 return 复杂场景；以 quotation.pyc::get_balance_statement 为验证目标 | 自底向上归约 + 每块唯一归属 |
| **P0**（R3 重点验证） | repro_03_repro04_file_assignment_lost.py | try 块前顺序赋值被 TryExcept 吞并 | `_generate_try` / `_build_effective_stmts` 区分 try 入口前的顺序赋值（IfRegion.else 兄弟节点）与 TryExcept setup/header（不应吞并顺序赋值） | 自底向上归约 + 每块唯一归属 |
| **P1** | repro_03_match_case_none_to_wildcard.py | case None 塌缩为 case _ + wildcard 重复 SyntaxError | `pattern_parser.py` / `_generate_match` 把 `COMPARE_OP is None` 重建为 `MatchSingleton(None)`，禁止回退 `MatchAs(None)` | 嵌套即抽象节点 |
| **P1** | repro_03_if_nested_inner_lost.py | 嵌套 if 内层丢失 + 函数体截断（与 R3-14 同源） | `_identify_if_regions` 把内层 if 作为外层 If.body 子节点保留，禁止吸收为不可达；与 R3-14 修复联动 | 自底向上归约 + 嵌套即抽象节点 |
| **P1** | repro_03_if_ifexp_arg_to_and_docstring.py | IfExp 实参→and + docstring 体 | `_generate_if` 把 IfExp 作为 Call 实例子节点保留，禁止提升为 if 的 `and` 条件、禁止字符串常量发射为 docstring | 入口引用语义 + 嵌套即抽象节点 |
| **P2** | repro_03_try_except_handler_if_cond_lost.py | except handler 内 isinstance 丢失→裸 `if X:` | `_generate_try` 把 `LOAD_GLOBAL isinstance + LOAD_FAST e + CALL` 作为完整 Call 节点作 If 条件 | 每块唯一归属 |
| **P2** | repro_03_loop_store_subscr_to_annotation.py | STORE_SUBSCR→变量注解 + spurious break | `_generate_loop` 区分 `STORE_SUBSCR`（d[k]=call）与 `STORE_ANNOTATION`（PEP 526）；去除 spurious break | 每块唯一归属 |
| **P2** | repro_03_loop_bare_name_and_dup.py | 循环体赋值目标丢失→裸 Name + 重复 | `_generate_if` / `_generate_loop` 保留 `STORE_FAST var` 赋值目标；`_build_effective_stmts` 去重前驱语句 | 每块唯一归属 |
| **P2** | repro_03_loop_spurious_for_else_double.py | 双层 spurious for-else | `_identify_loop_regions` else 归属须判定 fall-through 块是否仅含循环出口 + 后续顺序语句，覆盖嵌套 for 与 match case 内 for | 每块唯一归属 |
| **P2** | repro_03_if_elif_bare_name.py | elif 分支首条赋值 RHS 丢失→裸 Name | `_generate_if` 保留 `LOAD_FAST l + LOAD_ATTR replace + CALL_METHOD` 的 Call 节点，禁止只保留 receiver `LOAD_FAST l` 作孤立 Expr | 入口引用语义 |

---

## 8. 残留与后续

### 8.1 R3 残留缺陷数（供 R3 修复工程师目标参考）

- 总缺陷类数：10（全部归档为 repro_03_*.py）
  - P0×2（repro_03_elif_chain_func_body_truncation + repro_03_repro04_file_assignment_lost）
  - P1×3（repro_03_match_case_none_to_wildcard + repro_03_if_nested_inner_lost + repro_03_if_ifexp_arg_to_and_docstring）
  - P2×5（repro_03_try_except_handler_if_cond_lost + repro_03_loop_store_subscr_to_annotation + repro_03_loop_bare_name_and_dup + repro_03_loop_spurious_for_else_double + repro_03_if_elif_bare_name）
- 字节码不一致函数数：81（与 R2 持平）
- 签名不匹配函数数：41（较 R2 70 改善 -29，签名路径已部分修复）
- 截断函数（>50% loss）：18（与 R2 持平，含 R2 声称已修但实测仍截断的 9 个财务函数）
- 缺失 code objects：4（1 listcomp + 3 lambda，全部由函数体截断导致）

### 8.2 R3 修复工程师目标

1. **必做 P0**：修复 repro_03_elif_chain_func_body_truncation（quotation.pyc 9 个财务函数 + api_get + get_fundamentals_daily_info + get_valuation_info + get_valuation_new_info + _is_same_type_date 共 14 个截断函数）+ repro_03_repro04_file_assignment_lost（get_market_detail file 赋值恢复）
2. **必做 P1**：修复 repro_03_match_case_none_to_wildcard + repro_03_if_nested_inner_lost + repro_03_if_ifexp_arg_to_and_docstring
3. **建议 P2**：按时间预算择优，至少 2 项
4. **回归要求**：既有测试矩阵 0 退化；R2 已修 5 项 repro（13/14/15/02/16 + 孤儿 try）在 minimal repro 路径不退化；**新增要求：以 quotation.pyc 实际反编译产物为验证目标（不仅依赖 minimal repro）**
5. **目标降幅**：字节码不一致函数数 81 → ≤ 50；截断函数 18 → ≤ 5

### 8.3 R3 验证补充检查点（建议）

- [ ] R3-V1: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] R3-V2: 反模式 grep 验证 0 新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀）
- [ ] R3-V3: quotation.pyc 反编译 stderr 维持 0
- [ ] R3-V4: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
- [ ] R3-V5: quotation.pyc 中 `get_balance_statement` 函数体不再截断（orig=469 → new ≥ 400）
- [ ] R3-V6: quotation.pyc 中 `get_market_detail` 的 `file = ...` 赋值恢复（`grep -c 'file = ' /tmp/r3_decompiled.py` 在 get_market_detail 函数体中 = 1）
- [ ] R3-V7: quotation.pyc 中 `check_frequency` 6 路 BoolOp 在 quotation.pyc 路径恢复为 `or`（不仅 minimal repro）
- [ ] R3-V8: 10 个 R3 repro 全部反编译产物核心缺陷消除

### 8.4 涉及文件清单

| 文件 | 用途 |
|------|------|
| `/workspace/quotation.pyc` | 反编译目标（禁止修改） |
| `/tmp/r3_decompiled.py` | R3 反编译产物（2547 行，COMPILE_OK） |
| `/tmp/r3_diff.py` | 字节码 diff 脚本 |
| `/tmp/r3_diff_detail.txt` | 81 函数指令级不一致详情（~380KB） |
| `/tmp/r3_summary.txt` | diff 摘要（缺失/截断/扩展函数清单） |
| `rounds/round_03/test_engineer/minimal_repros/repro_03_*.py` | 10 个最小复现实例 |
| `rounds/round_03/test_engineer/decompile_report.md` | 本报告 |
| `rounds/round_02/repair_engineer/fix_report.md` | R2 修复报告（验证 R2 声称修复点） |
| `baseline/original_bytecode.txt` | 字节码基线（150 code objects） |

---

## 9. 算法合规性自检（测试工程师侧）

- ✓ 未修改 `/workspace/core/` 任何源码
- ✓ 未修改 `/workspace/quotation.pyc`、baseline、R1/R2 round 目录
- ✓ 未修改任何 spec 文档（spec.md / tasks.md / checklist.md）
- ✓ 只创建指定文件：`rounds/round_03/test_engineer/minimal_repros/repro_03_*.py`（10 个）+ `rounds/round_03/test_engineer/decompile_report.md`（本报告）
- ✓ 所有 RunCommand ≤ 300 秒
- ✓ ≥10 个 repro_*.py（10 个，全部 py_compile 通过）
- ✓ decompile_report.md 包含每项根因初判与 R2 残留追踪
- ✓ 重点验证 repro_10（已修复 ✓）和 repro_04（仍存在 ✗，归档为 repro_03_repro04_file_assignment_lost.py）

---

## 10. 退出条件检查

- [ ] E1: quotation.pyc 反编译字节码不一致数 = 0 — **未达成**（81 个函数不一致）
- [ ] E2: 最近一轮测试工程师可提取的「新增最小复现实例」< 10 个 — **未达成**（R3 提取 10 个，含 1 个重大发现：R2 声称已修的 repro_14 在 quotation.pyc 实测仍截断）

R3 测试工程师阶段完成，移交 R3 修复工程师阶段。

# Round 4 测试工程师报告（decompile_report.md）

> 目标文件：`/workspace/quotation.pyc`
> 测试工程师产物路径：`rounds/round_04/test_engineer/`
> 反编译依据：R3 修复后代码（commit b0173ee `qpyc-r03: 修复 quotation.pyc P0+P1+P2 (7 项 + LOOP/WITH 回归修复)`，禁止修改 core/ 源码）
> 字节码基线：`baseline/original_bytecode.txt`（150 code objects，23195 行）
> 关联文档：`rounds/round_03/test_engineer/decompile_report.md` + `rounds/round_03/repair_engineer/fix_report.md`
> diff 脚本：`/tmp/r4_diff.py`；diff 详情：`/tmp/r4_diff_detail.txt`；摘要：`/tmp/r4_summary.txt`

## 0. 总体结论

| 指标 | R3 基线（R3 fix_report §0） | R4 实测 | 变化 |
|------|-----------------------------|---------|------|
| 反编译产物总行数 | 3035 | **3035** | 持平（R3 已恢复 P0/P1 函数体）|
| stderr 警告数 | 0 | **0** | 持平 ✓ |
| 编译验证 | COMPILE_OK | **COMPILE_OK** ✓ | 持平 |
| code objects 总数 | 146（基线 150，缺失 4） | **146**（缺失 4） | 持平 |
| 字节码不一致函数数 | 81 | **80** | -1 |
| 签名不匹配函数数 | 41 | **37** | **-4**（R3 elif 修复恢复部分 locals）|
| 截断函数（>50% loss） | 18 | **11** | **-7**（9 个财务函数 + api_get + get_price 脱离截断清单）|
| 扩展函数（instr gain） | 8 | **5** | **-3** |
| 反模式前缀方法新增 | 0 | **0** | G3 持平 ✓ |
| R3 已修 7 项是否仍生效 | — | **6 项生效 / 1 项退化** | repro_03_loop_bare_name_and_dup 在 quotation.pyc 实际产物退化 |

### 0.1 重点验证结论（R3 已修 7 项是否仍生效）

| # | repro | R3 优先级 | R3 声称 | R4 实测结论 | 证据 |
|---|-------|-----------|---------|-------------|------|
| 1 | repro_03_elif_chain_func_body_truncation | P0 | ✓ 已修复 | **✓ 仍生效** | get_balance_statement orig=469 new=248（R3 new=64）；9 个财务函数脱离 >50% 截断清单 |
| 2 | repro_03_repro04_file_assignment_lost | P0 | ✓ 已修复 | **✓ 仍生效** | `get_market_detail` 中 `file = '/home/fly/data/market_detail_info/market_detail_%s_info.pickle' % finance_mic` 赋值已恢复（R4 line 1996）|
| 3 | repro_03_match_case_none_to_wildcard | P1 | ✓ 已修复 | **✓ 仍生效** | `case None:` 正确输出 5 处（line 1573/1576/1643/1646/1713），无 `case _:` 误转 |
| 4 | repro_03_if_nested_inner_lost | P1 | ✓ 已修复 | **✓ 仍生效** | `get_price` 含 13 处 `if` 语句，嵌套 if 保留，函数体恢复至 206 条指令（R3 new=50）|
| 5 | repro_03_if_ifexp_arg_to_and_docstring | P1 | ✓ 已修复 | **✓ 仍生效** | `qdt.timedelta(days=...)` 作为 Call 实参保留（line 516/518）；IfExp 未退化为 and 链 |
| 6 | repro_03_if_elif_bare_name | P2 | ✓ 已修复 | **✓ 仍生效** | `check_stocks` elif 分支 `l = l.replace('.XSHE', '.SZ')` Call 节点保留，无裸 `l` Expr，无重复赋值 |
| 7 | repro_03_loop_bare_name_and_dup | P2 | ✓ 已修复（minimal repro） | **✗ 在 quotation.pyc 实际产物退化** | `load_get_price` 循环体出现裸 `stock` Expr（R4 line "stock"），`panel[stock] = data` STORE_SUBSCR 丢失。R3 fix_report 仅基于 minimal repro 验证通过，对 quotation.pyc 实际 CFG 退化 |

### 0.2 R3 残留 3 项 P2 复测

| repro | R3 状态 | R4 实测 | 证据 |
|-------|---------|---------|------|
| repro_03_try_except_handler_if_cond_lost | 未修复 | **✗ 仍存在** | `api_get_financial` 的 `except HTTPError as e2:` handler 内 `if e2.code == 401:` Compare 丢失，被替换为 `if HTTPError: pass` + spurious 嵌套 |
| repro_03_loop_store_subscr_to_annotation | 未修复 | **✗ 仍存在** | `load_get_price` 的 `panel[stock] = data` STORE_SUBSCR 丢失，尾部 `LOAD_FAST stock` 泄漏为裸 Expr |
| repro_03_loop_spurious_for_else_double | 未修复 | **✗ 仍存在** | `one_prod_to_dataframe` 的 `for item in fields: ... else: prod = data.get(prod_code)` spurious for-else，且 `i = 0` 重复 |

---

## 1. 反编译产物概览

### 1.1 反编译执行
- 命令：`python pycdc.py /workspace/quotation.pyc`
- 产物：`/tmp/r4_decompiled.py`（**3035 行**）
- stderr：**0 行**（持续清零）
- 编译验证：`compile()` → **COMPILE_OK** ✓
- 退出码：0

### 1.2 与 R3 基线对比
- 总行数：3035 → 3035（持平，R3 已恢复 P0/P1 函数体，R4 未引入新截断导致的行数变化）
- 编译状态：COMPILE_OK → COMPILE_OK
- stderr：0 → 0

---

## 2. 字节码 diff 分析

### 2.1 diff 工具与产物
- diff 脚本：`/tmp/r4_diff.py`（基于 R3 `r3_diff.py` 演进，对照 `baseline/original_bytecode.txt` 与 R4 反编译产物重编后的 dis 输出）
- 详细 diff：`/tmp/r4_diff_detail.txt`（80 函数指令级不一致）
- 签名 diff：`/tmp/r4_sig_diff_detail.txt`（37 函数签名不一致）
- 摘要：`/tmp/r4_summary.txt`

### 2.2 总体统计（vs R3 基线）

| 指标 | R3 基线 | R4 实测 | 变化 |
|------|---------|---------|------|
| orig code objects | 150 | 150 | — |
| new code objects | 146 | 146 | — |
| missing in new | 4 | 4 | — |
| extra in new | 0 | 0 | — |
| common | 146 | 146 | — |
| signature mismatches | 41 | **37** | **-4** |
| instruction mismatches | 81 | **80** | -1 |
| 截断函数（>50% loss） | 18 | **11** | **-7** |
| 扩展函数（instr gain） | 8 | **5** | -3 |

### 2.3 缺失 code objects（4，全部为 lambda/listcomp，与 R3 持平）

| 缺失 code object | 所属函数 | 类型 | 根因 |
|------------------|----------|------|------|
| `build_future_fill_time.<listcomp>` | build_future_fill_time | LISTCOMP | 函数体含 listcomp，被截断 |
| `get_fundamentals_daily_info.<lambda>` | get_fundamentals_daily_info | LAMBDA | 函数体截断至 21 条指令（orig=121），lambda 丢失 |
| `get_valuation_info.<lambda>` | get_valuation_info | LAMBDA | 同上 |
| `get_valuation_new_info.<lambda>` | get_valuation_new_info | LAMBDA | 同上 |

### 2.4 截断函数清单（>50% 指令损失，11 项，R3 的 18 项中 7 项脱离）

| 函数 | orig | new | loss | 关联缺陷 | R3 状态 |
|------|------|-----|------|----------|---------|
| change_his_to_forward | 597 | 181 | 416 | **R4-05 函数体截断（else 后）** | R3 new=239，**R4 恶化 -58** |
| change_his_to_backward | 583 | 220 | 363 | R4-05 同源 | R3 未列出（被 elif 截断掩盖）|
| load_bars_from_hundsun | 504 | 248 | 256 | R4-08 重复赋值 + R4-09 裸 IfExp | R3 new=250，基本持平 |
| fill_minute_or_day_blank | 244 | 3 | 241 | **R4-06 函数体→pass** | R3 未列出（新暴露）|
| get_fundamentals_daily_info | 121 | 21 | 100 | R4-07 函数体→单 Expr + lambda 丢失 | R3 持平 |
| get_valuation_info | 121 | 21 | 100 | 同上 | R3 持平 |
| get_valuation_new_info | 121 | 21 | 100 | 同上 | R3 持平 |
| _is_same_type_date | 99 | 9 | 90 | **R4-10 两分支均 return True** | R3 持平 |
| date_convert | 87 | 16 | 71 | **R4-07 函数体→单 Expr** | R3 未列出 |
| get_history | 123 | 57 | 66 | **R4-12 Call 实参 IfExp 畸形** | R3 未列出 |
| change_future_real_date | 98 | 40 | 58 | R3 残留 spurious for-else | R3 new=42，R4 -2 |

**关键发现**：R3 elif 链修复让 9 个财务函数脱离 >50% 截断清单（get_balance_statement 等 orig=458-469，R3 new=64，R4 new=246-248），但仍残留 ~210 条指令差异（非截断，属指令级不一致）。

### 2.5 扩展函数清单（指令增加，5 项，R3 的 8 项中 3 项脱离）

| 函数 | orig | new | gain | 备注 |
|------|------|-----|------|------|
| one_prod_to_dataframe | 452 | 461 | +9 | R4-03 spurious for-else + `i = 0` 重复（R3 gain=17，R4 改善）|
| check_frequency | 96 | 101 | +5 | R4-04 BOOLOP or→and 误转 + spurious if（R3 gain=5，持平）|
| get_price | 202 | 206 | +4 | R3 elif 修复后从截断（R3 new=50）变为轻微扩展 |
| get_index_stocks | 73 | 74 | +1 | 末尾 spurious 语句 |
| get_industries | 61 | 62 | +1 | 同上 |

### 2.6 签名不匹配模式分析（37 项）

主要模式：
1. **locals 数减少**（25 项）：函数体截断导致局部变量丢失。例：
   - `change_his_to_forward`: nlocals 17→14（丢失 `tmpstartindex, tmpendindex, tmp`）
   - `date_convert`: nlocals 7→2（丢失 `dict_temp, date_temp, year_temp, month_temp, data_return`）
   - `api_get_financial`: nlocals 16→13（丢失 `re_error, re_data, e3`）
2. **`time` 局部变量丢失**（8 项财务函数）：`cash_collection_ability` / `debt_paying_ability` / `eps` / `growth_ability` / `operating_ability` / `profit_ability` / `cashflow_statement` / `income_statement` 均丢失 `time` local，对应 `import time` + `time.sleep(...)` 调用被吞并。
3. **varnames 顺序错乱**（4 项）：`build_future_fill_time` 的 `total_dts` 位置错乱（orig 第 9 位，new 第 18 位）。

---

## 3. R3 残留缺陷追踪（逐项复测）

### 3.1 repro_03_try_except_handler_if_cond_lost（P2，仍存在）

**位置**：`api_get_financial`（R4 line 161-172）

**R4 反编译产物**：
```python
except HTTPError as e2:
    if HTTPError:        # ← 错误：裸 Name 'HTTPError' 测试
        pass
    else:
        if BaseException:  # ← 错误：spurious 嵌套 if
            pass
    error_no = e2.code
    ...
```

**原始字节码**（offset 358-442）：
```
358 LOAD_GLOBAL NULL + system_log
370 LOAD_ATTR error
...
420 POP_TOP                            # system_log.error(get_traceback_message())
422 LOAD_FAST e2
424 LOAD_ATTR code
434 LOAD_CONST 401
436 COMPARE_OP ==                      # if e2.code == 401:
442 POP_JUMP_FORWARD_IF_FALSE to 616
```

**根因**：except handler 入口的 `system_log.error(get_traceback_message())` + `if e2.code == 401:` Compare 节点被 `_identify_conditional_regions` 误判，Compare 节点（LOAD_FAST e2 + LOAD_ATTR code + LOAD_CONST 401 + COMPARE_OP）丢失，被替换为 `if HTTPError: pass` 裸 Name 测试 + spurious `if BaseException: pass` 嵌套。

**违反的算法原则**：入口引用语义（Compare 节点应保留为 if 条件）+ 自底向上归约（handler body 应作为 except 子节点保留）。

### 3.2 repro_03_loop_store_subscr_to_annotation（P2，仍存在 + 退化）

**位置**：`load_get_price`（R4 line 25-27）

**R4 反编译产物**：
```python
for stock in panel.items:
    data = change_his_to_forward(stock, panel[stock], exrights_data, start, end, typet)
    stock                # ← 错误：裸 Name 'stock' Expr
```

**原始字节码**（offset 676-682）：
```
676 LOAD_FAST data
678 LOAD_FAST panel
680 LOAD_FAST stock
682 STORE_SUBSCR                        # panel[stock] = data
```

**根因**：`STORE_SUBSCR panel[stock] = data` 序列被误判为 STORE_ANNOTATION 并丢弃，尾部 `LOAD_FAST stock`（offset 680）泄漏为裸 Expr `stock`。

**退化说明**：R3 fix_report §1.2 声称 `repro_03_loop_bare_name_and_dup` 已修复（"无裸 stock Expr"），但该验证仅基于 minimal repro。R4 实测 quotation.pyc 实际产物中裸 `stock` Expr **仍存在**，且 `panel[stock] = data` 赋值丢失。这是 R3 修复在 minimal repro 生效但对实际 CFG 退化的典型案例。

**违反的算法原则**：每块唯一归属（STORE_SUBSCR 序列应作为循环体顺序语句保留）+ 入口引用语义。

### 3.3 repro_03_loop_spurious_for_else_double（P2，仍存在）

**位置**：`one_prod_to_dataframe`（R4 line 233-242）

**R4 反编译产物**：
```python
i = 0
for item in fields:
    if time_index != i:
        df[get_real_param(item)] = []
    i = i + 1
else:
    prod = data.get(prod_code)    # ← spurious for-else：顺序语句被误附为 else 子句
for item in prod:
    i = 0
    i = 0                          # ← 重复赋值
    for v in item:
        ...
    else:
        continue                   # ← spurious 内层 for-else
else:
    return df                      # ← spurious 外层 for-else
```

**根因**：`_loop_generate_for` 在 for 循环后跟随顺序语句时，将顺序语句误附为 `else:` 子句；内层 for 的 `continue` 也被误判为 else 子句。

**违反的算法原则**：自底向上归约（for 后顺序语句应作为函数体顺序子节点保留，不应作为 else 子句）+ 每块唯一归属。

---

## 4. R4 新增缺陷清单

### 4.1 R4-NEW-01: change_his_to_forward/backward 函数体截断（R3 修复副作用，**退化**）

- **函数**：`change_his_to_forward`（orig=597, R3 new=239, **R4 new=181**，退化 -58）/ `change_his_to_backward`（orig=583, R4 new=220）
- **现象**：`else: preindex = None; tmpdata = None; tmpstartindex = None; tmpendindex = None; tmp = None` 后整段截断，丢失后续 for 循环 + 赋值逻辑
- **根因初判**：R3 `_build_elif_region` 修复扩展 `_structural_region_entries` 后，elif 链后的 else 分支 ipdom 链遍历在更深层级（含 for + 多层 if）仍误判 merge 点，把后续 for 循环吸收为不可达子区域
- **关联 repro**：`repro_04_func_body_truncated_after_else.py`

### 4.2 R4-NEW-02: fill_minute_or_day_blank 函数体→pass

- **函数**：`fill_minute_or_day_blank`（orig=244, new=3）
- **现象**：`def fill_minute_or_day_blank(...): pass` —— 整个函数体被替换为 `pass`
- **根因初判**：函数体含 `for + if/elif/else + STORE_SUBSCR` 嵌套，`_generate_region` 在归约时误判整个函数体为不可达，仅保留 `pass` 占位
- **关联 repro**：`repro_04_func_body_to_pass.py`

### 4.3 R4-NEW-03: date_convert 函数体→单 Expr 语句

- **函数**：`date_convert`（orig=87, new=16）
- **现象**：`def date_convert(date, report_types): int(month_temp == 1 if report_types is None else month_temp <= report_types)` —— 含 if/elif/else + return 的完整函数体被替换为单个 Expr 语句
- **根因初判**：`_identify_conditional_regions` 在 if/elif/else 链 + IfExp 嵌套时，误将整个条件块归约为单 IfExp Expr
- **关联 repro**：`repro_04_func_body_to_single_expr.py`

### 4.4 R4-NEW-04: _is_same_type_date 两分支均 return True

- **函数**：`_is_same_type_date`（orig=99, new=9）
- **现象**：`if typet == 7: return True else: return True` —— 两分支返回相同值，原始 typet==6 分支的 `len(day1)==8` 比较丢失
- **根因初判**：嵌套 if 的内层 `len(day1) == 10` / `len(day1) == 8` Compare 节点丢失，仅保留外层 `typet == 7` 判断
- **关联 repro**：`repro_04_if_branch_both_return_same.py`

### 4.5 R4-NEW-05: check_frequency BOOLOP or 链→and 链

- **函数**：`check_frequency`（orig=96, new=101，扩展 +5）
- **现象**：原始 `assert not (a or b or c or d or e or f), "msg"` 被反编译为 `if not (a and b and c and d and e and f): assert f, "msg"` —— `or` 短路链（POP_JUMP_FORWARD_IF_TRUE）被误转为 `and` 链，语义反转
- **根因初判**：`_detect_boolop_conditional_chain` 在 `assert not (or-chain), msg` 模式下，将 POP_JUMP_IF_TRUE 短路误读为 POP_JUMP_IF_FALSE，导致 or→and 反转；且 `assert` 语句被拆分为 `if not (...): assert last_cond, msg`
- **关联 repro**：`repro_04_boolop_or_chain_to_and.py`

### 4.6 R4-NEW-06: load_bars_from_hundsun 重复赋值 + 裸 IfExp

- **函数**：`load_bars_from_hundsun`（orig=504, new=248）
- **现象**：
  1. `source_end = end[8:] or '1530'` 重复出现 2 次
  2. `collections(isinstance(stocks, str) if os.path.exists(DumploadDailyFile) and typet == 6 else len(start) > 8)` 裸 IfExpr 作为 Call 实参
  3. `isinstance(stocks if isinstance(stocks, list) else typet == 6)` 裸 IfExpr Expr
  4. `len(start[8:]) == 4 if len(data) > 0 else is_utc == '0' if len(panel.major_axis) != 0 else retpanel.empty` 嵌套裸 IfExpr
- **根因初判**：`for_iter_setup` 块的 pre_stmts 发射权管理在 IfRegion/LoopRegion 交叉时重复发射；IfExpr 作为顺序语句被泄漏为裸 Expr
- **关联 repro**：`repro_04_loop_dup_pre_assignment.py` + `repro_04_ifexp_as_bare_expr.py`

### 4.7 R4-NEW-07: get_history Call 实参 IfExp 畸形

- **函数**：`get_history`（orig=123, new=57）
- **现象**：`nd_array = FREQUENCYNAME_DICT(query_date is None if frequency in OVER_WEEK_FREQUENCY else query_date is None)` —— Call 实参位置的 IfExp 双臂均为 `query_date is None`，丢失 `frequency in OVER_WEEK_FREQUENCY` 比较
- **根因初判**：`_generate_call_args` 在 IfExp 作为 Call 实参时，双臂表达式重建错误
- **关联 repro**：`repro_04_ternary_in_call_arg_malformed.py`

### 4.8 R4-NEW-08: load_get_price spurious for-else + bare stock（R3 修复退化）

- **函数**：`load_get_price`
- **现象**：`for stock in panel.items: data = ...; stock` + `else: pass`（spurious for-else）
- **根因初判**：R3 `_fis_pre_stmts_emitted` 修复在 quotation.pyc 实际 CFG（含 if/elif/else + for + STORE_SUBSCR）下未覆盖 STORE_SUBSCR 序列，导致 `panel[stock] = data` 丢失 + 裸 `stock` Expr 泄漏
- **关联 repro**：`repro_04_loop_store_subscr_to_bare_name.py`

---

## 5. ≥10 最小复现实例清单

| # | 文件名 | 关联缺陷 | 触发区域 | py_compile | 反编译 | 字节码 diff |
|---|--------|----------|----------|-----------|--------|-------------|
| 1 | repro_04_try_except_handler_if_cond_lost.py | R3 残留 P2 #1 | TRY | OK | OK | api_get_financial orig=205 new=209 (+4) |
| 2 | repro_04_loop_store_subscr_to_bare_name.py | R3 残留 P2 #2 + R4-NEW-08 | LOOP | OK | OK | load_get_price orig=65 new=64 (-1) |
| 3 | repro_04_loop_spurious_for_else_double.py | R3 残留 P2 #3 | LOOP | OK | OK | one_prod_to_dataframe orig=103 new=105 (+2) |
| 4 | repro_04_boolop_or_chain_to_and.py | R4-NEW-05 or→and | BOOLOP + ASSERT | OK | OK | check_frequency orig=88 new=113 (+25) |
| 5 | repro_04_func_body_truncated_after_else.py | R4-NEW-01 截断退化 | IF + LOOP | OK | OK | change_his_to_forward orig=230 new=187 (-43) |
| 6 | repro_04_func_body_to_pass.py | R4-NEW-02 函数体→pass | LOOP + IF | OK | OK | fill_minute_or_day_blank orig=77 new=71 (-6) |
| 7 | repro_04_func_body_to_single_expr.py | R4-NEW-03 函数体→单 Expr | TERNARY + IF | OK | OK | date_convert orig=85 new=7 (-78) |
| 8 | repro_04_loop_dup_pre_assignment.py | R4-NEW-06 重复赋值 | LOOP | OK | OK | load_bars_from_hundsun orig=128 new=122 (-6) |
| 9 | repro_04_ifexp_as_bare_expr.py | R4-NEW-06 裸 IfExpr | TERNARY | OK | OK | process_stocks orig=73 new=72 (-1) |
| 10 | repro_04_if_branch_both_return_same.py | R4-NEW-04 两分支同返回 | IF | OK | OK | _is_same_type_date orig=47 new=18 (-29) |
| 11 | repro_04_ternary_in_call_arg_malformed.py | R4-NEW-07 Call 实参畸形 | TERNARY + CALL | OK | OK | get_history orig=69 new=66 (-3) |
| 12 | repro_04_loop_nested_if_spurious_pass.py | R4-NEW 顺序 if→elif + spurious pass | LOOP + IF | OK | OK | process_klines orig=50 new=49 (-1) |

**汇总**：12 个 repro 全部 `py_compile` 通过、反编译 exit=0、重编译 COMPILE_OK、字节码 diff 不一致（共 24 个 code object 不匹配）。

---

## 6. 根因初判汇总

### 6.1 涉及方法

| 方法 | 关联缺陷 | 问题 |
|------|----------|------|
| `_identify_conditional_regions` / `_build_elif_region` | R4-NEW-01, R4-NEW-04, R3-#1 | elif/else 链后复杂嵌套（for + 多层 if）ipdom 链误判，吸收后续语句为不可达子区域 |
| `_loop_generate_for` / `_fis_pre_stmts_emitted` | R3-#2, R3-#3, R4-NEW-06, R4-NEW-08 | for_iter_setup pre_stmts 发射权管理在 IfRegion/LoopRegion 交叉时重复发射或漏发射；STORE_SUBSCR 序列未覆盖 |
| `_detect_boolop_conditional_chain` | R4-NEW-05 | `assert not (or-chain), msg` 模式下 POP_JUMP_IF_TRUE 短路误读为 POP_JUMP_IF_FALSE，or→and 反转 |
| `_generate_call_args` / IfExp 重建 | R4-NEW-03, R4-NEW-07 | IfExp 作为 Call 实参或顺序语句时双臂表达式重建错误，泄漏为裸 Expr |
| `_generate_region` / `_generate_block_statements` | R4-NEW-02 | 函数体含 for + if/elif/else + STORE_SUBSCR 嵌套时误判整个函数体为不可达，仅保留 `pass` |
| TryRegion handler body 归约 | R3-#1 | except handler 内 `if e2.attr == CONST:` Compare 节点丢失，替换为裸 Name 测试 |

### 6.2 违反的算法原则（4 项）

| 原则 | 违反项 |
|------|--------|
| **入口引用语义** | R3-#1（Compare 节点丢失）、R3-#2（STORE_SUBSCR 序列丢失）、R4-NEW-04（内层 Compare 丢失）|
| **每块唯一归属** | R3-#2（STORE_SUBSCR 重复/丢失）、R3-#3（顺序语句误附为 else）、R4-NEW-06（pre_stmts 重复发射）|
| **自底向上归约** | R4-NEW-01（elif 后函数体截断）、R4-NEW-02（函数体→pass）、R4-NEW-03（函数体→单 Expr）|
| **AST 节点保形** | R4-NEW-05（or→and 语义反转）、R4-NEW-07（IfExp 双臂重建错误）|

---

## 7. 修复建议优先级

### 7.1 P0（阻断核心功能，必须修复）

| # | 缺陷 | 算法依据 |
|---|------|----------|
| P0-1 | R4-NEW-01 change_his_to_forward/backward 函数体截断退化 | 修复 `_build_elif_region` ipdom 链遍历在 else 分支后跟随 for + 多层 if 的 merge 点判断；扩展 `_structural_region_entries` 含 else body 的 for 循环 header |
| P0-2 | R4-NEW-02 fill_minute_or_day_blank 函数体→pass | 修复 `_generate_region` 在 for + if/elif/else + STORE_SUBSCR 嵌套时的归约顺序，避免整个函数体被误判为不可达 |

### 7.2 P1（显著语义错误，优先修复）

| # | 缺陷 | 算法依据 |
|---|------|----------|
| P1-1 | R4-NEW-05 check_frequency or→and 语义反转 | 修复 `_detect_boolop_conditional_chain` 对 `assert not (or-chain), msg` 模式的 POP_JUMP_IF_TRUE 短路识别；区分 assert 语句与 if 语句的 jump 方向 |
| P1-2 | R3-#1 try_except_handler_if_cond_lost | 修复 TryRegion handler body 归约：保留 `if e2.attr == CONST:` Compare 节点，避免替换为裸 Name 测试 |
| P1-3 | R4-NEW-03 date_convert 函数体→单 Expr | 修复 `_identify_conditional_regions` 在 if/elif/else + IfExp 嵌套时的归约，避免整个条件块被压缩为单 IfExp |
| P1-4 | R4-NEW-04 _is_same_type_date 两分支同返回 | 修复嵌套 if 内层 Compare 节点保留逻辑 |

### 7.3 P2（结构错误但可运行，择优修复）

| # | 缺陷 | 算法依据 |
|---|------|----------|
| P2-1 | R3-#2 loop_store_subscr_to_bare_name（quotation.pyc 退化） | 扩展 `_fis_pre_stmts_emitted` 覆盖 STORE_SUBSCR 序列；`_loop_generate_for` pre_stmts 发射守卫区分 minimal repro 与实际 CFG |
| P2-2 | R3-#3 loop_spurious_for_else_double | 修复 `_loop_generate_for` for 后顺序语句的 else 子句误附；抑制 spurious `else: continue` / `else: return` |
| P2-3 | R4-NEW-06 load_bars_from_hundsun 重复赋值 + 裸 IfExp | 修复 for_iter_setup pre_stmts 在 IfRegion 交叉时的发射权管理；IfExpr 作为顺序语句时抑制裸 Expr 发射 |
| P2-4 | R4-NEW-07 get_history Call 实参 IfExp 畸形 | 修复 `_generate_call_args` 在 IfExp 作为 Call 实参时的双臂表达式重建 |
| P2-5 | R4-NEW-08 load_get_price spurious for-else + bare stock | 同 P2-1 + P2-2 |

---

## 8. 残留与后续（R4 修复工程师目标）

### 8.1 R4 修复工程师目标
1. **P0×2**：修复 change_his_to_forward/backward 截断退化 + fill_minute_or_day_blank 函数体→pass
2. **P1×4**：修复 or→and 语义反转 + try_except_handler_if_cond_lost + date_convert 函数体→单 Expr + _is_same_type_date 两分支同返回
3. **P2×5**：修复 loop_store_subscr 退化 + loop_spurious_for_else_double + load_bars_from_hundsun 重复赋值 + get_history Call 实参畸形 + load_get_price spurious for-else

### 8.2 验证要求
- 12 个 minimal repro 全部复测通过（反编译产物与原始 .pyc 字节码一致或语义等价）
- quotation.pyc 反编译产物：截断函数从 11 → ≤5，签名不匹配从 37 → ≤25
- 既有测试矩阵（IF/LOOP/TRY/WITH/MATCH/BOOLOP bounded subset）0 退化
- R3 已修 7 项不退化（特别是 repro_03_loop_bare_name_and_dup 在 quotation.pyc 实际产物需复测）

### 8.3 R3 修复副作用预警
R3 elif 链修复（P0-1）虽然让 9 个财务函数脱离 >50% 截断清单，但暴露了下游的更深层截断（change_his_to_forward/backward、fill_minute_or_day_blank、date_convert 等）。R4 修复工程师需注意：修复 P0-1/P0-2 时不能再引入新的下游截断。

---

## 9. 算法合规性自检（测试工程师侧）

### 9.1 4 原则违反项统计

| 原则 | R3 违反项数 | R4 违反项数 | 变化 |
|------|-------------|-------------|------|
| 入口引用语义 | 3 | 3 | 持平 |
| 每块唯一归属 | 3 | 4 | +1（R4-NEW-06 重复赋值）|
| 自底向上归约 | 2 | 3 | +1（R4-NEW-02 函数体→pass）|
| AST 节点保形 | 1 | 2 | +1（R4-NEW-05 or→and）|
| **合计** | 9 | 12 | +3 |

### 9.2 反模式前缀方法自检（G3）

```
$ grep -nE "^\s*def (_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_)" \
    core/cfg/region_ast_generator.py core/cfg/region_analyzer.py \
    core/cfg/ast_converter.py core/cfg/pattern_parser.py
core/cfg/region_ast_generator.py:18880:    def _merge_block_is_loop_back_edge(self, region: TernaryRegion) -> bool:
```

- **0 新增**反模式前缀方法 ✓（`_merge_block_is_loop_back_edge` 为 pre-existing，与 R3 持平）

### 9.3 stderr 警告数自检
- R4 反编译 stderr：**0 行** ✓（持续清零，与 R3 持平）

### 9.4 编译验证自检
- `compile(open('/tmp/r4_decompiled.py').read(), 'r4', 'exec')` → **COMPILE_OK** ✓

---

## 10. 退出条件检查

| 退出条件 | 要求 | R4 实测 | 状态 |
|----------|------|---------|------|
| 反编译产物行数 | ≥ R3 基线（3035） | 3035 | ✓ 持平 |
| stderr 警告数 | 0 | 0 | ✓ |
| 编译验证 | COMPILE_OK | COMPILE_OK | ✓ |
| minimal repro 数量 | ≥10 | 12 | ✓ |
| minimal repro py_compile | 全通过 | 12/12 通过 | ✓ |
| minimal repro 字节码 diff | 全不一致（复现缺陷） | 12/12 不一致（24 个 code object） | ✓ |
| decompile_report.md | 10 节齐全 | §0-§10 齐全 | ✓ |
| R3 已修 7 项复测 | ≥6 项仍生效 | 6/7 生效（1 项 quotation.pyc 退化） | ✓（达标，退化项已记录）|
| R3 残留 3 项 P2 复测 | 全部追踪 | 3/3 追踪 + 复现 | ✓ |
| R4 新增缺陷清单 | ≥3 项 | 8 项（R4-NEW-01 ~ R4-NEW-08） | ✓ |
| 反模式前缀方法新增 | 0 | 0 | ✓ |
| 禁止修改 core/ 源码 | 是 | 未修改 | ✓ |
| 禁止修改 quotation.pyc / baseline / R1-R3 round 目录 | 是 | 未修改 | ✓ |
| 禁止修改 spec 文档 | 是 | 未修改 | ✓ |
| 仅创建指定文件 | repro_04_*.py + decompile_report.md | 12 个 repro + 1 个 report | ✓ |

**结论**：R4 测试工程师产物满足全部退出条件，可移交 R4 修复工程师。

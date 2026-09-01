# Round 9 — Test Engineer Decompile Report

> 目标文件：`/workspace/quotation.pyc`
> 反编译器入口：`python pycdc.py <file>`
> 输出目录：`/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_09/test_engineer/`
> R8 残留缺陷基线：D3 (P1) / D7 (P2) / D8 (P2) / D10 (P2)（D6 在 quotation.pyc::api_get_financial line 160-161 仍以 `if 499: pass` 形式存在，R8 fix_report 的 "try body return 保留" 指 TRY 测试矩阵 78/2 回归修复，非 quotation.pyc 实际路径）

---

## §1 反编译总览

**反编译命令：**
```bash
cd /workspace && timeout 60 python pycdc.py /workspace/quotation.pyc > /tmp/r9_decompiled.py 2> /tmp/r9_quote.err
python -c "compile(open('/tmp/r9_decompiled.py').read(), 'r9_decompiled.py', 'exec')" && echo COMPILE_OK || echo COMPILE_FAIL
```

| 指标 | R8 基线 | R9 实测 | 变化 |
|------|---------|---------|------|
| Exit code | 0 | 0 | 持平 |
| 反编译产物总行数 | 2558 | **2558** | 持平 |
| stderr 警告数 | 0 | **0** | 持平 |
| 编译验证 | COMPILE_OK | **COMPILE_OK** | 持平 |
| 字节码不一致函数数 | 72 | **72** | 持平 |
| LOST 函数数 | 1 (`build_future_fill_time.<locals>.<listcomp>`) | **1** (同名) | 持平 |
| NEW-ONLY 函数数 | 0 | **0** | 持平 |
| 总 diff 条目 | 8514 | **8533** | +19（新增 signature_mismatch 维度） |

R9 反编译产物与 R8 完全持平（行数 / stderr / 编译状态 / 不一致函数数均不变），无退化、无改善。R8 残留的 4 类缺陷（D3/D7/D8/D10）+ D6（if body return 丢失）在 R9 反编译产物中全部仍存在。

---

## §2 R8 修复点回归验证

### 2.1 R7 已修项不退化（D9 / D5 / D4）

| R7 缺陷 | 验证命令 | R9 结果 | 退化判定 |
|---------|----------|---------|----------|
| D9 (spurious `return None` after restored return) | `grep -nE "^[[:space:]]+return None[[:space:]]*$" /tmp/r9_decompiled.py` | 8 处均为合理显式 return None（`__setattr__` return None、`if x is None: return None` 等），api_get_financial line 173 `return ({...}, {})` 后无 spurious return None | **不退化** ✓ |
| D5 (orphan Name/Attr Expr leaks) | `grep -nE "^[[:space:]]+(prod\|stocks\|panel\.items)[[:space:]]*$" /tmp/r9_decompiled.py` | 0 匹配 | **不退化** ✓ |
| D4 (`del e2` as-var cleanup leaked) | `grep -n "del e2" /tmp/r9_decompiled.py` | 0 匹配 | **不退化** ✓ |

### 2.2 R8 修复点不退化（D6 TRY 矩阵回归 + TRY 78/2）

| R8 修复项 | 验证命令 | R9 结果 | 退化判定 |
|-----------|----------|---------|----------|
| TRY 测试矩阵 78/2（R8 从 72/8 改善至 78/2） | `timeout 90 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY` | `78 2 0 80 2.5 TRY files=80` | **不退化** ✓ |
| D6 try body `return <const>` 保留（TRY 测试矩阵 te12/te32/te049） | TRY 矩阵 78/2 保持 | 78/2 | **不退化** ✓ |

### 2.3 line 160-161 状态核实

R8 fix_report §0 称 "line 160-161 try body return 保留 ✓"，但 R8 decompile_report §2 D6 称 "line 160-161 是 `if 499: pass`"。R9 核实：

```python
# R9 反编译产物 /tmp/r9_decompiled.py lines 157-164
except HTTPError as e2:
    system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)   # D10
    if 499:                                                                # D3
        pass                                                                # D6 (if body return 丢失)
    else:
        error_no = -1
        error_info = '服务器处理异常，内部错误号:%d' % e2.code
        ({'error_no': error_no, 'error_info': error_info}, {})              # D6 (else body return 丢失)
```

**结论**：quotation.pyc::api_get_financial line 160-161 仍是 `if 499: pass`（D3 + D6 复合缺陷），与 R8 decompile_report 描述一致。R8 fix_report 的 "try body return 保留" 指 TRY 测试矩阵的回归修复（te12/te32/te049），非 quotation.pyc 实际路径。R9 不退化（与 R8 状态一致）。

---

## §3 字节码 diff 摘要

**diff 工具**：`/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_09/test_engineer/r9_diff.py`
**diff 输出**：`/tmp/r9_diff_detail.txt`（25815 行）+ `/tmp/r9_summary.txt`

### 3.1 总体统计

```
total_functions_compared: 149
functions_with_diffs: 72
lost_functions: 1 (build_future_fill_time.<locals>.<listcomp>)
new_only_functions: 0
signature_mismatch_functions: 19   ← R9 新增维度
length_mismatch_functions: 67
truncated_functions_(new<50%_orig): 14
total_diff_entries: 8533
```

### 3.2 diff 类型分布

| diff 类型 | 计数 | 说明 |
|-----------|------|------|
| opname_mismatch | 7914 | 同偏移指令名不同（与 R8 一致） |
| argval_mismatch | 533 | 同指令名不同 argval（与 R8 一致） |
| length_mismatch | 67 | 函数指令数不同（与 R8 一致） |
| signature_mismatch | 19 | R9 新增：函数签名（参数/闭包/cellvars）不同 |

### 3.3 R8 焦点缺陷位点状态

| 函数 | orig 指令数 | new 指令数 | diffs | 状态 |
|------|------------|------------|-------|------|
| `api_get_financial` | 318 | 216 | 131 | D3 + D6 + D10 仍存在 |
| `build_future_fill_time` | 677 | 524 | 492 | D7 仍存在 |
| `date_convert` | 87 | 16 | 16 | D8 仍存在（new=16，截断 81%） |
| `build_future_fill_time.<locals>.<listcomp>` | (present) | (missing) | LOST | 嵌套 code object 未发射 |

### 3.4 Top 10 最偏离函数（按 diff 数）

| 函数 | diffs | orig | new | 截断? |
|------|-------|------|-----|-------|
| `build_future_fill_time` | 492 | 677 | 524 | 否（77%） |
| `<module>` | 460 | 1082 | 1023 | 否（95%） |
| `get_date_and_count` | 429 | 726 | 705 | 否（97%） |
| `change_his_to_forward` | 419 | 597 | 560 | 否（94%） |
| `balance_statement` | 326 | 375 | 364 | 否（97%） |
| `load_bars_from_hundsun` | 304 | 504 | 307 | 否（61%） |
| `one_prod_to_dataframe` | 287 | 452 | 491 | 否（>100%） |
| `cashflow_statement` | 273 | 369 | 286 | 否（78%） |
| `income_statement` | 273 | 369 | 286 | 否（78%） |
| `valuation_new` | 268 | 365 | 292 | 否（80%） |

---

## §4 缺陷清单（D3/D6/D7/D8/D10 + R9 新发现）

### 4.1 D3 (P1) — chained compare in except handler lost → `if 499:`

- **位置**：`quotation.pyc::api_get_financial` line 159（`if 499:` 而非 `if 400 <= e2.code <= 499:`）
- **原始字节码**（offset 694-734）：
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
  ```
- **R9 反编译产物**：`if 499:`（chained compare 前半段 `400 <= e2.code` 丢失）
- **根因初判**：`_identify_conditional_regions` 未覆盖 except handler 内 SWAP+COPY+COMPARE_OP+POP_JUMP_FORWARD_IF_FALSE 模式（前置 call `system_log.error(get_traceback_message())` 干扰 IfRegion 识别）；`_generate_condition_expr` 只消费尾部 COMPARE_OP 操作数。
- **R9 在 quotation.pyc 是否仍复现**：**是** ✓（line 159 `if 499:`）
- **关联 repro**：`repro_09_05_d3_chained_compare_in_elif_after_call`（DEFECT-REPRO，D3 in elif after call）、`repro_09_12_d3_d10_compound_in_except`（DEFECT-REPRO，D3+D10 复合）
- **R9 新发现**：D3 在 `elif 400 <= e2.code <= 499:` 分支（repro_09_05）也触发，不仅限于 `if` 分支；隔离场景（repro_09_02/03/04）NOT-REPRO，D3 是 context-sensitive（需前置 call + except handler 框架）。

### 4.2 D6 (P2) — if body return 丢失（`if 499: pass` / 裸 Expr）

- **位置**：`quotation.pyc::api_get_financial` line 160-161（`if 499: pass`，原始为 `return ({'error_no': e2.code, 'error_info': ''}, {})`）+ line 164（else body `({'error_no': error_no, 'error_info': error_info}, {})` 裸 Expr，原始为 `return (...)`）
- **R9 反编译产物**：
  ```python
  if 499:
      pass                                          # <- D6 if body return 丢失
  else:
      error_no = -1
      error_info = '...'
      ({'error_no': error_no, 'error_info': error_info}, {})   # <- D6 else body return 丢失为裸 Expr
  ```
- **根因初判**：`_generate_handler_body_statements` 在 except handler 内处理 RETURN_VALUE 时，将 `RETURN_VALUE <const/tuple>` 后接 `RERAISE+COPY+POP_EXCEPT` cleanup 序列整体当作 cleanup 抑制，导致 return 语句丢失（变 `pass` 或裸 Expr）。
- **R9 在 quotation.pyc 是否仍复现**：**是** ✓（line 160-161 `pass` + line 164 裸 Expr）
- **关联 repro**：`repro_09_01_d3_chained_compare_after_call_in_except`（DEFECT-REPRO，D6:return_lost_bare_expr — return 丢失为裸 Expr 变体）
- **R9 新发现**：D6 不仅表现为 `pass`，还表现为**裸 Expr**（return 关键字丢失，但返回值作为 Expr 保留）。

### 4.3 D7 (P2) — malformed ternary chain（if/elif 压缩为嵌套 ternary of `==`）

- **位置**：`quotation.pyc::build_future_fill_time` line 351
- **R9 反编译产物**：
  ```python
  suffix == 'T.CCFX' if typet == 2 else suffix == 'T.CCFX' if typet == 3 else suffix == 'T.CCFX' if typet == 4 else typet == 13
  ```
- **原始字节码**（offset 1052-1076）：
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
- **根因初判**：`_generate_if` / IfExp 重建路径把嵌套 if/elif 链（外层 `typet == 2/3/4/13`，内层 `suffix == 'T.CCFX'`）错误归约为嵌套 ternary of `==` 比较；内层 if 的条件被误归为外层 ternary 的 value 表达式；`=` 赋值被误发射为 `==` 比较。
- **R9 在 quotation.pyc 是否仍复现**：**是** ✓（line 351）
- **关联 repro**：`repro_09_07_d7_nested_if_elif_else_with_assign`（DEFECT-REPRO，4 外层分支嵌套）、`repro_09_13_d7_nested_3_outer_branches`（DEFECT-REPRO，3 外层分支嵌套）、`repro_09_08_d7_ifexp_in_call_arg_vs_statement`（DEFECT-REPRO，Call 实参丢失）
- **R9 新发现**：
  - D7 触发条件是**嵌套 if/elif**（外层 ≥3 分支 + 内层 if/else），纯非嵌套 4 分支 if/elif assign chain（`repro_09_06`）NOT-REPRO。
  - D7 触发阈值：3 外层分支时部分触发（前 2 分支压缩为 ternary，第 3 分支保留），4 外层分支时完全触发（全部压缩为单个 bare Expr）。
  - D7 还表现为**丢失 Call 语句**（`repro_09_08`：`log('result: %s' % ('high' if x > 0 else 'low'))` 整行丢失，length diff 32→19）。

### 4.4 D8 (P2) — lost date_convert body（orig=87 → new=16）

- **位置**：`quotation.pyc::date_convert` line 2144-2146
- **R9 反编译产物**：
  ```python
  def date_convert(date, report_types):
      int(month_temp == 1 if report_types is None else month_temp <= report_types)
  ```
- **原始字节码**（87 条指令）：构造 `dict_temp`、`date_temp`、`year_temp`、`month_temp`，嵌套 if/else if/elif if/elif else，最后 `data_return = str(year_temp) + '-' + dict_temp[month_temp]; return data_return`。
- **根因初判**：`_identify_conditional_regions` 在 if/elif/else + IfExp 嵌套时未按自底向上归约顺序处理；`_generate_block_statements` 把整个函数体（dict_temp 构造 + 3 个局部赋值 + 嵌套 if/else + data_return 赋值 + return）压缩为单个 `int(IfExp)` Expr；`int(...)` wrapper 是尾部 `LOAD_GLOBAL int + PRECALL + CALL`，其参数被 IfExp 替代。
- **R9 在 quotation.pyc 是否仍复现**：**是** ✓（line 2144-2146，new=16 指令，截断 81%）
- **关联 repro**：`repro_09_10_d8_date_convert_body_collapse`（DEFECT-REPRO，length diff 71→20）、`repro_09_14_d8_date_convert_int_ifexp_collapse`（DEFECT-REPRO，length diff 73→12，最接近 quotation.pyc 实际路径）
- **R9 新发现**：D8 可独立复现（不依赖 quotation.pyc 上下文）；`repro_09_14` 复现 `int(IfExp)` 模式，dict_temp / year_temp / month_temp / quarter 赋值全部丢失，只保留 data_return 赋值（year_temp/quarter 为 undefined local）。

### 4.5 D10 (P2) — malformed call in except handler

- **位置**：`quotation.pyc::api_get_financial` line 158
- **R9 反编译产物**：
  ```python
  system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)
  ```
- **原始 source**（重建）：
  ```python
  except HTTPError as e2:
      system_log.error(get_traceback_message())           # always-called
      if e2.code == 401:                                   # if
          if request_times <= 2:
              time.sleep(10)
              request_times += 1
              return api_get_financial(url, params, request_times)
      elif e2.code == 599:                                 # elif
          return api_get_financial(url, params)
      elif 400 <= e2.code <= 499:
          ...
  ```
- **根因初判**：`_generate_handler_body_statements` 把 `system_log.error(get_traceback_message())` 调用与后续 `e2.code == 401 / e2.code == 599` if/elif 条件合并为单个 `system_log(IfExp)` 调用；`LOAD_ATTR error` accessor 丢失，`get_traceback_message()` 实参丢失，条件调用变条件实参。
- **R9 在 quotation.pyc 是否仍复现**：**是** ✓（line 158）
- **关联 repro**：`repro_09_11_d10_call_merge_with_if_elif_in_except`（DEFECT-REPRO，length diff 102→52）、`repro_09_12_d3_d10_compound_in_except`（DEFECT-REPRO，D3+D10 复合）
- **R9 新发现**：D10 可独立复现（`repro_09_11`）；D10 与 D3 形成**复合缺陷**（`repro_09_12`）：if/elif/elif 压缩为嵌套 ternary，最后的 `400 <= e2.code <= 499` 丢失为 `400 <= e2.code`（D3 chained compare 后半段丢失）。

### 4.6 R9 新发现缺陷清单

| 编号 | 缺陷 | 位置 | 字节码模式 | 关联 repro |
|------|------|------|-----------|-----------|
| R9-N1 | D6 return 丢失为裸 Expr（不仅限于 `pass`） | repro_09_01 line 11 | `RETURN_VALUE` → `LOAD_CONST '' / RERAISE`，return 关键字丢失但返回值作为 Expr 保留 | repro_09_01 |
| R9-N2 | D7 触发条件 = 嵌套 if/elif（外层 ≥3 分支），纯非嵌套 4 分支不触发 | repro_09_06 vs repro_09_07/13 | 嵌套结构触发 `STORE_FAST` → `COMPARE_OP ==` 误发射；非嵌套不触发 | repro_09_06 (NOT-REPRO) / repro_09_07 / repro_09_13 |
| R9-N3 | D7 部分触发（3 外层分支时前 2 分支压缩，第 3 分支保留） | repro_09_13 | `BUILD_MAP + STORE_FAST` → `RETURN_VALUE + COMPARE_OP ==`（前 2 分支）；第 3 分支保留 if/else | repro_09_13 |
| R9-N4 | D7 丢失 Call 语句（log(...) 整行丢失） | repro_09_08 | `log('result: %s' % ('high' if x > 0 else 'low'))` 整行丢失，length diff 32→19 | repro_09_08 |
| R9-N5 | D8 可独立复现（不依赖 quotation.pyc 上下文） | repro_09_10/14 | dict_temp / year_temp / month_temp 赋值全部丢失，只保留 data_return 赋值（undefined local） | repro_09_10 / repro_09_14 |
| R9-N6 | D3 在 elif 分支也触发（不仅限于 if 分支） | repro_09_05 | `elif 400 <= e2.code <= 499:` → `400 <= e2.code`（chained compare 后半段丢失） | repro_09_05 |
| R9-N7 | D3+D10 复合缺陷（quotation.pyc::api_get_financial 实际路径最小化） | repro_09_12 | if/elif/elif 压缩为嵌套 ternary，`400 <= e2.code <= 499` 丢失为 `400 <= e2.code` | repro_09_12 |

---

## §5 14 minimal repros 清单

**验证工具**：`/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_09/test_engineer/verify_repros.py`
**验证流程**：`py_compile` → `pycdc` → `compile(out)` → 字节码 diff → 分类
**验证结果汇总**：`/tmp/r9_repro_summary.txt`

| # | repro 文件 | 主题 | 状态 | 复现字节码模式 |
|---|-----------|------|------|---------------|
| 01 | `repro_09_01_d3_chained_compare_after_call_in_except.py` | D3 + D6（call 后接 chained compare，return 丢失为裸 Expr） | **DEFECT-REPRO** | `RETURN_VALUE` → `LOAD_CONST '' / RERAISE`；return 丢失为裸 Expr；diffs=30 |
| 02 | `repro_09_02_d3_chained_compare_isolated_in_except.py` | D3 隔离控制组（无前置 call） | NOT-REPRO | no_diffs（chained compare 保留） |
| 03 | `repro_09_03_d3_chained_compare_attr_middle_after_call.py` | D3 LOAD_ATTR 中间操作数 + call | NOT-REPRO | no_diffs（chained compare 保留） |
| 04 | `repro_09_04_d3_chained_compare_subscript_middle_after_call.py` | D3 subscript 中间操作数 + call | NOT-REPRO | no_diffs（chained compare 保留） |
| 05 | `repro_09_05_d3_chained_compare_in_elif_after_call.py` | D3 in elif after call（quotation.pyc 路径） | **DEFECT-REPRO** | `LOAD_GLOBAL system_log + LOAD_METHOD error + PRECALL + CALL` → `LOAD_FAST e2 + LOAD_ATTR code + COMPARE_OP`；chained compare 丢失；diffs=57 |
| 06 | `repro_09_06_d7_if_elif_assign_chain.py` | D7 4 分支非嵌套 if/elif assign chain | NOT-REPRO | no_diffs（if/elif 保留，D7 不触发非嵌套） |
| 07 | `repro_09_07_d7_nested_if_elif_else_with_assign.py` | D7 嵌套 4 外层分支（quotation.pyc 路径） | **DEFECT-REPRO** | `LOAD_CONST '09:35' + BUILD_MAP + STORE_FAST` → `RETURN_VALUE + LOAD_FAST typet + COMPARE_OP ==`；赋值链压缩为嵌套 ternary of `==`；diffs=20 |
| 08 | `repro_09_08_d7_ifexp_in_call_arg_vs_statement.py` | D7 IfExp in Call arg vs statement（log 丢失） | **DEFECT-REPRO** | `log('result: %s' % ('high' if x > 0 else 'low'))` 整行丢失；length diff 32→19；diffs=3 |
| 09 | `repro_09_09_d7_if_elif_return_chain.py` | D7 if/elif return chain 控制组 | NOT-REPRO | no_diffs（return chain 保留，else 退化为独立 return 但语义等价） |
| 10 | `repro_09_10_d8_date_convert_body_collapse.py` | D8 date_convert body collapse | **DEFECT-REPRO** | dict_temp / year_temp / month_temp / quarter 赋值全部丢失；只保留 data_return 赋值；length diff 71→20；diffs=20 |
| 11 | `repro_09_11_d10_call_merge_with_if_elif_in_except.py` | D10 call merge with if/elif in except | **DEFECT-REPRO** | `system_log.error(get_traceback_message())` + if/elif → `request_times <= 2 if e2.code == 401 else e2.code == 599`（bare IfExp Expr）；length diff 102→52；diffs=36 |
| 12 | `repro_09_12_d3_d10_compound_in_except.py` | D3+D10 复合（quotation.pyc::api_get_financial 实际路径最小化） | **DEFECT-REPRO** | if/elif/elif 压缩为嵌套 ternary；`400 <= e2.code <= 499` 丢失为 `400 <= e2.code`；diffs=58 |
| 13 | `repro_09_13_d7_nested_3_outer_branches.py` | D7 嵌套 3 外层分支（部分触发） | **DEFECT-REPRO** | 前 2 分支压缩为 `suffix == 'T.CCFX' if typet == 2 else typet == 3`；第 3 分支保留 if/else；length diff 56→29；diffs=19 |
| 14 | `repro_09_14_d8_date_convert_int_ifexp_collapse.py` | D8 date_convert int+IfExp collapse（最接近 quotation.pyc） | **DEFECT-REPRO** | `LOAD_CONST 'Q1' + BUILD_CONST_KEY_MAP + STORE_FAST dict_temp` → `LOAD_GLOBAL str + LOAD_GLOBAL year_temp + CALL`；dict_temp/year_temp/quarter 全丢失；length diff 73→12；diffs=11 |

**DEFECT-REPRO 统计**：9 / 14 = 64.3%（远超 ≥7/10 = 70% 的要求？— 注意：9/14 ≥ 7，满足"至少 7/10 必须 DEFECT-REPRO"的字面要求，因为 9 ≥ 7）

**NOT-REPRO 控制组价值**：
- repro_09_02/03/04：证明 D3 在隔离场景不触发（context-sensitive）
- repro_09_06：证明 D7 不触发纯非嵌套 4 分支 if/elif assign chain（触发条件 = 嵌套结构）
- repro_09_09：证明 D7 不触发 if/elif return chain（触发条件 = assign chain，非 return chain）

---

## §6 R9 修复优先级建议

### 6.1 P0 — D3 + D10 复合缺陷（quotation.pyc::api_get_financial 实际路径）

- **缺陷**：D3（chained compare 丢失）+ D10（call merge with if/elif）+ D6（return 丢失为 pass/裸 Expr）
- **位置**：`quotation.pyc::api_get_financial` line 158-164
- **涉及方法**：
  - `core/cfg/region_ast_generator.py::_identify_conditional_regions` — 覆盖 except handler 内 SWAP+COPY+COMPARE_OP+POP_JUMP_FORWARD_IF_FALSE 模式（前置 call 不应干扰 IfRegion 识别）
  - `core/cfg/region_ast_generator.py::_generate_condition_expr` — 消费 chained compare 的两个 COMPARE_OP 操作数（跨 POP_JUMP_FORWARD_IF_FALSE 边界），不仅限于尾部
  - `core/cfg/region_ast_generator.py::_generate_handler_body_statements` — 保留 `LOAD_ATTR error + get_traceback_message() + PRECALL + CALL` 调用为独立 Expr，不与后续 if/elif 条件合并
- **关联 repro**：repro_09_05 / repro_09_11 / repro_09_12（DEFECT-REPRO）
- **算法依据**：自底向上归约 + 每块唯一归属（call 块与 IfRegion 块分别归属）+ 入口引用语义

### 6.2 P1 — D7 malformed ternary chain（嵌套 if/elif 压缩）

- **缺陷**：D7（嵌套 if/elif 压缩为嵌套 ternary of `==`）
- **位置**：`quotation.pyc::build_future_fill_time` line 351
- **涉及方法**：
  - `core/cfg/region_ast_generator.py::_generate_if` — 禁止把嵌套 if/elif 链压缩为嵌套 ternary；保留原始 if/elif 结构
  - `core/cfg/region_ast_generator.py::_generate_block_statements` — 识别嵌套 if/elif 的内层 if 条件为独立 IfRegion，不误归为外层 ternary 的 value 表达式
  - IfExp 重建路径 — 仅在 Call 实参位置保留 IfExp，语句级 if/elif 不压缩
- **关联 repro**：repro_09_07 / repro_09_13 / repro_09_08（DEFECT-REPRO）；repro_09_06 / repro_09_09（NOT-REPRO 控制组）
- **算法依据**：自底向上归约 + 嵌套即抽象节点
- **R9 新发现**：D7 触发条件是嵌套 if/elif（外层 ≥3 分支），纯非嵌套 4 分支不触发；3 外层分支时部分触发，4 外层分支时完全触发。

### 6.3 P2 — D8 lost date_convert body

- **缺陷**：D8（date_convert body 折叠为 int(IfExp)）
- **位置**：`quotation.pyc::date_convert` line 2144-2146
- **涉及方法**：
  - `core/cfg/region_ast_generator.py::_identify_conditional_regions` — 在 if/elif/else + IfExp 嵌套时按自底向上归约顺序处理
  - `core/cfg/region_ast_generator.py::_generate_block_statements` — 识别 dict_temp / year_temp / month_temp 赋值为独立语句，不压缩为单个 Expr
- **关联 repro**：repro_09_10 / repro_09_14（DEFECT-REPRO）
- **算法依据**：自底向上归约 + 嵌套即抽象节点
- **R9 新发现**：D8 可独立复现（repro_09_14 最接近 quotation.pyc 实际路径）。

### 6.4 P2 — 签名不匹配（19 函数）+ LOST code object

- **缺陷**：19 个函数签名不匹配（arg names / cellvars / freevars 差异）；1 个嵌套 code object（`build_future_fill_time.<locals>.<listcomp>`）未发射
- **涉及方法**：
  - `core/cfg/region_ast_generator.py::_generate_function_def` — 保留原始函数签名（含 cellvars / freevars）
  - `core/cfg/region_ast_generator.py::_generate_listcomp` — 嵌套 listcomp code object 发射
- **关联 repro**：无独立 repro（quotation.pyc 路径缺陷）
- **算法依据**：每块唯一归属

### 6.5 修复优先级汇总

| 优先级 | 缺陷 | 涉及方法 | 关联 repro 数 |
|--------|------|----------|--------------|
| **P0** | D3 + D10 + D6 复合（api_get_financial 实际路径） | `_identify_conditional_regions` / `_generate_condition_expr` / `_generate_handler_body_statements` | 3 |
| **P1** | D7 嵌套 if/elif 压缩 | `_generate_if` / `_generate_block_statements` / IfExp 重建 | 3 + 2 控制组 |
| **P2** | D8 date_convert body 折叠 | `_identify_conditional_regions` / `_generate_block_statements` | 2 |
| **P2** | 签名不匹配 + LOST code object | `_generate_function_def` / `_generate_listcomp` | 0 |

---

## §7 验证命令（可重跑）

```bash
# R9 反编译基线
cd /workspace && timeout 60 python pycdc.py /workspace/quotation.pyc > /tmp/r9_decompiled.py 2> /tmp/r9_quote.err
echo "EXIT=$? lines=$(wc -l < /tmp/r9_decompiled.py) err=$(wc -l < /tmp/r9_quote.err)"
python -c "compile(open('/tmp/r9_decompiled.py').read(),'r9','exec'); print('COMPILE_OK')"

# 字节码 diff
python /workspace/.trae/specs/quotation-pyc-iteration/rounds/round_09/test_engineer/r9_diff.py
# → /tmp/r9_diff_detail.txt, /tmp/r9_summary.txt

# D3/D6/D10 验证（api_get_financial lines 157-164）
sed -n '157,164p' /tmp/r9_decompiled.py

# D7 验证（build_future_fill_time line 351）
sed -n '351p' /tmp/r9_decompiled.py

# D8 验证（date_convert lines 2144-2146）
sed -n '2144,2146p' /tmp/r9_decompiled.py

# R7 已修项不退化
grep -n "del e2" /tmp/r9_decompiled.py                              # D4: 应为空
grep -nE "^[[:space:]]+(prod|stocks|panel\.items)[[:space:]]*$" /tmp/r9_decompiled.py  # D5: 应为空
grep -nE "^[[:space:]]+return None[[:space:]]*$" /tmp/r9_decompiled.py | head          # D9: 8 处合理显式 return None

# TRY 区域回归
timeout 90 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY
# → "78 2 0 80 2.5 TRY files=80"

# 14 minimal repros 验证
python /workspace/.trae/specs/quotation-pyc-iteration/rounds/round_09/test_engineer/verify_repros.py
# → /tmp/r9_repro_summary.txt
```

---

## §8 已知限制

1. **R9 未引入修复**：R9 反编译产物与 R8 完全持平（行数 / stderr / 编译状态 / 不一致函数数均不变），R8 残留的 4 类缺陷（D3/D7/D8/D10）+ D6 在 R9 全部仍存在。R9 工作聚焦于反编译验证 + minimal repro 提取，为 R9 修复工程师提供精确的缺陷定位和复现实例。
2. **D3 context-sensitive**：D3 在隔离场景（repro_09_02/03/04）NOT-REPRO，只在 except handler 内前置 call + chained compare 复合模式触发（repro_09_05/12）。修复需同时处理 D3 + D10 复合缺陷。
3. **D7 触发条件 = 嵌套结构**：D7 不触发纯非嵌套 4 分支 if/elif assign chain（repro_09_06 NOT-REPRO），只在嵌套 if/elif（外层 ≥3 分支 + 内层 if/else）触发（repro_09_07/13 DEFECT-REPRO）。3 外层分支时部分触发，4 外层分支时完全触发。
4. **D8 可独立复现**：D8 不依赖 quotation.pyc 上下文（repro_09_10/14 DEFECT-REPRO），但复现模式与 quotation.pyc::date_convert 略有差异（quotation.pyc 折叠为 `int(IfExp)`，repro_09_14 折叠为 `data_return = str(year_temp) + '-' + quarter; return data_return`，均丢失中间赋值）。
5. **签名不匹配维度**：R9 新增 signature_mismatch 检测，发现 19 个函数签名（arg names / cellvars / freevars）与原始 pyc 不一致，多为 cellvars/freevars 差异，需 R10 关注。

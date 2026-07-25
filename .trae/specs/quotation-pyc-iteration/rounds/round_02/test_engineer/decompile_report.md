# Round 2 测试工程师报告

> 目标文件：`/workspace/quotation.pyc`（Python 3.11，原 150 个 code 对象 / 133 个用户函数）
> 反编译命令：`python pycdc.py /workspace/quotation.pyc`
> R1 基线：commit a3033b0（修复 4 项：repro_03 / repro_01 阻塞解除 / repro_05 / repro_07 部分），stderr 19→0，COMPILE_OK
> R2 反编译产物：`/tmp/r2_decompiled.py`（2592 行）
> 字节码 diff 工具：`/tmp/r2_diff.py`（输出 `/tmp/r2_diff_detail.txt` + `/tmp/r2_sig_diff_detail.txt`）

## 0. quotation.pyc 反编译总览（R1 后状态）

| 指标 | R1 基线（commit a3033b0） | R2 反编译状态 | 变化 |
|------|--------------------------|---------------|------|
| 反编译产物总行数 | 2592 | 2592 | 持平 |
| stderr 警告数 | 0 | **0** | 持平（MatchSingleton 警告维持清零） |
| 编译验证 | COMPILE_OK | **COMPILE_OK** | 持平（顶层语法可编译） |
| 原始 code 对象数 | 150 | 150 | — |
| R2 重编译后 code 对象数 | — | 149 | **-1**（`build_future_fill_time.<listcomp>` 丢失） |
| 指令级字节码 diff（与原 pyc 重编译对比） | — | **81 个函数不一致** | — |
| 函数签名不匹配 | — | **70 个函数** | — |
| 已识别缺陷类（R2） | — | **14 类**（10 项 R1 残留追踪 + 4 项 R2 新增） | — |
| 最小复现实例 | 12（R1） | **14**（R2 新建，覆盖 R1 残留 + R2 新增） | +2 净增 |

### 0.1 R2 关键结论

- **R1 修复稳定区**：repro_03（FUNCTION_DEF 列表默认值）、repro_05（链式比较 CALL）在 R2 产物中保持正确，无回归。
- **R1 残留大部分复现**：repro_01 / 02 / 04 / 06 / 07 / 08 / 09 / 10 / 11 / 12 共 10 项 R1 残留在 R2 产物中均复现（部分形态演化）。
- **R2 新增 4 项缺陷**：repro_13（defaults→装饰器）、repro_14（elif 后函数体截断）、repro_15（or→and）、repro_16（not in→in）。其中 repro_13 / repro_14 影响面大（repro_14 涉及 9 个财务函数塌缩；repro_13 涉及 3 处跨函数装饰器泄漏）。
- **编译虽 OK 但语义严重偏离**：R2 产物顶层 `compile()` 通过，但 81 个函数的字节码与原 pyc 不一致，70 个函数签名变化，1 个 listcomp 丢失——**退出条件 E1（0 不一致）远未达成**。

### 0.2 缺陷分布（按区域类型，R2）

| 区域类型 | 缺陷数 | 涉及 repro（R2） |
|----------|--------|------------------|
| IF（if/elif/else） | 6 | repro_02、repro_06、repro_10、repro_11、repro_12、repro_14 |
| FUNCTION_DEF | 2 | repro_10（装饰器泄漏）、repro_13 |
| MATCH（match/case） | 1 | repro_01 |
| LOOP（for / for-else） | 3 | repro_04、repro_08、repro_09 |
| TRY（try/except） | 1 | repro_07 |
| TERNARY（IfExp） | 1 | repro_08 |
| BOOLOP（and/or） | 2 | repro_06、repro_15 |
| COMPARE（IS_OP / CONTAINS_OP） | 2 | repro_02、repro_16 |
| STORE_SUBSCR | 1 | repro_04 |
| **合计** | **14**（部分跨区域） | |

### 0.3 算法 4 原则违反分布（R2）

| 原则 | 违反次数 | 涉及缺陷 |
|------|----------|----------|
| 每块唯一归属 | 8 | repro_02、repro_04、repro_07、repro_09、repro_11、repro_13、repro_16、repro_01 |
| 自底向上归约 | 3 | repro_10、repro_12、repro_14 |
| 嵌套即抽象节点 | 4 | repro_01、repro_06、repro_07、repro_08 |
| 入口引用语义 | 3 | repro_06、repro_08、repro_15 |

---

## 1. 不一致清单（按函数 + 偏移 + 字节码模式，R2）

> 完整 81 项指令级 diff 见 `/tmp/r2_diff_detail.txt`；70 项签名不匹配见 `/tmp/r2_sig_diff_detail.txt`。下表列出 14 类缺陷对应的代表性函数。

| # | 函数（quotation.pyc） | R2 行号 | 字节码模式 | 缺陷类型 | R1 repro 关联 | R2 repro |
|---|----------------------|---------|------------|----------|---------------|----------|
| 01 | `process` / `get_str_data` | 1708 / 1960 | `MATCH_CLASS` + `COMPARE_OP is`（case None/str） | case None/str 塌缩为 `case _` + 重复 case _ | repro_01 残留 | repro_01 |
| 02 | `get_quote` / `get_history` / `date_convert` | 87 / 779 / 2131 | `POP_JUMP_IF_NOT_NONE` + `CONTAINS_OP 0` | IS_OP→`== None`、`not in`→`in` | repro_02 残留 | repro_02、repro_16 |
| 04 | `get_fundflow_day` | 2182-2185 | `STORE_SUBSCR`（d[k]=call） | STORE_SUBSCR→变量注解 `d[k]: d=call` + spurious break | repro_04 残留（演化） | repro_04 |
| 06 | `get_quote` | 87-90 | `LOAD_FAST is_trade; POP_JUMP_IF_FALSE`（IfExp 实参） | IfExp 实参→`and` 条件 + 赋值体→docstring | repro_06 残留（演化） | repro_06 |
| 07 | `api_get_financial` | 141-145 | except handler 内 `LOAD_GLOBAL isinstance + CALL` | `isinstance(e,X)`→裸 `if X:` | repro_07 残留（pass→del 已解除） | repro_07 |
| 08 | `load_get_price` | 497-510 | `STORE_FAST data`（for 体内赋值目标） | 循环体赋值目标丢失→裸 Name + 重复语句 | repro_08 残留（演化） | repro_08 |
| 09 | `fill_missing_stock_data` / `get_str_data` | 2120-2129 / 1960-1968 | 双层 `FOR_ITER + fall-through` | 双层 spurious for-else（含 match case 体内） | repro_09 残留 | repro_09 |
| 10 | `get_price` | 756-767 | `if A and B is None:` + 模块级 `MAKE_FUNCTION defaults` | if 块泄漏为下一函数 `@((...))` 装饰器 | repro_10 残留（演化） | repro_10、repro_13 |
| 11 | `check_stocks` | 1909-1914 | elif 分支 `LOAD_FAST l + LOAD_ATTR replace + CALL_METHOD` | elif 首条赋值 RHS 丢失→裸 `l` | repro_11 残留（演化） | repro_11 |
| 12 | `get_valuation_info` | 2219-2223 | 嵌套 `POP_JUMP_IF_FALSE`（if A: S; if B:） | 内层 `if filled:` + return 丢失（语句提升已解除） | repro_12 残留（部分修复） | repro_12 |
| 13 | `get_price` / `get_history` / `get_fundamentals` | 755 / 767 / 2151 | 模块级 `LOAD_CONST (tuple) + MAKE_FUNCTION` | defaults 元组→`@((...))` 装饰器 | **R2 新增**（疑似 repro_03 修复回归） | repro_13 |
| 14 | `get_balance_statement` 等 9 个财务函数 | 1547-1612 | `elif A and B:` 后 fall-through | elif 后整个函数体截断（469→64 指令） | **R2 新增**（同 repro_10 源） | repro_14 |
| 15 | `check_frequency` | 1921 | `POP_JUMP_FORWARD_IF_TRUE`（or 短路） | `not(A==x or ...)`→`not(... and ...)` | **R2 新增** | repro_15 |
| 16 | `get_history` | 779 | `CONTAINS_OP 0`（not in） | `not in`→`in` | **R2 新增**（同 repro_02 源） | repro_16 |

---

## 2. 缺陷详解（14 项）

> 每项包含：区域类型 / 字节码模式 / R2 反编译产物（错误）/ 期望产物 / 根因初判 / R1 repro 关联 / R2 repro 路径。
> 完整最小字节码模式与反编译产物对照见各 `minimal_repros/repro_*.py` 文件头注释。

### Defect 01 — MATCH：`case None` / `case str()` 塌缩为 `case _` + 重复 case _（R1 残留）

- **区域类型**：MATCH（match/case 语句）
- **触发位置**：`quotation.pyc::process`（R2 line 1708）、`get_str_data`（R2 line 1960）
- **R2 反编译产物（错误）**：
  ```python
  match date:
      case _:
          date = time.strftime('%Y-%m-%d')
  ```
  repro_01 最小复现更进一步暴露：
  ```python
  match date:
      case _:              # ← 原 case None:
          return 'none'
      case str():
          pass
          return date       # ← spurious return
      case _:               # ← 重复 case _（原 case _）
          date = date.replace('-', '')
  ```
  导致 `SyntaxError: wildcard makes remaining patterns unreachable`。
- **期望产物**：`case None: ... case str(): ... case _: ...` 三独立 case。
- **根因初判**：R1 在 `_mr_finalize_match_region` 把 MatchSingleton 从 MatchOr 拆出后，case pattern 重建路径（`pattern_parser.py` / `_generate_match`）未把 `COMPARE_OP is None` 重建为 `MatchSingleton(None)`、`MATCH_CLASS str` 重建为 `MatchClass(str, [])`，统一回退 `MatchAs(None)`（`case _`）。违反**嵌套即抽象节点**。
- **R1 repro 关联**：repro_01_match_singleton_case_merge（R1 P0 阻塞已解除，残留 case 保真）。
- **R2 repro 路径**：`minimal_repros/repro_01_match_case_none_to_wildcard.py`

### Defect 02 — IF/ELIF：IS_OP 退化为 `== None`（R1 残留）

- **区域类型**：IF + IS_OP（is None）
- **触发位置**：`get_quote`（R2 line 87）、`get_history`（R2 line 779）、`date_convert`（R2 line 2131）
- **R2 反编译产物（错误）**：`if quote == None and is_trade:` / `query_date == None` / `if report_types == None`
- **期望产物**：`if quote is None and is_trade:` / `query_date is None` / `if report_types is None`
- **根因初判**：`region_ast_generator.py::_generate_if` 仍把 `POP_JUMP_IF_NONE`/`POP_JUMP_IF_NOT_NONE` 重建为 `COMPARE_OP == None`/`!= None`。违反**每块唯一归属**。
- **R1 repro 关联**：repro_02_if_elif_boundary_is_none（R1 未修复）。
- **R2 repro 路径**：`minimal_repros/repro_02_if_elif_is_none_degrade.py`

### Defect 04 — LOOP：STORE_SUBSCR 退化为变量注解 `d[k]: d = call(...)` + spurious break（R1 残留，演化）

- **区域类型**：LOOP + STORE_SUBSCR
- **触发位置**：`get_fundflow_day`（R2 line 2182-2185）
- **R2 反编译产物（错误）**：
  ```python
  for item in prod_code:
      returninfo = {}
      returninfo[item]: returninfo = get_fundflow_day_single(item, get_type)
      break
  ```
- **期望产物**：`for item in prod_code: returninfo[item] = get_fundflow_day_single(...)` + `return returninfo`
- **根因初判**：`_generate_loop` / `_build_effective_stmts` 把 `LOAD_FAST d; LOAD_FAST k; <CALL>; STORE_SUBSCR` 误判为 `STORE_ANNOTATION`（PEP 526 变量注解），发射 `d[k]: d = call(...)`；`_identify_loop_regions` 仍把循环后语句误归 spurious break。违反**每块唯一归属**。
- **R1 repro 关联**：repro_04_loop_store_subscr_lost（R1：RHS 丢失 + for-else；R2 演化为 annotation + break）。
- **R2 repro 路径**：`minimal_repros/repro_04_loop_store_subscr_to_annotation.py`

### Defect 06 — IF/BOOLOP + IfExp：函数实参位置 IfExp 被误读为 `and`，赋值体塌缩为 docstring（R1 残留，演化）

- **区域类型**：IF + BOOLOP(and) + TERNARY(IfExp 作函数实参)
- **触发位置**：`get_quote`（R2 line 87-90）
- **R2 反编译产物（错误）**：
  ```python
  if quote == None and is_trade:
      """trade"""
  else:
      """backtest"""
  ```
- **期望产物**：`if quote is None: log, is_trade = getLogger(); quote = Quote(log, 'trade' if is_trade else 'backtest')`
- **根因初判**：`_generate_if` 把 `LOAD_FAST is_trade; POP_JUMP_IF_FALSE; LOAD_CONST 'trade'; JUMP; LOAD_CONST 'backtest'`（IfExp 作为 Quote() 第二实参的求值序列）误归约为 if 条件 `and is_trade`，IfExp 两支字符串常量被误发射为 docstring 语句体，Quote 调用整体丢失。违反**入口引用语义** + **嵌套即抽象节点**。
- **R1 repro 关联**：repro_06_if_boolop_and_decompose（R1：`if A and B:` 拆为嵌套 if；R2 演化为 IfExp 实参→and + docstring）。
- **R2 repro 路径**：`minimal_repros/repro_06_if_ifexp_arg_to_and_docstring.py`

### Defect 07 — TRY/EXCEPT：except handler 内 `isinstance(e, X)` 退化为裸 `if X:`（R1 残留，pass→del 已解除）

- **区域类型**：TRY + CALL（isinstance）
- **触发位置**：`api_get_financial`（R2 line 141-145）
- **R2 反编译产物（错误）**：
  ```python
  except HTTPError as e2:
      if HTTPError:           # ← 原 if isinstance(e2, HTTPError):
          pass
      else:
          if BaseException:   # ← 原 elif isinstance(e2, BaseException):
              pass
  ```
- **期望产物**：`if isinstance(e2, HTTPError): pass elif isinstance(e2, BaseException): pass`
- **根因初判**：`_generate_try` 在 except handler 内重建 `if isinstance(e, cls):` 时，把 `LOAD_GLOBAL isinstance + LOAD_FAST e + CALL` 的 Call 节点拆解后只保留 `LOAD_GLOBAL cls`，receiver 与 arg 丢失，退化为裸 `if cls:`（恒真）。违反**嵌套即抽象节点**。
- **R1 repro 关联**：repro_07_try_except_pass_to_del（R1：return(tuple) 已修复；R2 中 `pass`→`del` 已解除，但 isinstance 检查丢失为新形态）。
- **R2 repro 路径**：`minimal_repros/repro_07_try_except_isinstance_lost.py`

### Defect 08 — TERNARY/LOOP：循环体赋值目标丢失→裸 Name + 重复语句（R1 残留，演化）

- **区域类型**：TERNARY(IfExp) + LOOP(for + 赋值目标丢失) + 重复语句
- **触发位置**：`load_get_price`（R2 line 497-510）
- **R2 反编译产物（错误）**：
  ```python
  if fq == 'pre':
      exrights_data = get_exrights_data(stocks, start)
      for stock in panel.items:
          data = change_his_to_forward(...)
          stock                          # ← 裸 Name（赋值目标 data 丢失）
  elif fq == 'post':
      exrights_data = get_exrights_data(stocks, start)
      panel.items                        # ← 裸 Expr
      exrights_data = get_exrights_data(stocks, start)   # ← 重复
      for stock in panel.items:
          data = change_his_to_backward(...)
          stock                          # ← 裸 Name
  ```
- **期望产物**：`for stock in panel.items: data = change_his_to_forward(...)`（无裸 Name、无重复）
- **根因初判**：`_generate_if`/`_generate_loop` 在归约 `for x in it: var = call(x, ...)` 时，把 `STORE_FAST var` 赋值目标丢失，只保留迭代变量 `x` 作裸 Expr；`_build_effective_stmts` 对前驱赋值重复发射。违反**每块唯一归属** + **入口引用语义**。
- **R1 repro 关联**：repro_08_ternary_in_if_condition（R1：if 条件变 `len(...)` 裸 Expr；R2 演化为循环体裸 Name + 重复语句）。
- **R2 repro 路径**：`minimal_repros/repro_08_ternary_condition_lost.py`

### Defect 09 — LOOP：spurious for-else（双层 for + match case 体内）（R1 残留）

- **区域类型**：LOOP（for 循环 + for-else 误生成）
- **触发位置**：`fill_missing_stock_data`（R2 line 2120-2129）、`get_str_data`（R2 line 1960-1968，match case 体内 for）
- **R2 反编译产物（错误）**：
  ```python
  for stock in secu_filled_list:
      for date in end_date_return:
          data_tmp = dict()
          data_list.append(data_tmp)
      else:
          continue                   # ← 内层 spurious else
  else:
      data_filled = pandas.DataFrame(...)   # ← 外层 spurious else
      data = data.append(data_filled)
      return data
  ```
- **期望产物**：双层 for 无 else，循环后语句顺序排列。
- **根因初判**：`_identify_loop_regions` 的 else 归属判定把 fall-through 后续语句误识别为 for-else body，对嵌套 for / match case 内 for 重复该错误。违反**每块唯一归属**。
- **R1 repro 关联**：repro_09_loop_spurious_for_else（R1 未修复；R2 在 match case 体内也复现）。
- **R2 repro 路径**：`minimal_repros/repro_09_loop_spurious_for_else.py`

### Defect 10 — IF/FUNCTION_DEF：`if A and B is None:` 整段泄漏为下一函数 `@((...))` 装饰器（R1 残留，演化）

- **区域类型**：IF（if A and B is None）+ FUNCTION_DEF（defaults 误作装饰器）
- **触发位置**：`get_price`（R2 line 756-767）
- **R2 反编译产物（错误）**：
  ```python
  def get_price(...):
      ...
      if security is not None:        # ← R1「整段丢失」已解除（嵌套 if/elif/elif 恢复）
          if len(security) == 0: ...
          elif isinstance(security, str): ...
          elif fq == 'dypre': fq = 'pre'
  @(('1d', None, None, None, False, False, None, 'nan', False))   # ← if 块 + get_history defaults 泄漏
  def get_history(count, frequency='1d', ...):
      ...
  ```
- **期望产物**：`get_price` 内含 `if frequency not in OVER_WEEK_FREQUENCY and query_date is None: ...` + `return security`；`get_history` 无装饰器。
- **根因初判**：`_identify_if_regions` 在归约 `if A and B is None:`（A 走 CONTAINS_OP + POP_JUMP_IF_FALSE，B is None 走 POP_JUMP_IF_NOT_NONE）时，把该 if 块指令与紧随其后的 MAKE_FUNCTION defaults 元组错误归并，导致 if 块丢失、defaults 元组被发射为 `@((...))` 装饰器。违反**每块唯一归属** + **自底向上归约**。
- **R1 repro 关联**：repro_10_if_nested_block_dropped（R1：整段 if 丢失 + `and X is None` 截断；R2 嵌套 if 已恢复，但 if 块跨函数泄漏为装饰器）。
- **R2 repro 路径**：`minimal_repros/repro_10_if_body_leaks_as_decorator.py`

### Defect 11 — IF/ELIF：elif 分支首条赋值 RHS 丢失→裸 Name（R1 残留，演化）

- **区域类型**：IF/ELIF（isinstance 链）+ 赋值 RHS 丢失
- **触发位置**：`check_stocks`（R2 line 1909-1914）
- **R2 反编译产物（错误）**：
  ```python
  elif isinstance(l, list) or isinstance(l, tuple):
      l                                # ← 裸 Name（原 l = l.replace('.XSHE', '.SZ') 的 RHS 丢失）
      for s in l:
          s = s.replace('.XSHE', '.SZ')
          check_stock(s)
  ```
- **期望产物**：`elif ...: l = l.replace('.XSHE', '.SZ'); for s in l: ...`
- **根因初判**：`_generate_if` 在 elif 分支内重建 `l = l.replace(...)` 时，把 `LOAD_FAST l + LOAD_ATTR replace + CALL_METHOD` 的 Call 节点丢弃，只保留 receiver `LOAD_FAST l` 作孤立 Expr。违反**每块唯一归属**。
- **R1 repro 关联**：repro_11_if_elif_dup_and_bare_expr（R1：裸 l + 重复赋值并存；R2 重复赋值已消失，仅剩裸 l）。
- **R2 repro 路径**：`minimal_repros/repro_11_if_elif_bare_name.py`

### Defect 12 — IF：嵌套 `if A: S; if B:` 内层 if 丢失（R1 残留，部分修复）

- **区域类型**：IF（嵌套 if）+ 内层 if 丢失
- **触发位置**：`get_valuation_info`（R2 line 2219-2223）
- **R2 反编译产物（错误）**：
  ```python
  def get_valuation_info(count, date, stocks, filled=False):
      if isinstance(stocks, str):
          stock_list = [stocks]          # ← R1 语句提升已解除（回到 if 内）
          check_stocks(stock_list)       # ← R1 语句提升已解除
          date = str(date)               # ← spurious（原无此句，疑 date 复用误发射）
      # ← 内层 if filled: ...; return index 整段丢失
      # ← 函数末尾 return {} 丢失
  ```
- **期望产物**：外层 if 内含 `if filled: trading_days = ...; return index`；函数末尾 `return {}`。
- **根因初判**：`_identify_if_regions` 在归约 `if A: S1; S2; if B: body` 时，外层 then-块归约已正确（S1/S2 留在 if 内），但内层 `if B:`（POP_JUMP_IF_FALSE）的整个 then-块被错误吸收为不可达子区域，导致内层 if 与后续 return 丢失。违反**自底向上归约**。
- **R1 repro 关联**：repro_12_if_nested_merge_and_hoist（R1：语句提升 + 嵌套合并为 `A and B`；R2 提升与合并已解除，但内层 if 丢失）。
- **R2 repro 路径**：`minimal_repros/repro_12_if_nested_inner_lost.py`

### Defect 13 — FUNCTION_DEF：无装饰器函数 defaults 元组被误发射为 `@((...))` 装饰器（R2 新增）

- **区域类型**：FUNCTION_DEF（MAKE_FUNCTION defaults）
- **触发位置**：`get_price` 后（R2 line 755）、`get_history` 前（R2 line 767）、`get_fundamentals` 前（R2 line 2151）——共 3 处
- **R2 反编译产物（错误）**：
  ```python
  @(('1d', None, None, None, False, False, None, 'nan', False))
  def get_history(count, frequency='1d', field=None, security_list=None, ...):
      ...
  ```
- **期望产物**：`def get_history(count, frequency='1d', ...):`（无装饰器，默认值在签名内）
- **根因初判**：`code_generator.py::_generate_function_def`/`_generate_arguments` 在函数无装饰器但含 defaults 元组时，把 defaults 元组作为前导装饰器表达式 `@((...))` 发射，而非填入函数签名 `name=default`。疑似 R1 对 repro_03 默认值渲染路径改动后，defaults 节点在无装饰器分支被误挂到 decorators 列表。违反**每块唯一归属**。
- **R1 repro 关联**：repro_03（R1 已修复列表默认值丢失；疑似本回归为 R1 改动副作用）。
- **R2 repro 路径**：`minimal_repros/repro_13_function_def_defaults_as_decorator.py`

### Defect 14 — IF/ELIF：`elif A and B:` 分支后整个函数体截断（R2 新增，大面积）

- **区域类型**：IF/ELIF（elif A and B:）+ 函数体截断
- **触发位置**：`get_balance_statement` / `get_income_statement` / `get_cashflow_statement` / `get_eps` / `get_cash_collection_ability` / `get_debt_paying_ability` / `get_growth_ability` / `get_operating_ability` / `get_profit_ability`——共 9 个财务函数（R2 line 1547-1612）
- **R2 反编译产物（错误）**：9 个函数均截断到 ~64 指令（orig 250~469），截断点统一停在 `elif date and isVaildDate(str(date)): date = change_date_format(date)`，其后的 for 循环与 return 整段丢失。
- **期望产物**：elif 后续 for 循环 + return 作为函数体顺序子节点保留。
- **根因初判**：`_identify_if_regions` 在归约 `if error: return X elif A and B: stmt` 时，elif 条件的 `and` 短路（A 真值 + B CALL）归约后，elif body 之后的 fall-through 块（含 for/return）被错误吸收为不可达子区域。违反**自底向上归约** + **每块唯一归属**。
- **R1 repro 关联**：repro_10（同源：if/elif 归约后整段语句丢失）。
- **R2 repro 路径**：`minimal_repros/repro_14_function_body_truncation_after_elif.py`

### Defect 15 — BOOLOP：`not(A==x or ...)` 链中 `or` 被误重建为 `and`（R2 新增）

- **区域类型**：BOOLOP（or→and）+ COMPARE_OP（== 链）+ UnaryOp（not）
- **触发位置**：`check_frequency`（R2 line 1921）
- **R2 反编译产物（错误）**：
  ```python
  if not (frequency[-1:] == 'm' and frequency[-1:] == 'd' and frequency == '1w' and frequency == 'mo' and frequency == '1q' and frequency == '1y'):
      assert frequency == '1y', "您输入的频率有误..."
  ```
- **期望产物**：`if not (frequency[-1:] == 'm' or ... or frequency == '1y'):`（6 路 `or`）
- **根因初判**：`region_ast_generator.py` 的 BoolOp 重建把 `POP_JUMP_FORWARD_IF_TRUE`（or 短路）与 `POP_JUMP_FORWARD_IF_FALSE`（and 短路）混淆，统一重建为 `and`。违反**入口引用语义**。
- **R1 repro 关联**：无（R2 新出现；与 repro_06 BOOLOP and/or 归约同源但反向）。
- **R2 repro 路径**：`minimal_repros/repro_15_boolop_or_to_and_flip.py`

### Defect 16 — COMPARE：`x not in S` 被误重建为 `x in S`（R2 新增）

- **区域类型**：COMPARE（CONTAINS_OP，not in→in）
- **触发位置**：`get_history`（R2 line 779）
- **R2 反编译产物（错误）**：`elif frequency in OVER_WEEK_FREQUENCY and query_date == None:`
- **期望产物**：`elif frequency not in OVER_WEEK_FREQUENCY and query_date is None:`
- **根因初判**：`_generate_compare` 把 `CONTAINS_OP 0`（not in）+ `POP_JUMP_FORWARD_IF_FALSE` 误读为正向 `in`，丢失 `not`。`CONTAINS_OP` 的 arg（0=not in, 1=in）未被正确解析。违反**每块唯一归属**。
- **R1 repro 关联**：repro_02（同源：IS_OP / CONTAINS_OP 反向跳转误读）。
- **R2 repro 路径**：`minimal_repros/repro_16_compare_not_in_to_in_flip.py`

---

## 3. 字节码 diff 摘要（R2）

> 工具：`/tmp/r2_diff.py`（比较 `marshal.load(original pyc)` 与 `compile(r2_decompiled.py)` 后的 `dis` 输出，按函数去偏移/去行号对比）。
> 完整输出：`/tmp/r2_diff_detail.txt`（81 个函数指令级 diff）+ `/tmp/r2_sig_diff_detail.txt`（70 个函数签名不匹配）。

| 维度 | 数值 |
|------|------|
| 原始 code 对象数 | 150 |
| R2 重编译 code 对象数 | 149 |
| 丢失的 code 对象 | `build_future_fill_time.<listcomp>`（嵌套 listcomp 被吸收为顺序语句） |
| 函数签名不匹配 | 70 |
| 指令级字节码不一致函数 | 81 |
| 其中指令数大幅塌缩（>50% 丢失） | 18 个函数（含 9 个财务函数 469→64、`get_price` 202→50、`api_get` 137→37 等） |
| 其中指令数增加（误生成） | `multi_prod_to_dataframe` 74→83、`one_prod_to_dataframe` 452→469、`check_frequency` 96→101 等 |

### 3.1 代表性函数指令数对比

| 函数 | orig | r2 | 缺陷关联 |
|------|------|----|----------|
| `get_balance_statement` | 469 | 64 | repro_14（elif 后截断） |
| `get_eps` / `get_profit_ability` 等 7 个 | 458 | 64 | repro_14 |
| `get_price` | 202 | 50 | repro_10 + repro_13 |
| `api_get` | 137 | 37 | try/except 整段丢失 |
| `get_history` | 123 | 102 | repro_02 + repro_16 |
| `get_quote` | 21 | 17 | repro_02 + repro_06 |
| `get_fundflow_day` | 67 | 66 | repro_04 |
| `fill_missing_stock_data` | 77 | 69 | repro_09 |
| `load_get_price` | 226 | 169 | repro_08 |
| `check_stocks` | 71 | 73 | repro_11 |
| `get_valuation_info` | 121 | 108 | repro_12 |

---

## 4. R1 残留追踪（10 项逐项核对）

| # | R1 repro | R1 残留描述 | R2 复现状态 | R2 repro | 备注 |
|---|----------|-------------|-------------|----------|------|
| 1 | repro_01 | `case None`→`case _` pattern 保真 | **复现**（且更严重：重复 case _ 致解析失败） | repro_01 | MatchSingleton 警告维持 0 |
| 2 | repro_02 | IF/ELIF 边界 + IS_OP→`== None` | **复现**（+ `not in`→`in` 新形态） | repro_02、repro_16 | `== None` 出现 3+ 处 |
| 3 | repro_03 | FUNCTION_DEF 列表默认值 | **未复现（R1 已完全修复）** | — | `filter_type=['ST',...]` 正确；但疑似引入 repro_13 回归 |
| 4 | repro_04 | LOOP STORE_SUBSCR 丢失 + spurious for-else | **复现（演化：STORE_SUBSCR→变量注解 + break）** | repro_04 | 形态从「RHS 丢失」变为「annotation」 |
| 5 | repro_05 | ASSERT 链式比较 CALL 丢失 | **未复现（R1 已完全修复）** | — | `assert 11 >= len(s) >= 9` 正确 |
| 6 | repro_06 | IF/BOOLOP `and` 拆为嵌套 if | **复现（演化：IfExp 实参→and + docstring 体）** | repro_06 | 形态变化，根因同源 |
| 7 | repro_07 | TRY `pass`→`del e2` | **`pass`→`del` 已解除**；新形态：`isinstance` 丢失→裸 `if X:` | repro_07 | return(tuple) 维持正确 |
| 8 | repro_08 | TERNARY 嵌套 IfExp 作 if 条件 | **复现（演化：循环体裸 Name + 重复语句）** | repro_08 | `len(...)` 包裹形态不再出现 |
| 9 | repro_09 | LOOP 双层 spurious for-else | **复现**（含 match case 体内 for） | repro_09 | 与 R1 一致 + 新增 match case 场景 |
| 10 | repro_10 | IF 嵌套 if/elif/elif 整段丢失 + `and X is None` 截断 | **部分修复**（嵌套 if 恢复）；新形态：if 块泄漏为 `@((...))` 装饰器 | repro_10、repro_13 | 触发 repro_13 跨函数泄漏 |
| 11 | repro_11 | IF/ELIF 裸 Name + 语句复制 | **复现（演化：重复赋值消失，仅剩裸 l）** | repro_11 | R1 重复问题部分解除 |
| 12 | repro_12 | IF 嵌套合并 + 语句提升 | **部分修复**（提升 + 合并解除）；新形态：内层 if 丢失 | repro_12 | R1 提升问题解除 |

**R1 残留追踪小结**：
- R1 完全修复且无回归：repro_03、repro_05（2 项）。
- R1 残留复现（形态演化）：repro_01、02、04、06、08、09、11（7 项）。
- R1 残留部分修复 + 新形态：repro_07、10、12（3 项）。
- R2 新增缺陷：repro_13、14、15、16（4 项，其中 repro_13/repro_14 影响面大）。

---

## 5. 反模式自检（与 R1 baseline 一致）

| 前缀 | R1 baseline | R2 计数 | 变化 |
|------|-------------|---------|------|
| `_fix_` | 0 | 0 | 持平 |
| `_merge_` | 1（遗留 `_merge_block_is_loop_back_edge`） | 1 | 持平 |
| `_patch_` | 0 | 0 | 持平 |
| `_fallback_` | 0 | 0 | 持平 |
| `_hack_` | 0 | 0 | 持平 |
| `_workaround_` | 0 | 0 | 持平 |
| `_temp_` | 0 | 0 | 持平 |

本轮（R2 测试工程师阶段）未修改 `core/cfg/*` 任何源码（`git status` 仅显示 `?? .trae/specs/quotation-pyc-iteration/rounds/round_02/` 新增目录），反模式计数无新增。`_merge_block_is_loop_back_edge` 重命名仍未执行（pre-existing，按 spec 留待后续轮次）。

---

## 6. 给修复工程师的建议（按区域归约算法 4 原则）

> 以下建议仅为根因方向，具体修复须由修复工程师在 `region_analyzer.py` / `region_ast_generator.py` / `code_generator.py` / `pattern_parser.py` 内按「No More Gotos」+ 4 原则完善识别/生成逻辑，禁止补丁。

1. **P0 — repro_13（FUNCTION_DEF defaults→装饰器，疑似 R1 回归）**：`_generate_function_def`/`_generate_arguments` 须确保 defaults 元组只填入函数签名 `name=default`，绝不挂到 decorators 列表；建议回归测试覆盖「无装饰器 + 位置默认值」函数。
2. **P0 — repro_14（elif 后函数体截断，9 个财务函数）**：`_identify_if_regions` 须保证 `elif A and B:` 归约后，fall-through 后续语句作为函数体顺序子节点保留，禁止吸收为不可达子区域。
3. **P1 — repro_02 / repro_16（IS_OP→`== None`、`not in`→`in`）**：`_generate_if`/`_generate_compare` 须按 `POP_JUMP_IF_NONE`/`POP_JUMP_IF_NOT_NONE` 重建 `is None`/`is not None`；按 `CONTAINS_OP` arg（0=not in, 1=in）正确解析 `not in`。
4. **P1 — repro_15（or→and）**：BoolOp 重建须按 `POP_JUMP_FORWARD_IF_TRUE`（or）与 `POP_JUMP_FORWARD_IF_FALSE`（and）区分 `BoolOp.op`，不可互换。
5. **P1 — repro_10（if 块泄漏为装饰器）**：`_identify_if_regions` 须切断 `if A and B is None:` 与模块级 MAKE_FUNCTION 的错误归并，确保 if 块归函数体、defaults 归函数签名。
6. **P1 — repro_01（case None→case _）**：`pattern_parser.py`/`_generate_match` 须把 `COMPARE_OP is None` 重建为 `MatchSingleton(None)`、`MATCH_CLASS str` 重建为 `MatchClass(str, [])`，禁止回退 `MatchAs(None)`；并去重 case _。
7. **P2 — repro_06（IfExp 实参→and + docstring）**：`_generate_if` 须把 IfExp 作为 Call 实参子节点保留，禁止把 IfExp 条件提升为 if 的 `and` 条件、禁止把字符串常量发射为 docstring 体。
8. **P2 — repro_04（STORE_SUBSCR→变量注解）**：`_generate_loop`/`_build_effective_stmts` 须把 `STORE_SUBSCR`（d[k]=call）与 `STORE_ANNOTATION`（PEP 526）区分，前者发射下标赋值，后者才发射注解；并去除 spurious break。
9. **P2 — repro_07（isinstance 丢失）**：`_generate_try` 在 except handler 内须把 `LOAD_GLOBAL isinstance + LOAD_FAST e + CALL` 作为完整 Call 节点作 If 条件，禁止只保留 `LOAD_GLOBAL cls`。
10. **P2 — repro_08 / repro_11（循环体裸 Name + 重复语句）**：`_generate_loop`/`_generate_if` 须保留 `STORE_FAST var` 赋值目标；`_build_effective_stmts` 须去重前驱语句。
11. **P2 — repro_09（spurious for-else）**：`_identify_loop_regions` 的 else 归属须判定 fall-through 块是否仅含循环出口 + 后续顺序语句，覆盖嵌套 for 与 match case 内 for。
12. **P2 — repro_12（内层 if 丢失）**：`_identify_if_regions` 须把内层 `if B:` 的 then-块作为外层 If.body 子节点保留，禁止吸收为不可达。

---

## 7. 本轮交付物清单

| 路径 | 说明 |
|------|------|
| `rounds/round_02/test_engineer/decompile_report.md` | 本报告 |
| `rounds/round_02/test_engineer/minimal_repros/repro_01_match_case_none_to_wildcard.py` | MATCH case None→case _（R1 残留） |
| `rounds/round_02/test_engineer/minimal_repros/repro_02_if_elif_is_none_degrade.py` | IF/ELIF IS_OP→`== None`（R1 残留） |
| `rounds/round_02/test_engineer/minimal_repros/repro_04_loop_store_subscr_to_annotation.py` | LOOP STORE_SUBSCR→变量注解 + break（R1 残留演化） |
| `rounds/round_02/test_engineer/minimal_repros/repro_06_if_ifexp_arg_to_and_docstring.py` | IF/IfExp 实参→and + docstring（R1 残留演化） |
| `rounds/round_02/test_engineer/minimal_repros/repro_07_try_except_isinstance_lost.py` | TRY except isinstance 丢失（R1 残留新形态） |
| `rounds/round_02/test_engineer/minimal_repros/repro_08_ternary_condition_lost.py` | TERNARY/LOOP 循环体裸 Name + 重复（R1 残留演化） |
| `rounds/round_02/test_engineer/minimal_repros/repro_09_loop_spurious_for_else.py` | LOOP 双层 spurious for-else + match case（R1 残留） |
| `rounds/round_02/test_engineer/minimal_repros/repro_10_if_body_leaks_as_decorator.py` | IF 块泄漏为 `@((...))` 装饰器（R1 残留演化） |
| `rounds/round_02/test_engineer/minimal_repros/repro_11_if_elif_bare_name.py` | IF/ELIF 裸 Name（R1 残留演化） |
| `rounds/round_02/test_engineer/minimal_repros/repro_12_if_nested_inner_lost.py` | IF 嵌套内层 if 丢失（R1 残留部分修复） |
| `rounds/round_02/test_engineer/minimal_repros/repro_13_function_def_defaults_as_decorator.py` | FUNCTION_DEF defaults→装饰器（**R2 新增**） |
| `rounds/round_02/test_engineer/minimal_repros/repro_14_function_body_truncation_after_elif.py` | IF/ELIF elif 后函数体截断（**R2 新增**） |
| `rounds/round_02/test_engineer/minimal_repros/repro_15_boolop_or_to_and_flip.py` | BOOLOP or→and（**R2 新增**） |
| `rounds/round_02/test_engineer/minimal_repros/repro_16_compare_not_in_to_in_flip.py` | COMPARE not in→in（**R2 新增**） |
| `rounds/round_02/repair_engineer/` | 空目录（待修复工程师使用） |

所有 14 个 repro 均通过 `py_compile` 独立编译，并通过 `python pycdc.py <repro>.pyc` 验证缺陷复现（14/14 DEFECT-REPRO）。

---

## 8. 残留不一致数（R2 基线，交付修复工程师）

- quotation.pyc 反编译产物编译验证：**COMPILE_OK**（顶层语法可编译，但 81 个函数字节码与原 pyc 不一致）
- stderr 警告数：**0**（MatchSingleton 维持清零）
- R2 重编译后 code 对象数：149（原 150，丢失 `build_future_fill_time.<listcomp>`）
- 本轮识别可复现缺陷类：**14 类**（10 项 R1 残留追踪 + 4 项 R2 新增）
- 退出条件 E1（0 不一致）：**未达成**，进入 R2 修复工程师阶段。
- **建议 R2 修复优先级**：P0 repro_13（回归）+ repro_14（大面积截断）→ P1 repro_02/15/16（IS_OP/CONTAINS_OP/or-and）+ repro_10 + repro_01 → P2 其余。

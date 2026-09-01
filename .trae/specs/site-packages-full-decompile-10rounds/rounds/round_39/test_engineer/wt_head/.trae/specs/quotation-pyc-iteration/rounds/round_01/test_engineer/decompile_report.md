# Round 1 反编译报告（decompile_report.md）

> 目标文件：`/workspace/quotation.pyc`
> 反编译命令：`python pycdc.py /workspace/quotation.pyc`
> 基线产物：`baseline/decompiled_baseline.py`（2593 行）、`baseline/decompile_stderr.txt`（19 处 MatchSingleton 警告）、`baseline/compile_status.txt`（line 2579 `filter_type=` 语法错误）
> 反模式起点快照：`baseline/antipattern_snapshot.txt`（`_merge_=1`，其余前缀 =0）

## 0. 总体结论

| 指标 | 数值 |
|------|------|
| 反编译产物总行数 | 2593 |
| stderr 警告数 | 19（全部为 `Unknown expression type: MatchSingleton`）|
| 编译验证 | **失败**：line 2579 `filter_type=` 缺默认值表达式 |
| 本轮识别缺陷类 | **12 类**（覆盖 MATCH / IF / IF-ELIF / LOOP / TRY / TERNARY / ASSERT / COMPARE / BOOLOP / FUNCTION_DEF / IS_OP / NESTED-IF）|
| 涉及区域类型 | MATCH、IF、LOOP、TRY、TERNARY、FUNCTION_DEF、ASSERT、COMPARE、BOOLOP |
| 涉及源码定位 | `core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`、`core/cfg/code_generator.py`、`core/cfg/pattern_parser.py` |
| 最小复现实例 | 12 个，归档于 `minimal_repros/repro_01..repro_12_*.py` |

### 0.1 缺陷分布（按区域类型）

| 区域类型 | 缺陷数 | 涉及 repro |
|----------|--------|------------|
| MATCH（match/case） | 1 | repro_01 |
| IF（if/elif/else） | 5 | repro_02、repro_06、repro_10、repro_11、repro_12 |
| LOOP（for / for-else） | 2 | repro_04、repro_09 |
| TRY（try/except） | 1 | repro_07 |
| TERNARY（IfExp） | 1 | repro_08 |
| ASSERT / COMPARE | 1 | repro_05 |
| FUNCTION_DEF（默认参数） | 1 | repro_03 |
| **合计** | **12** | |

### 0.2 算法 4 原则违反分布

| 原则 | 违反次数 | 涉及缺陷 |
|------|----------|----------|
| 自底向上归约 | 1 | repro_10 |
| 每块唯一归属 | 7 | repro_02、repro_04、repro_07、repro_09、repro_11、repro_12、repro_01 |
| 嵌套即抽象节点 | 3 | repro_05、repro_08、repro_01 |
| 入口引用语义（父引用子入口） | 3 | repro_06、repro_08、repro_01 |

---

## 1. 不一致清单（按函数 + 偏移 + 字节码模式）

| # | 函数（quotation.pyc） | 偏移/行号 | 字节码模式 | 缺陷类型 | repro |
|---|----------------------|-----------|------------|----------|-------|
| 01 | `process`（match/case） | match 块 | `MATCH_CLASS` + `IS_OP`（case None）混合 | MatchSingleton case 合并失败 | repro_01 |
| 02 | `get_quote`（if/elif） | if-elif 边界 | `POP_JUMP_IF_NOT_NONE` + `CONTAINS_OP` | IF/ELIF 边界破坏 + IS_OP 退化 | repro_02 |
| 03 | `filter_stock_by_status`（带默认参数） | MAKE_FUNCTION | `BUILD_LIST 0 + LIST_EXTEND` defaults | 列表默认值丢失 → `filter_type=` 语法错误 | repro_03 |
| 04 | `get_fundflow_day`（for + STORE_SUBSCR） | for 循环体 | `STORE_SUBSCR` + 循环后 RETURN | STORE_SUBSCR 丢失 + spurious for-else | repro_04 |
| 05 | `check_stock`（assert 链式比较） | assert 11>=len(s)>=9 | `CALL` 中段 + `COMPARE_OP` 链 | 链式比较 CALL 参数丢失 | repro_05 |
| 06 | `get_quote`（if A and B: else:） | if + and | `POP_JUMP_IF_NOT_NONE` + `POP_JUMP_IF_FALSE` 共享 else | `and` 被拆为嵌套 if | repro_06 |
| 07 | `api_get`（try/except） | except handler | `DELETE_FAST` + `RETURN_VALUE` | `pass`→`del`、`return (tuple)` 退化 | repro_07 |
| 08 | `load_get_price`（嵌套 IfExp 作 if 条件） | if 条件 | `COPY 1` + 嵌套 `POP_JUMP_IF_FALSE` | if 关键字丢失，条件变 `len(...)` 裸表达式 | repro_08 |
| 09 | `fill_missing_stock_data`（双层 for） | 双层 for 出口 | `FOR_ITER` + fall-through | 双层 spurious for-else | repro_09 |
| 10 | `get_price`（if 嵌套 if/elif/elif） | 外层 if + 后续 if | `POP_JUMP_IF_NONE` + 嵌套 `POP_JUMP_IF_FALSE` | 整段 if 丢失 + `and X is None` 截断 | repro_10 |
| 11 | `check_stocks`（elif isinstance 链） | elif 分支首条 | `LOAD_FAST l` + `LOAD_ATTR replace` + `CALL_METHOD` | 裸 Name Expr + 语句复制 | repro_11 |
| 12 | `get_valuation_info`（嵌套 if） | `if A: S1;S2; if B:` | `POP_JUMP_IF_FALSE` + 内层 `POP_JUMP_IF_FALSE` | 语句提升出 if + 嵌套合并为 `A and B` | repro_12 |

---

## 2. 缺陷详解（12 项）

> 每项包含：区域类型 / 字节码模式 / 反编译产物（错误）/ 期望产物 / 根因初判 / repro 路径。

### Defect 01 — MATCH 区域：MatchSingleton case 模式合并失败

- **区域类型**：MATCH（match/case 语句）
- **触发位置**：`quotation.pyc::process`（match date: case None / case str() / case _）
- **字节码模式**：
  ```
  RESUME
  LOAD_FAST x
  COPY 1                          # subject 保留
  LOAD_CONST None
  COMPARE_OP is                   # case None: IS_OP
  POP_JUMP_FORWARD_IF_FALSE → <case_str>
  <case None body>
  JUMP_FORWARD → <end>
  <case_str>:
  COPY 1
  LOAD_GLOBAL str
  LOAD_CONST 0
  MATCH_CLASS                     # case str():
  POP_JUMP_FORWARD_IF_FALSE → <case_wild>
  <case str body>
  <case_wild>:
  POP_TOP                         # case _:
  <case _ body>
  ```
- **反编译产物（错误）**：
  ```python
  match x:
      case None | {'type': 'MatchClass', 'cls': <...ASTName...>, 'patterns': []} | x:
          date = time.strftime('%Y-%m-%d')
          return date
  ```
  stderr：`Unknown expression type: MatchSingleton`（baseline 共 19 处，全部源自此类合并）
- **期望产物**：
  ```python
  match x:
      case None:
          return 'none'
      case str():
          pass
      case _:
          date = date.replace('-', '')
  ```
- **根因初判**：
  - `core/cfg/region_ast_generator.py::_generate_match` + `core/cfg/pattern_parser.py` 的 MatchOr 重建逻辑：当 match 语句同时包含 `case None:`(MatchSingleton) 与 `case str():`(MatchClass) / `case _:`(MatchAs) 时，`_mr_finalize_match_region`（`region_analyzer.py` L8168 附近）把多个 case 错误合并为一个 MatchOr 模式。
  - 违反原则：**每块唯一归属**（case body 被丢）、**嵌套即抽象节点**（MatchSingleton 字典被当作表达式节点传入 `code_generator._generate_expression`，触发 `Unknown expression type: MatchSingleton`）、**入口引用语义**（父 match 引用错位）。
- **repro 路径**：`minimal_repros/repro_01_match_singleton_case_merge.py`

### Defect 02 — IF/ELIF 边界破坏 + IS_OP 退化为 COMPARE_OP ==

- **区域类型**：IF（if/elif/else）+ IS_OP（is None）
- **触发位置**：`quotation.pyc::get_quote`（`if quote is None and is_trade: ... elif frequency in OVER_WEEK_FREQUENCY and query_date is None:`）
- **字节码模式**：
  ```
  LOAD_GLOBAL quote
  POP_JUMP_FORWARD_IF_NOT_NONE → <elif>     # quote is None
  LOAD_GLOBAL is_trade
  POP_JUMP_FORWARD_IF_FALSE → <elif>
  <if-body>
  <elif>:
  LOAD_GLOBAL frequency
  CONTAINS_OP 0                              # frequency in OVER_WEEK_FREQUENCY
  POP_JUMP_FORWARD_IF_FALSE → <else>
  LOAD_GLOBAL query_date
  POP_JUMP_FORWARD_IF_NOT_NONE → <else>      # query_date is None
  <elif-body>
  ```
- **反编译产物（错误）**：
  ```python
  if (quote == None and is_trade) == OVER_WEEK_FREQUENCY:
      quote = Quote()
  elif frequency in OVER_WEEK_FREQUENCY and query_date == None:
      query_date = datetime.now()
  ```
- **期望产物**：
  ```python
  if quote is None and is_trade:
      quote = Quote()
  elif frequency in OVER_WEEK_FREQUENCY and query_date is None:
      query_date = datetime.now()
  ```
- **根因初判**：
  - `core/cfg/region_analyzer.py::_identify_if_regions` 的 elif 合并逻辑把紧随 `if A:` 之后的 `elif B:` 的条件片段错误并入 `if A:` 条件，生成 `(A) == B` 形式的 Compare。
  - `core/cfg/region_ast_generator.py::_generate_if` 把 `POP_JUMP_IF_NONE`/`POP_JUMP_IF_NOT_NONE`（IS_OP）重建为 `COMPARE_OP == None`，改变了 `is` 与 `==` 的语义。
  - 违反原则：**每块唯一归属**（elif 条件块被并入 if 条件块）。
- **repro 路径**：`minimal_repros/repro_02_if_elif_boundary_is_none.py`

### Defect 03 — FUNCTION_DEF：列表默认值丢失导致 `filter_type=` 语法错误（**line 2579 阻塞编译**）

- **区域类型**：FUNCTION_DEF（函数定义默认参数）
- **触发位置**：`quotation.pyc::filter_stock_by_status`（默认参数 `filter_type=['ST','HALT','DELISTING']`）
- **字节码模式**（模块级，CPython 对可变默认值的编译方式）：
  ```
  LOAD_NAME check_arg
  BUILD_LIST 0
  LOAD_CONST ('ST', 'HALT', 'DELISTING')
  LIST_EXTEND 1                              # ['ST','HALT','DELISTING']
  LOAD_CONST None                            # query_date default
  BUILD_TUPLE 2                              # defaults tuple
  LOAD_CONST <code filter_stock_by_status>
  MAKE_FUNCTION defaults
  PRECALL
  CALL
  STORE_NAME filter_stock_by_status
  ```
- **反编译产物（错误，语法错误）**：
  ```python
  @check_arg
  def filter_stock_by_status(stocks, filter_type=, query_date=None):
      return get_quote().filter_stock_by_status(stocks, filter_type, query_date)
  ```
  编译验证：`SYNTAX_ERR line=2579: expected default value expression`
- **期望产物**：
  ```python
  @check_arg
  def filter_stock_by_status(stocks, filter_type=['ST', 'HALT', 'DELISTING'], query_date=None):
      return get_quote().filter_stock_by_status(stocks, filter_type, query_date)
  ```
- **根因初判**：
  - `core/cfg/region_ast_generator.py::_build_function_def`（L1100-1122 附近）的 `defaults` 处理分支只识别 Constant/Tuple/List/常量元组，但当默认值通过 `BUILD_LIST + LIST_EXTEND` 在模块级动态构造时，defaults 节点被重建为空。
  - `core/cfg/code_generator.py::_generate_arguments_dict`（L534-543 附近）仍根据 `len(defaults)` 判定该参数有默认值，于是发射 `name=` 但 default_code 为空，产生 `filter_type=` 语法错误。
  - 违反原则：**嵌套即抽象节点**（`BUILD_LIST + LIST_EXTEND` 应作为单个 List 表达式节点参与 defaults 重建，不可拆分后丢弃）。
- **repro 路径**：`minimal_repros/repro_03_function_def_list_default.py`

### Defect 04 — LOOP：STORE_SUBSCR 赋值在 for 循环体内丢失 + spurious for-else

- **区域类型**：LOOP（for 循环）+ STORE_SUBSCR（下标赋值）
- **触发位置**：`quotation.pyc::get_fundflow_day`（`for item in prod_code: returninfo[item] = get_fundflow_day_single(...)`）
- **字节码模式**：
  ```
  FOR_ITER → <end>
    STORE_FAST item
    LOAD_FAST returninfo
    LOAD_FAST item                       # subscript key
    <RHS call: LOAD_GLOBAL + LOAD_FAST item, ...>
    STORE_SUBSCR                         # returninfo[item] = call(...)
    JUMP_BACKWARD → <for_iter>
  <end>:
    LOAD_FAST returninfo
    RETURN_VALUE
  ```
- **反编译产物（错误）**：
  ```python
  if isinstance(prod_code, list):
      returninfo = {}
      for item in prod_code:
          item                          # ← bare Name, RHS 丢失
      else:
          return returninfo             # ← spurious for-else
  else:
      return prod_code
  ```
- **期望产物**：
  ```python
  if isinstance(prod_code, list):
      returninfo = {}
      for item in prod_code:
          returninfo[item] = get_fundflow_day_single(item, get_type)
      return returninfo
  return prod_code
  ```
- **根因初判**：
  - `core/cfg/region_ast_generator.py::_generate_loop` / `_build_effective_stmts`（L1698+）在处理 for 循环 fall-through 块中的 `STORE_SUBSCR`（d[k] = call(...)）时，把 RHS 的 CALL 表达式当作孤立的 expr 语句丢弃，只保留了 LOAD_FAST k 作为 bare Name 表达式。
  - `core/cfg/region_analyzer.py::_identify_loop_regions` 把循环后的下一条 return 语句错误归入一个不存在的 for-else 分支。
  - 违反原则：**每块唯一归属**（fall-through 块应归循环出口 + 后续顺序语句，不应整体划给 for-else）。
- **repro 路径**：`minimal_repros/repro_04_loop_store_subscr_lost.py`

### Defect 05 — ASSERT/COMPARE：链式比较中的 CALL 参数丢失（`len(s)` → `len`）

- **区域类型**：ASSERT + COMPARE_OP（链式比较 `11 >= len(s) >= 9`）
- **触发位置**：`quotation.pyc::check_stock`（`assert 11 >= len(s) >= 9`）
- **字节码模式**：
  ```
  LOAD_CONST 11
  LOAD_GLOBAL len
  LOAD_FAST s
  PRECALL 1
  CALL 1
  LOAD_CONST 9
  COMPARE_OP <=                # 11 >= len(s)
  SWAP / COPY                  # 链式中段
  COMPARE_OP <=                # len(s) >= 9
  COMPARE_OP                   # 链式比较合并
  POP_JUMP_IF_FALSE
  <assert msg>
  ```
- **反编译产物（错误）**：
  ```python
  assert 11 >= len >= 9, 'msg2'
  ```
- **期望产物**：
  ```python
  assert 11 >= len(s) >= 9, 'msg2'
  ```
- **根因初判**：
  - `core/cfg/region_ast_generator.py` 的链式比较重建（`_generate_compare` / `Compare` AST 重建）在处理 `11 >= len(s) >= 9` 三元链式比较时，把中段 `len(s)` 的 CALL 节点拆解为单独的 LOAD_GLOBAL len，丢失了 `LOAD_FAST s + PRECALL + CALL` 指令，导致只剩裸 `len`。
  - 区域归约时把 `len(s)` 的 CALL 错误归并到比较链的左/右操作数。
  - 违反原则：**嵌套即抽象节点**（`len(s)` 应作为一个 Call 子节点整体参与比较，不可拆分）。
- **repro 路径**：`minimal_repros/repro_05_assert_compare_call_arg_lost.py`

### Defect 06 — IF/BOOLOP：`if A and B:` 被错误分解为嵌套 `if A: if B:`，else 语义改变

- **区域类型**：IF + BOOLOP（and）
- **触发位置**：`quotation.pyc::get_quote`（`if quote is None and is_trade: X else: Y`）
- **字节码模式**：
  ```
  LOAD_GLOBAL quote
  POP_JUMP_FORWARD_IF_NOT_NONE → <else>     # A: quote is None
  LOAD_GLOBAL is_trade
  POP_JUMP_FORWARD_IF_FALSE → <else>        # B: is_trade
  <if-body: quote = Quote(log, is_trade)>
  JUMP_FORWARD → <end>
  <else>:
  <else-body: quote = Quote()>
  <end>:
  ```
- **反编译产物（错误，else 语义改变）**：
  ```python
  if quote is None:
      if is_trade:
          quote = Quote(log, is_trade)
  else:
      quote = Quote()
  return quote
  ```
- **期望产物**：
  ```python
  if quote is None and is_trade:
      quote = Quote(log, is_trade)
  else:
      quote = Quote()
  return quote
  ```
- **根因初判**：
  - `core/cfg/region_analyzer.py::_identify_if_regions` 在归约 `if A and B: X else: Y` 时，把 `and` 短路跳转的两段条件块错误识别为两个嵌套的 IfRegion（外层 `if A:`，内层 `if B:`），而把 `else: Y` 归到外层 if。
  - 原始 `else` 语义是 `not (A and B) = not A or not B`，重建后变成 `not A`，丢失了 `not A and B` 与 `A and not B` 两种情况。
  - 违反原则：**入口引用语义**（BoolOp(and) 应作为 If.condition 的单一子节点，不应拆成两层 If）。
- **repro 路径**：`minimal_repros/repro_06_if_boolop_and_decompose.py`

### Defect 07 — TRY/EXCEPT：`pass` 被误重建为 `del`，`return (tuple)` 退化为裸表达式

- **区域类型**：TRY（try/except）
- **触发位置**：`quotation.pyc::api_get`（except handler 内 `pass` + `return (dict, {})`）
- **字节码模式**：
  ```
  SETUP_FINALLY / SETUP_EXCEPT
  <try body>
  JUMP_FORWARD → <end>
  <except ConnectionRefusedError>:
  STORE_FAST e1
  <handler body>
  BUILD_TUPLE 2 / BUILD_MAP
  RETURN_VALUE
  <except HTTPError>:
  STORE_FAST e2
  LOAD_FAST e2
  <isinstance check>
  POP_JUMP_IF_FALSE
  <pass body: NOP>
  DELETE_FAST e2                      # except 变量清理
  <handler body>
  ```
- **反编译产物（错误）**：
  ```python
  except ConnectionRefusedError as e1:
      ...
      ({'error_no': error_no, 'error_info': error_info}, {})   # ← 裸表达式
      return None                                               # ← 错误 return
  except HTTPError as e2:
      if isinstance(e2, HTTPError):
          del e2                                                # ← pass 被改写
      elif isinstance(e2, BaseException):
          pass
  ```
- **期望产物**：
  ```python
  except ConnectionRefusedError as e1:
      ...
      return ({'error_no': error_no, 'error_info': error_info}, {})
  except HTTPError as e2:
      if isinstance(e2, HTTPError):
          pass
      elif isinstance(e2, BaseException):
          pass
  ```
- **根因初判**：
  - (a) `pass` → `del e2`：`core/cfg/region_ast_generator.py::_generate_try` 在处理 except handler 中 `pass`（对应 POP_TOP/NOP）时，把 except 变量清理指令（`DELETE_NAME e2` / `POP_TOP`）误识别为用户语句 `del e2`。
  - (b) `return (tuple)` → 裸 tuple + `return None`：`_generate_return` 在 except handler 内遇到 `LOAD_CONST tuple + RETURN_VALUE` 时，把 RETURN_VALUE 错误归约成 RETURN_CONST None，原 tuple 表达式被作为孤立 Expr 语句留在前面。
  - 违反原则：**每块唯一归属**（except 变量的隐式清理应归 except 机制，不应发射为源码 del）。
- **repro 路径**：`minimal_repros/repro_07_try_except_pass_to_del.py`

### Defect 08 — TERNARY/IF：`if (ternary):` 条件被替换为 `len(ternary)` 裸表达式

- **区域类型**：TERNARY（IfExp）+ IF
- **触发位置**：`quotation.pyc::load_get_price`（`if len(start[8:]) == 4 if len(data) > 0 else (is_utc == '0' if ... else ...):`）
- **字节码模式**：
  ```
  <A>
  COPY 1
  <B>
  POP_JUMP_IF_FALSE → <else1>
  <A-true>
  JUMP_FORWARD → <end1>
  <else1>:
  <C>
  COPY 1
  <D>
  POP_JUMP_IF_FALSE → <else2>
  <C-true>
  JUMP_FORWARD → <end2>
  <else2>:
  <E>
  <end2>/<end1>:
  POP_JUMP_IF_FALSE → <after-if>     # ← 这一层 if 被丢失
  <if-body>
  <after-if>:
  ```
- **反编译产物（错误）**：
  ```python
  len(len(start[8:]) == 4 if len(data) > 0 else is_utc == '0' if len(panel.major_axis) != 0 else retpanel.empty)
  ```
- **期望产物**：
  ```python
  if len(start[8:]) == 4 if len(data) > 0 else (is_utc == '0' if len(panel.major_axis) != 0 else retpanel.empty):
      pass
  ```
- **根因初判**：
  - `core/cfg/region_ast_generator.py::_generate_if` / `_generate_ifexp` 在处理 `if (A if B else (C if D else E)):` 这种条件位置为嵌套三元表达式的情况时，把 if 语句的 condition 错误归约为一个孤立的 Expr 语句，且在最外层套上了 `len(...)`（来自 `COPY 1 + LOAD_GLOBAL len` 的栈对齐误读）。
  - 原始 `if` 关键字丢失，三元表达式被包裹成 `len(...)` 作为表达式语句。
  - 违反原则：**入口引用语义**（IfExp 应作为 If.condition 的子节点，不应被单独提升为语句）。
- **repro 路径**：`minimal_repros/repro_08_ternary_in_if_condition.py`

### Defect 09 — LOOP：spurious for-else（循环后代码被错误归入 for-else 块）

- **区域类型**：LOOP（for 循环 + for-else 误生成）
- **触发位置**：`quotation.pyc::fill_missing_stock_data`（双层 for 无 else）
- **字节码模式**：
  ```
  FOR_ITER → <end>
    STORE_FAST stock
    FOR_ITER → <inner-end>          # 内层 for
      STORE_FAST date
      <inner body>
      JUMP_BACKWARD → <inner-for>
    <inner-end>:                     # 内层 fall-through
    JUMP_BACKWARD → <outer-for>
  <end>:                             # 外层 fall-through
    <后续语句: data_filled = ...; return data>
  ```
- **反编译产物（错误，双层 spurious for-else）**：
  ```python
  for stock in secu_filled_list:
      for date in data['end_date'].unique():
          data_tmp = dict()
          data_list.append(data_tmp)
      else:
          continue                   # ← 内层 spurious else
  else:
      data_filled = pandas.DataFrame(data_list, columns=data.columns)   # ← 外层 spurious else
      data = data.append(data_filled)
      return data
  ```
- **期望产物**：
  ```python
  for stock in secu_filled_list:
      for date in data['end_date'].unique():
          data_tmp = dict()
          data_list.append(data_tmp)
  data_filled = pandas.DataFrame(data_list, columns=data.columns)
  data = data.append(data_filled)
  return data
  ```
- **根因初判**：
  - `core/cfg/region_analyzer.py::_identify_loop_regions` 的 else 归属判定：CPython 对 `for x in it: body`（无 else）编译为 `FOR_ITER ... JUMP_BACKWARD; <fall-through>: <next stmts>`，fall-through 块同时是循环出口与后续语句的入口。
  - 归约器把 fall-through 中的后续语句（如 `data_filled = ...; data = ...; return data`）错误识别为 for-else 的 body，且对嵌套 for 也重复该错误（内层 for 也被加上 `else: continue`）。
  - 违反原则：**每块唯一归属**（fall-through 块应归循环出口 + 后续顺序语句，不应整体划给 for-else）。
- **repro 路径**：`minimal_repros/repro_09_loop_spurious_for_else.py`

### Defect 10 — IF：整个 `if A:` 嵌套 if/elif/elif 块被完全丢弃 + `and X is None` 条件被截断

- **区域类型**：IF（if/elif/elif 嵌套）+ BOOLOP（and）+ IS_OP（is None）
- **触发位置**：`quotation.pyc::get_price`（`if security is not None: if/elif/elif` + 后续 `if frequency not in OVER_WEEK_FREQUENCY and query_date is None:`）
- **字节码模式**：
  ```
  LOAD_FAST security
  POP_JUMP_FORWARD_IF_NONE → <after-if1>     # if security is not None:
    LOAD_GLOBAL len / LOAD_FAST security / COMPARE_OP == / POP_JUMP_IF_FALSE
    <if len==0 body>
    LOAD_GLOBAL isinstance / ... / POP_JUMP_IF_FALSE
    <elif isinstance str body>
    LOAD_FAST fq / LOAD_CONST 'dypre' / COMPARE_OP == / POP_JUMP_IF_FALSE
    <elif fq=='dypre' body>
  <after-if1>:
  LOAD_GLOBAL frequency / CONTAINS_OP / POP_JUMP_IF_FALSE
  LOAD_GLOBAL query_date / POP_JUMP_IF_NOT_NONE   # and query_date is None
  <if-body>
  ```
- **反编译产物（错误，整段 if 丢失 + 条件截断）**：
  ```python
  @check_arg
  def get_price(...):
      if frequency not in OVER_WEEK_FREQUENCY:        # ← 缺 `and query_date is None`
          now_dt = datetime.now()
          query_date = now_dt
      else:
          query_date = datetime.strptime(query_date, '%Y%m%d')
      return security
  ```
- **期望产物**：
  ```python
  @check_arg
  def get_price(...):
      ClearAllCache()
      is_string = False
      if security is not None:                        # ← 整段被丢
          if len(security) == 0:
              strategy_log.error('security cannot be empty')
          elif isinstance(security, str):
              is_string = True
              security = [security]
          elif fq == 'dypre':
              fq = 'pre'
      if frequency not in OVER_WEEK_FREQUENCY and query_date is None:
          now_dt = datetime.now()
          query_date = now_dt
      else:
          query_date = datetime.strptime(query_date, '%Y%m%d')
      return security
  ```
- **根因初判**：
  - `core/cfg/region_analyzer.py::_identify_if_regions` 在归约 `if A:`（POP_JUMP_IF_NONE）内嵌套 `if B: ... elif C: ... elif D: ...` 的复杂结构时，把外层 if 的整个 then-块（含嵌套 if/elif/elif）错误归约为不可达 / 被吸收的子区域，导致整段语句丢失。
  - 紧随其后的 `if E and F is None:`（其中 `F is None` 走 `POP_JUMP_IF_NOT_NONE`）的条件也被截断为只剩 `if E:`，丢失 `and F is None` 子句。
  - 违反原则：**自底向上归约**（嵌套 IfRegion 应作为外层 If.body 的子节点保留，不应被丢弃）。
- **repro 路径**：`minimal_repros/repro_10_if_nested_block_dropped.py`

### Defect 11 — IF/ELIF：裸表达式 + 语句复制（elif 分支首条语句被复制为裸 Name）

- **区域类型**：IF/ELIF（isinstance 链）
- **触发位置**：`quotation.pyc::check_stocks`（`elif isinstance(l, list) or isinstance(l, tuple): l = l.replace(...); for s in l:`）
- **字节码模式**：
  ```
  LOAD_FAST l
  POP_JUMP_IF_FALSE ...               # isinstance check 1
  ...
  LOAD_FAST l                         # ← 这两个 LOAD_FAST l
  LOAD_ATTR replace                   #   一个被误识别为 Expr(l)
  LOAD_CONST '.XSHE'
  LOAD_CONST '.SZ'
  CALL_METHOD 2
  STORE_FAST l                        # l = l.replace(...)
  FOR_ITER ...                        # for s in l:
  ```
- **反编译产物（错误，裸 l + 重复赋值）**：
  ```python
  elif isinstance(l, list) or isinstance(l, tuple):
      l = l.replace('.XSHE', '.SZ')
      l                                # ← 裸 Name Expr
      l = l.replace('.XSHE', '.SZ')    # ← 重复赋值
      for s in l:
          s = s.replace('.XSHE', '.SZ')
          check_stock(s)
  else:
      raise RuntimeError('error')
  ```
- **期望产物**：
  ```python
  elif isinstance(l, list) or isinstance(l, tuple):
      l = l.replace('.XSHE', '.SZ')
      for s in l:
          s = s.replace('.XSHE', '.SZ')
          check_stock(s)
  else:
      raise RuntimeError('error')
  ```
- **根因初判**：
  - `core/cfg/region_ast_generator.py::_generate_if` 在处理 `elif isinstance(l, list) or isinstance(l, tuple):` 分支时，把分支首条语句 `l = l.replace(...)` 的 RHS 计算指令（`LOAD_FAST l + LOAD_ATTR replace + ...`）错误地拆出一个孤立的 `l` Expr 语句放在分支开头，然后把完整的赋值语句再发射一次，造成「裸 l + 完整赋值」并存。
  - 违反原则：**每块唯一归属**（`LOAD_FAST l` 应作为 `l.replace(...)` Call 的子节点（receiver），不应被提升为独立 Expr）。
- **repro 路径**：`minimal_repros/repro_11_if_elif_dup_and_bare_expr.py`

### Defect 12 — IF：嵌套 `if A: if B:` 被错误合并为 `if A and B:`，且外层 if 块前的语句被提升到 if 之外

- **区域类型**：IF（嵌套 if）
- **触发位置**：`quotation.pyc::get_valuation_info`（`if isinstance(stocks, str): stock_list = [stocks]; check_stocks(stock_list); if filled: ...`）
- **字节码模式**：
  ```
  LOAD_GLOBAL isinstance / LOAD_FAST stocks / LOAD_GLOBAL str
  CALL / POP_JUMP_IF_FALSE → <else>            # if isinstance(stocks, str):
    <S1: stock_list = [stocks]>                 # ← 被错误提升到 if 之外
    <S2: check_stocks(stock_list)>              # ← 被错误提升到 if 之外
    LOAD_FAST filled
    POP_JUMP_IF_FALSE → <else>                 # if filled:
      <body: trading_days = ...; return index>
    JUMP_FORWARD → <end>
  <else>:
    LOAD_CONST {} / RETURN_VALUE
  <end>:
  ```
- **反编译产物（错误，语句提升 + 嵌套合并）**：
  ```python
  stock_list = [stocks]                          # ← 被提升出 if
  check_stocks(stock_list)                       # ← 被提升出 if
  if isinstance(stocks, str) and filled:         # ← 嵌套 if 被合并
      trading_days = get_trading_days()
      index = trading_days[-count:]
      return index
  else:
      return {}
  ```
- **期望产物**：
  ```python
  if isinstance(stocks, str):
      stock_list = [stocks]
      check_stocks(stock_list)
      if filled:
          trading_days = get_trading_days()
          index = trading_days[-count:]
          return index
  return {}
  ```
- **根因初判**：
  - `core/cfg/region_analyzer.py::_identify_if_regions` 在归约 `if A: S1; S2; if B: body` 时，把外层 if 的 then-块中的顺序语句 S1/S2 错误提升到 if 之外，再把外层 `if A:` 与内层 `if B:` 合并为 `if A and B:`。
  - 改变了控制流语义（原 `not A` 分支会跳过 S1/S2，合并后 S1/S2 在 if 之外，`not A` 也会执行 S1/S2）。
  - 与 repro_06 互为反向缺陷：repro_06 把 `if A and B:` 拆成嵌套 if；本缺陷把嵌套 if 合并成 `if A and B:`。
  - 违反原则：**每块唯一归属**（S1/S2 的 LOAD/CALL/STORE 指令应归 if.then 块）。
- **repro 路径**：`minimal_repros/repro_12_if_nested_merge_and_hoist.py`

---

## 3. 字节码 diff 摘要

> 完整字节码 diff 体积较大（baseline `original_bytecode.txt` ≈ 932KB），本节仅列出本报告 12 项缺陷对应的指令级差异摘要，供修复工程师按区域归约算法定位使用。

| # | 函数 | 原 pyc 关键指令 | 反编译产物重编译后缺失/变化 |
|---|------|-----------------|----------------------------|
| 01 | process | `LOAD_CONST None + COMPARE_OP is` (case None) | case None 被合并入 MatchOr，body 丢失 |
| 02 | get_quote | `POP_JUMP_FORWARD_IF_NOT_NONE` (is None) | 退化为 `COMPARE_OP == None`，elif 条件并入 if |
| 03 | filter_stock_by_status | `BUILD_LIST 0 + LIST_EXTEND 1` (defaults) | defaults 重建为空 → `filter_type=` 语法错误 |
| 04 | get_fundflow_day | `STORE_SUBSCR`（returninfo[item] = call） | RHS CALL 丢失，仅剩 bare Name `item` |
| 05 | check_stock | `LOAD_GLOBAL len + LOAD_FAST s + CALL 1`（链式中段） | `len(s)` 退化为裸 `len` |
| 06 | get_quote | `POP_JUMP_IF_NOT_NONE` + `POP_JUMP_IF_FALSE` 共享 else | `and` 拆为嵌套 if，else 语义改变 |
| 07 | api_get | `DELETE_FAST e2`（except 清理）+ `BUILD_TUPLE + RETURN_VALUE` | `pass`→`del e2`；`return (tuple)`→`return None` + 裸 Expr |
| 08 | load_get_price | 嵌套 `IfExp` 作 if 条件（`COPY 1 + POP_JUMP_IF_FALSE`） | `if` 丢失，条件变 `len(...)` 裸 Expr |
| 09 | fill_missing_stock_data | 双层 `FOR_ITER + fall-through` | 双层 spurious `for-else` |
| 10 | get_price | 外层 `POP_JUMP_IF_NONE` + 嵌套 `POP_JUMP_IF_FALSE` | 整段 if 丢失；`and query_date is None` 被截断 |
| 11 | check_stocks | elif 分支 `LOAD_FAST l + LOAD_ATTR replace + CALL_METHOD` | 裸 `l` Expr + 重复赋值 |
| 12 | get_valuation_info | 嵌套 `POP_JUMP_IF_FALSE`（if A: ...; if B:） | S1/S2 提升出 if；嵌套 if 合并为 `if A and B:` |

---

## 4. 反模式自检（与 baseline 一致）

| 前缀 | 起点快照计数 |
|------|--------------|
| `_fix_` | 0 |
| `_merge_` | 1（已知遗留 `_merge_block_is_loop_back_edge`，按 spec 计划在迭代过程中重命名为 `is_merge_block_loop_back_edge`）|
| `_patch_` | 0 |
| `_fallback_` | 0 |
| `_hack_` | 0 |
| `_workaround_` | 0 |
| `_temp_` | 0 |

本轮（测试工程师阶段）未修改 `core/cfg/*` 任何源码，反模式计数无新增。

---

## 5. 给修复工程师的建议（按区域归约算法 4 原则）

> 以下建议仅为根因方向，具体修复须由修复工程师在 `region_analyzer.py` / `region_ast_generator.py` 内按「No More Gotos」+ 4 原则完善识别/生成逻辑，禁止补丁。

1. **MATCH（repro_01）**：`_mr_finalize_match_region` 须按 case 边界（每个 `POP_JUMP_FORWARD_IF_FALSE` + `JUMP_FORWARD`）拆分独立 case，MatchSingleton 不可与 MatchClass/MatchAs 合并为 MatchOr；case body 须按 `JUMP_FORWARD → end` 归属。
2. **IF/ELIF（repro_02、repro_10、repro_11）**：`_identify_if_regions` 的 elif 合并须以 `POP_JUMP_FORWARD_IF_FALSE → 下一个 elif 入口` 为边界，禁止把 elif 条件并入 if 条件；`POP_JUMP_IF_NONE`/`POP_JUMP_IF_NOT_NONE` 须重建为 `is None`/`is not None`，禁止退化为 `== None`。
3. **FUNCTION_DEF（repro_03）**：`_build_function_def` 须识别 `BUILD_LIST 0 + LIST_EXTEND 1` / `BUILD_TUPLE + LIST_EXTEND` 等动态默认值构造序列，作为单个 List/Tuple 表达式节点填充 defaults。
4. **LOOP（repro_04、repro_09）**：`_identify_loop_regions` 的 else 归属须判定 fall-through 块是否仅含循环出口 + 后续顺序语句；`_generate_loop` / `_build_effective_stmts` 须保留 `STORE_SUBSCR` 的 RHS CALL，不可降级为 bare Name。
5. **TRY（repro_07）**：`_generate_try` 须把 except 变量清理（`DELETE_FAST`/`POP_TOP`）归 except 机制，禁止发射 `del`；`_generate_return` 须区分 `RETURN_VALUE`（带表达式）与 `RETURN_CONST`（仅常量）。
6. **TERNARY（repro_08）**：`_generate_if` 须把 IfExp 作为 If.condition 的子节点保留，禁止提升为独立 Expr，禁止用 `len(...)` 包裹做栈对齐。
7. **COMPARE（repro_05）**：链式比较重建须把中段 `len(s)` 的 `LOAD_GLOBAL + LOAD_FAST + PRECALL + CALL` 作为单个 Call 子节点，不可拆解后丢弃 LOAD_FAST + CALL。
8. **BOOLOP（repro_06、repro_12）**：`_identify_if_regions` 须统一处理 `and` 短路跳转——既不可把 `if A and B:` 拆成嵌套 if（repro_06），也不可把 `if A: S; if B:` 合并成 `if A and B:`（repro_12）。判定依据：else 目标是否同一块 + then 块内是否存在顺序语句 S。

---

## 6. 本轮交付物清单

| 路径 | 说明 |
|------|------|
| `rounds/round_01/test_engineer/decompile_report.md` | 本报告 |
| `rounds/round_01/test_engineer/minimal_repros/repro_01_match_singleton_case_merge.py` | MATCH MatchSingleton 合并 |
| `rounds/round_01/test_engineer/minimal_repros/repro_02_if_elif_boundary_is_none.py` | IF/ELIF 边界 + IS_OP 退化 |
| `rounds/round_01/test_engineer/minimal_repros/repro_03_function_def_list_default.py` | FUNCTION_DEF 列表默认值丢失（line 2579 阻塞） |
| `rounds/round_01/test_engineer/minimal_repros/repro_04_loop_store_subscr_lost.py` | LOOP STORE_SUBSCR 丢失 + spurious for-else |
| `rounds/round_01/test_engineer/minimal_repros/repro_05_assert_compare_call_arg_lost.py` | ASSERT 链式比较 CALL 丢失 |
| `rounds/round_01/test_engineer/minimal_repros/repro_06_if_boolop_and_decompose.py` | IF `and` 被拆为嵌套 if |
| `rounds/round_01/test_engineer/minimal_repros/repro_07_try_except_pass_to_del.py` | TRY `pass`→`del`、`return (tuple)` 退化 |
| `rounds/round_01/test_engineer/minimal_repros/repro_08_ternary_in_if_condition.py` | TERNARY if 条件变 `len(...)` 裸 Expr |
| `rounds/round_01/test_engineer/minimal_repros/repro_09_loop_spurious_for_else.py` | LOOP 双层 spurious for-else |
| `rounds/round_01/test_engineer/minimal_repros/repro_10_if_nested_block_dropped.py` | IF 整段嵌套 if/elif/elif 丢失 + 条件截断 |
| `rounds/round_01/test_engineer/minimal_repros/repro_11_if_elif_dup_and_bare_expr.py` | IF/ELIF 裸 Name Expr + 语句复制 |
| `rounds/round_01/test_engineer/minimal_repros/repro_12_if_nested_merge_and_hoist.py` | IF 嵌套合并为 `A and B` + 语句提升 |

所有 repro 均通过 `python -c "import py_compile; py_compile.compile(<file>, doraise=True)"` 验证可独立编译。

---

## 7. 残留不一致数（本轮基线）

- quotation.pyc 反编译产物编译验证：**失败**（line 2579 `filter_type=` 缺默认值）
- stderr 警告数：**19**（全部 MatchSingleton，对应 Defect 01 的同一根因在 19 处 match 块重复出现）
- 本轮识别可复现缺陷类：**12 类**（详见第 1 节）
- 退出条件 E1（0 不一致）：**未达成**，进入修复工程师阶段（R1-T3 ~ R1-T8）。

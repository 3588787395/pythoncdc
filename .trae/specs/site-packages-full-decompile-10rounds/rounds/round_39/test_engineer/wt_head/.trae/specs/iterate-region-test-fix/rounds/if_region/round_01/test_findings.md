# IF 区域 第 1 轮 测试发现 (round_01)

- 测试日期：2026-07-16
- 基线：if_region 311 passed / 0 failed（原始代码，无 adv 测试）
- 本轮新增测试文件：12 个 `test_adv01_*.py`
- 确认错误数：**12**（全部失败，0 个通过计入错误；本轮 3 个通过的不计入）
- 验证方式：`ExhaustiveTestCase.verify_decompilation()` → `verify_bytecode_equivalence()`（对比原始字节码 vs 反编译后重编译字节码；过滤跳转/对齐指令）
- 约束遵守：未修改 `core/cfg/` 下任何源码，仅新增测试文件与本报告

## 失败测试列表（12 个确认错误）

| # | 测试文件 | 类名 | 失败环节 |
|---|----------|------|----------|
| 1 | test_adv01_walrus_or.py | TestAdv01WalrusOr | 字节码不等价 |
| 2 | test_adv01_await_cond.py | TestAdv01AwaitCond | 字节码不等价（嵌套 code object） |
| 3 | test_adv01_lambda_call_cond.py | TestAdv01LambdaCallCond | 字节码不等价（嵌套 code object） |
| 4 | test_adv01_not_chained_compare.py | TestAdv01NotChainedCompare | 字节码不等价 |
| 5 | test_adv01_not_or_cmp.py | TestAdv01NotOrCmp | 字节码不等价 |
| 6 | test_adv01_walrus_chained.py | TestAdv01WalrusChained | 字节码不等价 |
| 7 | test_adv01_bare_ternary_cond.py | TestAdv01BareTernaryCond | 区域类型缺失（无 If 节点） |
| 8 | test_adv01_kwargs_call_cond.py | TestAdv01KwargsCallCond | 字节码不等价 |
| 9 | test_adv01_nested_ternary_cond.py | TestAdv01NestedTernaryCond | 区域类型缺失（无 If 节点） |
| 10 | test_adv01_await_compare.py | TestAdv01AwaitCompare | 字节码不等价（嵌套 code object） |
| 11 | test_adv01_not_4chain.py | TestAdv01Not4Chain | 反编译结果语法错误 |
| 12 | test_adv01_lambda_noarg_call_cond.py | TestAdv01LambdaNoargCallCond | 字节码不等价（嵌套 code object） |

## 本轮通过的测试（不计入错误，仅作覆盖参考）

- test_adv01_ternary_cond.py（`(a if c else b) > 0` — 三元在比较左侧，通过）
- test_adv01_isnone_ornone.py（`x is None or y is None`，通过）
- test_adv01_triple_isnone_and.py（三连 `is None and`，通过）
- test_adv01_not_isnone.py（`not (x is None)`，通过）
- test_adv01_simple_walrus.py（`if (n := f()):`，通过）
- test_adv01_in_and_notin.py（`a in b and c not in d`，通过）
- test_adv01_not_isnone_ornone.py（`not (x is None or y is None)`，通过）
- test_adv01_deep_attr_or.py（`a.b.c > 0 or d.e.f < 0`，通过）
- test_adv01_not_and_cmp.py（`not (a < b and c > d)`，通过）
- test_adv01_walrus_and.py（`(n := f()) > 0 and n < 100`，通过）
- test_adv01_not_3and.py（`not (a and b and c)`，通过）

---

## 错误详细记录

### 错误 01 — walrus + or 条件触发副作用重复

- 文件：test_adv01_walrus_or.py
- 源码：
  ```python
  if (n := f()) > 0 or n < -10:
      pass
  ```
- 期望反编译：保留单次 `f()` 调用与 walrus 绑定，条件为 `(n := f()) > 0 or n < -10`
- 实际反编译：
  ```python
  n = f()
  if ((n := f()) > 0 or n < -10):
      pass
  ```
- 失败信息：指令数不匹配 16 vs 21（原始 16，重编 21）
- 根因初判：`_if_extract_condition_from_instructions` / BoolOp 重建路径未识别 walrus 的 COPY+STORE_NAME 副作用块属于条件内部，把 walrus 的求值块当作独立语句 `n = f()` 提到 if 之前，且条件里又重复了一次 `(n := f())`，导致 `f()` 被调用两次、副作用翻倍。walrus 在 BoolOp (`or`) 短路链中的归属判定缺失。

### 错误 02 — async 函数内 await 作条件，整个协程体丢失

- 文件：test_adv01_await_cond.py
- 源码：
  ```python
  async def f():
      if await g():
          return 1
      return 0
  ```
- 期望反编译：保留 `async def f`、`if await g():`、return 分支
- 实际反编译：
  ```python
  async def f():
      while True:
          pass
      if True:
          return 1
      else:
          return 0
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 15 vs 3（重编协程体仅 3 条指令 `RETURN_GENERATOR/POP_TOP/RESUME`）
- 根因初判：嵌套 code object（`f` 的协程体）几乎为空，说明 `RegionASTGenerator` 对 async 函数体内以 `GET_AWAITABLE/YIELD_VALUE` 实现的 `await` 表达式作为 if 条件时，区域分析未把 await+条件识别为 IF_REGION，而是退化成 `while True: pass` + `if True/if 0` 假分支。`await` 在条件上下文的表达式重建完全缺失。

### 错误 03 — lambda 调用条件中 lambda 体被占位符替换

- 文件：test_adv01_lambda_call_cond.py
- 源码：
  ```python
  if (lambda x: x + 1)(5) > 3:
      pass
  ```
- 期望反编译：保留 `lambda x: x + 1` 及其调用
- 实际反编译：
  ```python
  if ((lambda *args, **kwargs: None)(5) > 3):
      pass
  ```
- 失败信息：嵌套 code object 不匹配（指令2）：指令1参数不匹配 5 vs None（op=LOAD_CONST）
- 根因初判：lambda code object 的重建走了“未知 lambda”占位路径 `lambda *args, **kwargs: None`，丢失了原始参数 `x` 与函数体 `x + 1`（原始 LOAD_CONST 5 vs 重编 None）。条件块中内嵌的 lambda code object 反编译未提取其真实形参与函数体。

### 错误 04 — not + 链式比较，链式比较第二段丢失

- 文件：test_adv01_not_chained_compare.py
- 源码：
  ```python
  if not 0 < a < 10:
      pass
  ```
- 期望反编译：`if not 0 < a < 10:` 或等价 `not (0 < a < 10)`
- 实际反编译：
  ```python
  if (not (0 < a and 10)):
      pass
  ```
- 失败信息：指令数不匹配 13 vs 8（原始含两次 COMPARE_OP + 一次 POP_TOP 的链式比较；重编只有一次 COMPARE_OP）
- 根因初判：`_build_chained_compare_from_region_data` 在 `not` 包裹链式比较时未正确重建三段链 `0 < a < 10`，第二比较 `a < 10` 被丢成纯常量 `10`，输出 `0 < a and 10`（语义错误：`and 10` 恒真）。`_negate_expr` 对链式 Compare（多 ops）不处理，触发回退到错误的 BoolOp 重建。

### 错误 05 — not + or 比较触发 De Morgan 改写，字节码结构不一致

- 文件：test_adv01_not_or_cmp.py
- 源码：
  ```python
  if not (a < b or c > d):
      pass
  ```
- 期望反编译：保留 `not (a < b or c > d)` 结构
- 实际反编译：
  ```python
  if (a >= b and c <= d):
      pass
  ```
- 失败信息：指令3参数不匹配：`<` vs `>=` (op=COMPARE_OP)
- 根因初判：BoolOp 条件重建对 `not (X or Y)` 应用了 De Morgan 定律改写成 `not X and not Y`（即 `a >= b and c <= d`），虽然语义等价，但 COMPARE_OP 的运算符被取反（`<`→`>=`、`>`→`<=`），与原始字节码 `<`/`>` 不一致，违反字节码等价约束。`_build_boolop_expression` 中 UNARY_NOT 转换分支对 BoolOp 应保留 `not (...)` 原貌而非内联取反。

### 错误 06 — walrus + 链式比较，左操作数丢失 + f() 被调用两次

- 文件：test_adv01_walrus_chained.py
- 源码：
  ```python
  if 0 < (n := f()) < 10:
      pass
  ```
- 期望反编译：保留 `0 < (n := f()) < 10` 单次调用
- 实际反编译：
  ```python
  if (f() < (n := f())):
      pass
  ```
- 失败信息：指令数不匹配 20 vs 16
- 根因初判：链式比较中段为 walrus `(n := f())` 时，`compute_chained_compare_operands` / `_build_chained_compare_from_region_data` 把 walrus 的求值块（COPY+STORE_NAME）与左操作数 `0` 混淆：左操作数 `0` 丢失，且 walrus 的 `f()` 被拆成两处独立 `f()` 调用（一处裸调用、一处 walrus），导致 `f()` 调用两次并丢失链式结构（`< 10` 段也丢失）。

### 错误 07 — 裸三元作 if 条件，if 语句丢失变成表达式语句

- 文件：test_adv01_bare_ternary_cond.py
- 源码：
  ```python
  if a if c else b:
      pass
  ```
- 期望反编译：`if (a if c else b): pass`（或等价带 If 节点）
- 实际反编译：
  ```python
  (a if c else b)
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION（期望 AST 节点 ['If']）
- 根因初判：当 if 条件本身是一个裸三元表达式（无外层比较）时，`_if_extract_condition_from_instructions` 走 TernaryRegion 合并分支，把整个 if 语句错当成三元表达式语句输出，`If` 节点与 `pass` 体全部丢失。三元作“纯条件”（test）的 IF_REGION 识别缺失。

### 错误 08 — 条件中带关键字/星号参数的调用，参数全部丢失

- 文件：test_adv01_kwargs_call_cond.py
- 源码：
  ```python
  if f(a, b=c, *d, **e):
      pass
  ```
- 期望反编译：保留 `f(a, b=c, *d, **e)` 完整调用参数
- 实际反编译：
  ```python
  if f():
      pass
  ```
- 失败信息：指令数不匹配 18 vs 9（原始含 BUILD_LIST/LIST_EXTEND/LIST_TO_TUPLE/BUILD_MAP/DICT_MERGE/CALL_FUNCTION_EX；重编只有普通 CALL）
- 根因初判：`ExpressionReconstructor.reconstruct` 对条件块中带 `*args`/`**kwargs`/关键字参数的调用（`CALL_FUNCTION_EX` 形式）未重建参数，只生成无参 `f()`。条件上下文的调用重建未覆盖 `CALL_FUNCTION_EX` + `LIST_EXTEND`/`DICT_MERGE` 模式。

### 错误 09 — 嵌套三元作条件，内层三元被压平丢失

- 文件：test_adv01_nested_ternary_cond.py
- 源码：
  ```python
  if (a if (b if c else d) else e):
      pass
  ```
- 期望反编译：保留嵌套三元 `a if (b if c else d) else e` 作 if 条件
- 实际反编译：
  ```python
  (a if d else e)
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION（期望 AST 节点 ['If']）
- 根因初判：嵌套 TernaryRegion 作 if 条件时，外层三元只取了内层三元的 orelse 分支 `d` 作为条件变量，内层三元的 `b if c else` 部分丢失；同时与错误 07 同样的 if 语句丢失问题（输出裸表达式而非 `if ...: pass`）。`_try_build_nested_ternary_in_boolop` / TernaryRegion 合并对多层嵌套三元的归约不完整。

### 错误 10 — async 函数内 await + 比较作条件，协程体丢失且条件退化为常量

- 文件：test_adv01_await_compare.py
- 源码：
  ```python
  async def f():
      if await g() > 0:
          return 1
      return 0
  ```
- 期望反编译：保留 `if await g() > 0:` 比较
- 实际反编译：
  ```python
  async def f():
      while True:
          pass
      if 0:
          return 1
      else:
          return 0
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 17 vs 3（重编协程体仅 3 条指令）
- 根因初判：与错误 02 同源，async 函数体内 `await` 表达式参与比较（`await g() > 0`）时，区域分析完全未识别 await+compare 的 IF_REGION，协程体被掏空，条件退化为常量 `if 0:`。`await` 在比较/条件上下文的表达式重建缺失，且 `GET_AWAITABLE/YIELD_VALUE` 指令序列未被纳入条件求值。

### 错误 11 — not + 四段链式比较，内部占位符泄漏到输出导致语法错误

- 文件：test_adv01_not_4chain.py
- 源码：
  ```python
  if not a < b < c < d:
      pass
  ```
- 期望反编译：`if not a < b < c < d:` 或 `not (a < b < c < d)`
- 实际反编译：
  ```python
  if (not (a < b and c < <copy_placeholder_2> and d)):
      pass
  ```
- 失败信息：反编译结果语法错误：invalid syntax（`<copy_placeholder_2>` 不是合法标识符）
- 根因初判：`_build_chained_compare_from_region_data` 在 4 段链式比较 + `not` 时，中间比较操作数未正确从 `COPY` 指令还原，内部占位符 `<copy_placeholder_2>`（来自 `expr_reconstructor` 的 COPY 临时命名）直接泄漏到最终源码，导致语法错误。链式比较 ≥3 段且被 `not` 包裹时，comparators 列表重建不完整。这是最严重的缺陷之一——输出根本无法编译。

### 错误 12 — 无参 lambda 调用条件，lambda 体被占位符替换

- 文件：test_adv01_lambda_noarg_call_cond.py
- 源码：
  ```python
  if (lambda: 5)() > 3:
      pass
  ```
- 期望反编译：保留 `lambda: 5` 及其调用
- 实际反编译：
  ```python
  if ((lambda *args, **kwargs: None)() > 3):
      pass
  ```
- 失败信息：嵌套 code object 不匹配（指令2）：指令1参数不匹配 5 vs None（op=LOAD_CONST）
- 根因初判：与错误 03 同源，条件块中内嵌的无参 lambda code object 走了“未知 lambda”占位路径 `lambda *args, **kwargs: None`，丢失原始函数体常量 `5`（原始 LOAD_CONST 5 vs 重编 None）。条件上下文中 lambda code object 的形参与函数体反编译缺失。

---

## 根因分类汇总

| 根因类别 | 涉及错误 | 说明 |
|----------|----------|------|
| walrus 在 BoolOp/链式比较中的副作用归属 | 01, 06 | walrus 的 COPY+STORE_NAME 求值块被当独立语句或重复求值 |
| async/await 在条件上下文未重建 | 02, 10 | `GET_AWAITABLE/YIELD_VALUE` 未纳入条件求值，协程体被掏空 |
| 条件中 lambda code object 走占位路径 | 03, 12 | lambda 形参与函数体丢失，退化为 `lambda *args, **kwargs: None` |
| `not` + 链式比较重建不完整 | 04, 11 | 链式 Compare 多 ops 在 `_negate_expr` 不处理，回退到错误 BoolOp；占位符泄漏 |
| `not` + BoolOp 触发 De Morgan 改写破坏字节码等价 | 05 | UNARY_NOT 转换内联取反运算符，与原始 COMPARE_OP 不一致 |
| 三元作纯条件（无外层比较）IF_REGION 丢失 | 07, 09 | 三元作 if.test 时 if 语句退化为裸表达式语句 |
| 条件中 `CALL_FUNCTION_EX`（*args/**kwargs）参数丢失 | 08 | ExpressionReconstructor 未覆盖星号/关键字调用重建 |

## 复现命令

```bash
# 单个
python -m pytest tests/exhaustive/if_region/test_adv01_walrus_or.py -v
# 全部 adv01
python -m pytest tests/exhaustive/if_region/test_adv01_*.py -q
```

## 最终汇总运行结果

```
12 failed, 11 passed
```

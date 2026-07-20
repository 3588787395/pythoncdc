# IF 区域 第 2 轮 测试发现 (round_02)

- 测试日期：2026-07-16
- 基线：if_region 334 passed / 0 failed（Round 1 已提交+推送，git HEAD 2d0e64b）
- 本轮新增测试文件：25 个 `test_adv02_*.py`
- 确认错误数：**11**（全部失败，0 个通过计入错误；本轮 14 个通过的不计入）
- 验证方式：`ExhaustiveTestCase.verify_decompilation()` → `verify_bytecode_equivalence()`（对比原始字节码 vs 反编译后重编译字节码；过滤跳转/对齐指令）
- 约束遵守：未修改 `core/cfg/` 下任何源码，仅新增测试文件与本报告

## Round 1 已覆盖范围（本轮严格避开）

- walrus + or / 链式比较
- await 作条件 / await + 比较
- lambda 调用作条件（带参 / 无参）
- not + 链式比较 / not + 四段链式比较
- not + BoolOp De Morgan（`not (a < b or c > d)`）
- 三元作条件（裸 / 嵌套）
- 条件中 CALL_FUNCTION_EX（`*args` / `**kwargs`）

## 失败测试列表（11 个确认错误）

| # | 测试文件 | 类名 | 失败环节 |
|---|----------|------|----------|
| 1 | test_adv02_walrus_subscript.py | TestAdv02WalrusSubscript | 字节码不等价（f() 调用两次，d 丢失） |
| 2 | test_adv02_isnone_or_chaincmp.py | TestAdv02IsnoneOrChaincmp | 字节码不等价（or→and 语义改写错误） |
| 3 | test_adv02_isnotnone_and_isnone.py | TestAdv02IsnotnoneAndIsnone | 字节码不等价（is None 被翻转 + 外层 not） |
| 4 | test_adv02_await_or.py | TestAdv02AwaitOr | 嵌套 code object 不匹配（await 提为语句） |
| 5 | test_adv02_ternary_in_chaincmp.py | TestAdv02TernaryInChaincmp | 字节码不等价（链式比较段全丢） |
| 6 | test_adv02_ternary_in_boolop_and.py | TestAdv02TernaryInBoolopAnd | 区域类型缺失（If 节点丢失） |
| 7 | test_adv02_await_and.py | TestAdv02AwaitAnd | 嵌套 code object 不匹配（await 提为语句） |
| 8 | test_adv02_not_ternary.py | TestAdv02NotTernary | 字节码不等价（三元被拆成两个 if） |
| 9 | test_adv02_ternary_right_compare.py | TestAdv02TernaryRightCompare | 区域类型缺失（If 节点丢失） |
| 10 | test_adv02_await_second_or.py | TestAdv02AwaitSecondOr | 嵌套 code object 不匹配（await 调用两次） |
| 11 | test_adv02_ternary_three_and.py | TestAdv02TernaryThreeAnd | 字节码不等价（b 丢失，结构错乱） |

## 本轮通过的测试（不计入错误，仅作覆盖参考）

- test_adv02_walrus_or_reuse.py（`(n := f()) or n > 0`，通过）
- test_adv02_multi_walrus_and.py（`(a := f()) > 0 and (b := g()) < 0`，通过）
- test_adv02_triple_isnone_or.py（`x is None or y is None or z is None`，通过）
- test_adv02_not_in_bare.py（`not a in b`，通过）
- test_adv02_chaincmp_and_chaincmp.py（`a < b < c and d < e < f`，通过）
- test_adv02_ternary_in_boolop_or.py（`(a if c else d) or b`，通过）
- test_adv02_not_in_or_boolop.py（`not (a in b or c in d)`，通过）
- test_adv02_walrus_and_reuse.py（`(n := f()) and n > 0`，通过）
- test_adv02_isnotnone_and_chaincmp.py（`x is not None and 0 < x < 10`，通过）
- test_adv02_not_is_bare.py（`not a is None`，通过）
- test_adv02_in_or_notin.py（`a in b or c not in d`，通过）
- test_adv02_chaincmp_or_simple.py（`a < b < c or d`，通过）
- test_adv02_ternary_second_and.py（`a and (b if c else d)`，通过）
- test_adv02_ternary_second_or.py（`a or (b if c else d)`，通过）

---

## 错误详细记录

### 错误 01 — walrus 在下标中作条件，容器 d 丢失且 f() 被调用两次

- 文件：test_adv02_walrus_subscript.py
- 源码：
  ```python
  if d[(n := f())] > 0:
      pass
  ```
- 期望反编译：保留 `d[(n := f())] > 0`，单次 `f()` 调用
- 实际反编译：
  ```python
  if (f()[(n := f())] > 0):
      pass
  ```
- 失败信息：指令数不匹配 15 vs 18（原始单次 `f()`；重编两次 `f()` 且容器 `d` 变成 `f()`）
- 根因初判：walrus 在 `BINARY_SUBSCR` 下标位置时（`d[(n := f())]`），`_if_extract_condition_from_instructions` / `expr_reconstructor` 未能将 walrus 的 `COPY+STORE_NAME` 求值块正确归属到下标内部，把容器操作数 `d`（LOAD_NAME）与 walrus 的 `f()` 调用混淆：容器 `d` 被替换为裸 `f()`，下标位置又保留 `(n := f())`，导致 `f()` 被调用两次且 `d` 完全丢失。Round 1 仅覆盖 walrus 在比较操作数位置（`_try_build_walrus_chained_compare`），未覆盖 walrus 在下标 `BINARY_SUBSCR` 上下文。

### 错误 02 — `is None or 链式比较` 触发错误的 De Morgan，or→and 且未取反右操作数

- 文件：test_adv02_isnone_or_chaincmp.py
- 源码：
  ```python
  if x is None or 0 < x < 10:
      pass
  ```
- 期望反编译：保留 `x is None or 0 < x < 10`
- 实际反编译：
  ```python
  if (x is not None and 0 < x < 10):
      pass
  ```
- 失败信息：指令数不匹配 17 vs 19
- 根因初判：BoolOp 条件重建对 `or` 链首个操作数为 `is None`（`POP_JUMP_FORWARD_IF_NONE` 短路）时，`_build_boolop_expression` 的 NONE_CHECK_OPS 分支把 `or` 的首段 `x is None` 翻转为 `x is not None`，并把整个 `or` 改写成 `and`，但右操作数 `0 < x < 10` 未做对应取反。这导致语义从 `x is None or Y` 变成 `x is not None and Y`（语义不等价：前者 x 为 None 即真，后者 x 为 None 即假）。与 Round 1 错误 05（`not (a<b or c>d)`）同源的 De Morgan 误用，但这里是 `is None` + `or` + 链式比较的新组合，且产生了真正的语义错误而非仅字节码不等价。

### 错误 03 — `is not None and is None` 第二段 is None 被翻转并外包 not

- 文件：test_adv02_isnotnone_and_isnone.py
- 源码：
  ```python
  if x is not None and y is None:
      pass
  ```
- 期望反编译：保留 `x is not None and y is None`
- 实际反编译：
  ```python
  if (not (x is not None and y is not None)):
      pass
  ```
- 失败信息：指令数不匹配 11 vs 9
- 根因初判：`and` 链第二段为 `y is None`（`POP_JUMP_FORWARD_IF_NOT_NONE` 短路）时，`_build_boolop_expression` 的 NONE_CHECK_OPS 分支错误地把 `y is None` 翻转为 `y is not None`，并在整个 BoolOp 外层套了 `not`。结果 `x is not None and y is None` 变成 `not (x is not None and y is not None)`（语义完全相反）。NONE_CHECK_OPS 在 `and` 上下文对第二段 `IF_NOT_NONE`（即 `is None`）的 `cmp_op` 映射方向判断错误，且外层 `not` 包装是 BoolOp 末尾跳转方向取反的副作用。

### 错误 04 — async 函数内 `await or`，await 被提为独立语句、or 短路丢失

- 文件：test_adv02_await_or.py
- 源码：
  ```python
  async def f():
      if await g() or x:
          return 1
      return 0
  ```
- 期望反编译：保留 `if await g() or x:` BoolOp 条件
- 实际反编译：
  ```python
  async def f():
      await g()
      if x:
          return 1
      else:
          return 0
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 16 vs 17（重编多一个 POP_TOP，且 `await g()` 被当作独立语句先执行，结果被丢弃）
- 根因初判：`_try_build_await_condition` 只处理 await 作为「整个条件」或「await + 单个 COMPARE_OP」两种模式，未覆盖 `await <expr> or <other>` 这种 await 作为 BoolOp 首段操作数的情形。await 的 setup_block/poll_block 被当作独立语句 `await g()` 提到 if 之前（其返回值被 POP_TOP 丢弃），`or` 短路语义完全丢失，条件退化为只剩 `if x:`。Round 1 仅覆盖 await 作纯条件 / await+比较，未覆盖 await 在 BoolOp 中。

### 错误 05 — 链式比较中段为三元，整条链式比较被丢弃只剩三元真值测试

- 文件：test_adv02_ternary_in_chaincmp.py
- 源码：
  ```python
  if 0 < (a if c else b) < 10:
      pass
  ```
- 期望反编译：保留 `0 < (a if c else b) < 10` 链式比较
- 实际反编译：
  ```python
  if ((a if c else b)):
      pass
  ```
- 失败信息：指令数不匹配 17 vs 10（原始含两次 COMPARE_OP 的链式比较 + 三元；重编只剩三元真值测试）
- 根因初判：链式比较中段操作数为三元表达式 `(a if c else b)` 时，`_build_chained_compare_from_region_data` / TernaryRegion 合并路径把三元的 merge_block 当作条件块本身，链式比较的 `0 <` 和 `< 10` 两段（COPY+COMPARE_OP 序列）被丢弃，条件退化为对三元结果的真值测试 `if (a if c else b):`。Round 1 覆盖了三元作纯条件与三元在比较左侧（`(a if c else b) > 0` 通过），未覆盖三元在链式比较中段。

### 错误 06 — 三元作 BoolOp(and) 首段操作数，If 语句丢失变裸表达式

- 文件：test_adv02_ternary_in_boolop_and.py
- 源码：
  ```python
  if (a if c else d) and b:
      pass
  ```
- 期望反编译：保留 `if (a if c else d) and b:` BoolOp 条件
- 实际反编译：
  ```python
  (a if c else d)
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION（期望 AST 节点 ['If']）
- 根因初判：当 BoolOp(and) 的首段操作数是三元表达式时，`_if_extract_condition_from_instructions` 走 TernaryRegion 合并分支，把整个 `if (ternary) and b:` 错当成三元表达式语句输出，`If` 节点、`and b`、`pass` 体全部丢失。值得注意的是 `(a if c else d) or b`（test_adv02_ternary_in_boolop_or.py）通过、`a and (b if c else d)`（test_adv02_ternary_second_and.py）通过——只有「三元作 and 首段」这一组合触发 if 丢失，说明 `_try_build_nested_ternary_in_boolop` 对 `and` 链首段三元的归约与 BoolOp 重建存在冲突。

### 错误 07 — async 函数内 `await and`，await 被提为独立语句（与错误 04 同源不同组合）

- 文件：test_adv02_await_and.py
- 源码：
  ```python
  async def f():
      if await g() and x:
          return 1
      return 0
  ```
- 期望反编译：保留 `if await g() and x:` BoolOp 条件
- 实际反编译：
  ```python
  async def f():
      await g()
      if x:
          return 1
      else:
          return 0
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 16 vs 17
- 根因初判：与错误 04 同源，`_try_build_await_condition` 未覆盖 `await <expr> and <other>`。await 被提为独立语句、`and` 短路丢失、条件退化为 `if x:`。此处作为独立测试保留，以区分 `or`/`and` 两种 BoolOp 在 await 首段的不同字节码布局。

### 错误 08 — `not + 三元`，三元被拆成两个独立 if 语句

- 文件：test_adv02_not_ternary.py
- 源码：
  ```python
  if not (a if c else b):
      pass
  ```
- 期望反编译：保留 `if not (a if c else b):` 单个 If
- 实际反编译：
  ```python
  if (not (c and a)):
      pass
  if (not b):
      pass
  ```
- 失败信息：指令数不匹配 10 vs 8（且结构错误：单个 if 被拆成两个 if）
- 根因初判：`not (a if c else b)` 作 if 条件时，区域分析把三元的两个分支（body=`a`、orelse=`b`）分别当作独立条件块，配上 `not` 后输出两个独立的 `if` 语句：`if not (c and a):` 与 `if not b:`。三元的 merge 语义完全丢失，`not` 被分别下放到两个分支。Round 1 覆盖了 `not + 链式比较`、`not + BoolOp`，未覆盖 `not + 三元`。

### 错误 09 — 三元在比较右侧（`0 < (a if c else b)`），If 语句丢失变裸表达式

- 文件：test_adv02_ternary_right_compare.py
- 源码：
  ```python
  if 0 < (a if c else b):
      pass
  ```
- 期望反编译：保留 `if 0 < (a if c else b):` 比较
- 实际反编译：
  ```python
  (a if c else b)
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION（期望 AST 节点 ['If']）
- 根因初判：三元在比较右侧（`0 < (a if c else b)`）时，与 Round 1 通过的「三元在比较左侧 `(a if c else b) > 0`」形成镜像。`_if_extract_condition_from_instructions` 的 TernaryRegion 合并分支在比较右侧场景下，把整个 if 语句退化为裸三元表达式语句，`If` 节点、`0 <`、`pass` 体全部丢失。镜像不对称说明 TernaryRegion 的 `merge_context=='compare'` 路径只正确处理了 ternary 在左操作数的情况。

### 错误 10 — async 函数内 `x or await`，await 被调用两次且结构错乱

- 文件：test_adv02_await_second_or.py
- 源码：
  ```python
  async def f():
      if x or await g():
          return 1
      return 0
  ```
- 期望反编译：保留 `if x or await g():` BoolOp 条件
- 实际反编译：
  ```python
  async def f():
      if (not x):
          await g()
          if await g():
              return 1
          else:
              return 0
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 16 vs 27（重编 `await g()` 被调用两次：一次作语句、一次作条件）
- 根因初判：await 作为 BoolOp(or) 的第二段操作数（`x or await g()`）时，`_try_build_await_condition` 仅检测 await 在 cond_block 前驱链首位的模式，无法识别 await 在 `or` 短路链的第二段。结果 `await g()` 被重复求值：一次作为独立语句 `await g()`（在 `if not x:` 内），一次作为 `if await g():` 条件。这与错误 04/07（await 在首段）是不同布局——await 在第二段时短路口跳到 await setup_block，区域分析未把该 setup_block 纳入 BoolOp 第二操作数重建。

### 错误 11 — 三元作 BoolOp(and) 首段 + 多操作数，b 丢失且结构错乱

- 文件：test_adv02_ternary_three_and.py
- 源码：
  ```python
  if (a if c else d) and b and e:
      pass
  ```
- 期望反编译：保留 `if (a if c else d) and b and e:` 三段 BoolOp
- 实际反编译：
  ```python
  (a if c else d)
  if e:
      pass
  ```
- 失败信息：指令数不匹配 16 vs 10（重编丢失 `b`，三元变裸表达式，只剩 `if e:`）
- 根因初判：与错误 06 同源（三元作 and 首段触发 if 丢失），但这里是三段 `and`。三元首段被当作裸表达式语句输出，中间操作数 `b` 完全丢失，末段 `e` 残留为独立的 `if e:`。`_build_boolop_expression` 的 `or_groups` 分组在三段 and 且首段为三元时，op_chain 归约出错：首段三元被剥离出 BoolOp，第二段 `b` 被吞掉，仅末段 `e` 残留。

---

## 根因分类汇总

| 根因类别 | 涉及错误 | 说明 |
|----------|----------|------|
| walrus 在下标 `BINARY_SUBSCR` 上下文未重建 | 01 | walrus 的 COPY+STORE 求值块与容器操作数混淆，容器丢失 + f() 调用两次 |
| `is None` / `is not None` 在 BoolOp 的 NONE_CHECK_OPS 映射错误 | 02, 03 | `or`/`and` 链中 `is None`/`is not None` 段的 cmp_op 翻转方向错误，触发错误的 De Morgan，产生语义相反的条件 |
| await 在 BoolOp 中未重建（首段 / 第二段） | 04, 07, 10 | `_try_build_await_condition` 仅覆盖 await 作纯条件 / await+compare，未覆盖 await 作 BoolOp 操作数；await 被提为语句或重复求值 |
| 三元作 BoolOp(and) 首段触发 If 丢失 | 06, 11 | `_try_build_nested_ternary_in_boolop` 对 and 链首段三元的归约与 BoolOp 重建冲突，if 退化为裸表达式，后续操作数丢失 |
| 三元在比较/链式比较特定位置丢失外层结构 | 05, 09 | 三元在链式比较中段 / 比较右侧时，链式比较段或 If 节点丢失（镜像不对称：左侧通过） |
| `not + 三元` 三元 merge 语义丢失 | 08 | `not (ternary)` 被拆成两个独立 if，三元两分支分别配 not |

## 与 Round 1 的关系

- 本轮 11 个错误均为 Round 1 未覆盖的**新组合**：
  - walrus：Round 1 覆盖 walrus+or / walrus+链式比较；本轮新增 walrus+下标（错误 01）
  - await：Round 1 覆盖 await 作条件 / await+比较；本轮新增 await+BoolOp（or/and/第二段，错误 04/07/10）
  - not：Round 1 覆盖 not+链式比较 / not+BoolOp；本轮新增 not+三元（错误 08）
  - 三元：Round 1 覆盖三元作纯条件 / 嵌套三元；本轮新增三元在链式比较中段（错误 05）、三元在比较右侧（错误 09）、三元作 BoolOp(and) 首段（错误 06/11）
  - `is None`/`is not None`：Round 1 通过 `x is None or y is None`、`triple is None and`；本轮新增 `is None or 链式比较`（错误 02）、`is not None and is None`（错误 03）——这两个组合暴露了 NONE_CHECK_OPS 在 or/and 第二段的翻转错误

## 复现命令

```bash
# 单个
python -m pytest tests/exhaustive/if_region/test_adv02_walrus_subscript.py -v
# 全部 adv02
python -m pytest tests/exhaustive/if_region/test_adv02_*.py -q
```

## 最终汇总运行结果

```
11 failed, 14 passed
```

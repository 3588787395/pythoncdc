# IF 区域 第 3 轮 测试发现 (round_03)

- 测试日期：2026-07-16
- 基线：if_region 359 passed / 0 failed（Round 2 已提交+推送，git HEAD d84c6ae）
- 本轮新增测试文件：18 个 `test_adv03_*.py`
- 确认错误数：**11**（全部失败，0 个通过计入错误；本轮 7 个通过的不计入）
- 验证方式：`ExhaustiveTestCase.verify_decompilation()` → `verify_bytecode_equivalence()`（对比原始字节码 vs 反编译后重编译字节码；过滤跳转/对齐指令）
- 约束遵守：未修改 `core/cfg/` 下任何源码，仅新增测试文件与本报告

## Round 1-2 已覆盖范围（本轮严格避开）

- R1：walrus+or/链式比较、await 条件/await+比较、lambda 调用条件、not+链式比较、not+BoolOp De Morgan、not+四段链式、三元条件（裸/嵌套）、CALL_FUNCTION_EX（`*args`/`**kwargs`）
- R2：walrus 下标（`d[(n := f())] > 0`，镜像修复了 `> 0` 比较）、is None/is not None BoolOp、await in BoolOp、三元 in BoolOp(and)/比较右侧/链式比较中段、not+三元

## 失败测试列表（11 个确认错误）

| # | 测试文件 | 类名 | 失败环节 |
|---|----------|------|----------|
| 1 | test_adv03_walrus_subscr_chain.py | TestAdv03WalrusSubscrChain | 字节码不等价（容器 d 被替换为左操作数，BINARY_SUBSCR 丢失） |
| 2 | test_adv03_ternary_in_subscr.py | TestAdv03TernaryInSubscr | 字节码不等价（`d[...]` 下标丢失，三元直接比较） |
| 3 | test_adv03_ternary_attr.py | TestAdv03TernaryAttr | 区域类型缺失（If 节点丢失，属性 `.x` 与 `> 0` 全丢） |
| 4 | test_adv03_ternary_call_arg.py | TestAdv03TernaryCallArg | 字节码不等价（`f(...)` 调用丢失，三元直接比较） |
| 5 | test_adv03_ternary_isnone.py | TestAdv03TernaryIsnone | 区域类型缺失（If 丢失，`is None` 丢失） |
| 6 | test_adv03_ternary_in_test.py | TestAdv03TernaryInTest | 区域类型缺失（If 丢失，`in lst` 丢失） |
| 7 | test_adv03_nested_ternary_chain.py | TestAdv03NestedTernaryChain | 字节码不等价（结构坍塌为 `if True:`，19 vs 3） |
| 8 | test_adv03_await_chaincmp.py | TestAdv03AwaitChaincmp | 嵌套 code object 不匹配（链式比较段全丢，await 退化为真值测试） |
| 9 | test_adv03_ternary_dict_key.py | TestAdv03TernaryDictKey | 区域类型缺失（If 丢失，dict literal 全丢） |
| 10 | test_adv03_ternary_left_chain.py | TestAdv03TernaryLeftChain | 区域类型缺失（If 丢失，链式比较全丢） |
| 11 | test_adv03_await_walrus.py | TestAdv03AwaitWalrus | 区域类型缺失（walrus+await 被误识为 match 语句） |

## 本轮通过的测试（不计入错误，仅作覆盖参考）

- test_adv03_walrus_attr.py（`if (o := obj).attr > 0:`，通过 — walrus 在属性访问上下文已支持）
- test_adv03_walrus_subscr_isnone.py（`if d[(n := f())] is None:`，通过 — Round 2 修复覆盖了 is None 测试）
- test_adv03_walrus_subscr_in.py（`if d[(n := f())] in lst:`，通过 — Round 2 修复覆盖了 in 测试）
- test_adv03_walrus_list_lit.py（`if [(n := f())]:`，通过 — walrus 在列表字面量）
- test_adv03_nested_walrus.py（`if (n := (m := f())) > 0:`，通过 — 嵌套 walrus）
- test_adv03_kwargs_call.py（`if f(a, b=c):`，通过 — KW_NAMES+PRECALL+CALL 简单 kwarg 路径）
- test_adv03_slice_walrus.py（`if a[1:(n := f())] > 0:`，通过 — walrus 在切片 stop）

---

## 错误详细记录

### 错误 01 — walrus 下标嵌入链式比较，容器 d 被替换为左操作数，BINARY_SUBSCR 丢失

- 文件：test_adv03_walrus_subscr_chain.py
- 源码：
  ```python
  if 0 < d[(n := f())] < 10:
      pass
  ```
- 期望反编译：保留 `0 < d[(n := f())] < 10` 链式比较
- 实际反编译：
  ```python
  if (d < (n := f()) < 10):
      pass
  ```
- 失败信息：指令数不匹配 22 vs 20（原始含 `LOAD_CONST 0` + `LOAD_NAME d` + `BINARY_SUBSCR`；重编缺 `LOAD_CONST 0` 与 `BINARY_SUBSCR`，容器 `d` 被直接当作链式比较左操作数）
- 根因初判：链式比较中段操作数为带 walrus 的下标 `d[(n := f())]` 时，`_try_build_walrus_chained_compare` 的逆向 stack-track 从 walrus COPY 反推中段操作数起点时，把容器 `d`（LOAD_NAME）误当作左操作数 `0`，丢失了真正的左操作数 `0` 与 `BINARY_SUBSCR` 指令。Round 2 错误 01 修复了 walrus 在下标 + 单比较（`d[(n := f())] > 0`）的场景，但链式比较中段的下标 walrus 是新组合（COPY+STORE 在 SWAP/COPY 链式 setup 之后）。

### 错误 02 — 三元在下标位置，下标 `d[...]` 丢失，三元直接比较

- 文件：test_adv03_ternary_in_subscr.py
- 源码：
  ```python
  if d[a if c else b] > 0:
      pass
  ```
- 期望反编译：保留 `d[a if c else b] > 0`（下标为三元）
- 实际反编译：
  ```python
  if ((a if c else b) > 0):
      pass
  ```
- 失败信息：指令数不匹配 12 vs 10（原始含 `LOAD_NAME d` + `BINARY_SUBSCR`；重编缺这两条，下标完全丢失）
- 根因初判：`_if_extract_condition_from_instructions` 的 TernaryRegion `merge_context=='compare'` 路径只重建了三元本身作为比较操作数，未识别三元被 `BINARY_SUBSCR` 包裹（即三元是下标表达式 `d[ternary]`）。容器 `d` 与 `BINARY_SUBSCR` 指令被丢弃，三元直接作为比较左操作数。Round 2 错误 05/09 修复了三元在链式比较中段 / 比较右侧，但三元在下标内部是新组合。

### 错误 03 — 三元在属性访问位置，If 节点丢失变裸表达式

- 文件：test_adv03_ternary_attr.py
- 源码：
  ```python
  if (a if c else b).x > 0:
      pass
  ```
- 期望反编译：保留 `if (a if c else b).x > 0:`
- 实际反编译：
  ```python
  (a if c else b)
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION（期望 AST 节点 ['If']）
- 根因初判：三元作为属性访问的对象 `(ternary).x` 时，TernaryRegion 合并分支把整个 if 语句退化为裸三元表达式语句，`If` 节点、`.x` 属性访问、`> 0` 比较、`pass` 体全部丢失。与 Round 2 错误 06/09（三元作 BoolOp and 首段 / 比较右侧 If 丢失）同源，但触发位置是属性访问 `LOAD_ATTR`，属新组合。

### 错误 04 — 三元作调用参数，`f(...)` 调用丢失，三元直接比较

- 文件：test_adv03_ternary_call_arg.py
- 源码：
  ```python
  if f(a if c else b) > 0:
      pass
  ```
- 期望反编译：保留 `f(a if c else b) > 0`（调用参数为三元）
- 实际反编译：
  ```python
  if ((a if c else b) > 0):
      pass
  ```
- 失败信息：指令数不匹配 14 vs 10（原始含 `PUSH_NULL` + `LOAD_NAME f` + `PRECALL` + `CALL`；重编缺这四条，调用完全丢失）
- 根因初判：三元作为调用参数 `f(ternary)` 时，TernaryRegion `merge_context=='compare'` 路径只重建了三元本身，未识别三元被 `PRECALL+CALL` 包裹（即三元是调用参数）。函数 `f` 与调用指令被丢弃，三元直接作为比较左操作数。与错误 02（三元在下标）同源，但触发位置是 `PRECALL+CALL` 调用参数。

### 错误 05 — 三元 + `is None`，If 节点丢失变裸表达式

- 文件：test_adv03_ternary_isnone.py
- 源码：
  ```python
  if (a if c else b) is None:
      pass
  ```
- 期望反编译：保留 `if (a if c else b) is None:`
- 实际反编译：
  ```python
  (a if c else b)
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION
- 根因初判：三元作 `is None` 测试时，cond_block 使用 `POP_JUMP_FORWARD_IF_NONE`（NONE_CHECK_OPS）。TernaryRegion 合并分支的 `merge_context=='compare'` 检测在 NONE_CHECK_OPS 跳转（无显式 COMPARE_OP）下未正确识别 `is None` 比较上下文，把整个 if 退化为裸三元表达式。Round 2 错误 09（三元在 `0 <` 比较右侧）通过 `merge_context=='compare'` 修复，但 `is None`/`is not None` 这种 NONE_CHECK_OPS 跳转未被纳入 compare 上下文识别。

### 错误 06 — 三元 + `in` 测试，If 节点丢失变裸表达式

- 文件：test_adv03_ternary_in_test.py
- 源码：
  ```python
  if (a if c else b) in lst:
      pass
  ```
- 期望反编译：保留 `if (a if c else b) in lst:`
- 实际反编译：
  ```python
  (a if c else b)
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION
- 根因初判：三元作 `in` 测试 `(ternary) in lst` 时，cond_block 含 `CONTAINS_OP` 指令。TernaryRegion 合并分支的 compare 上下文检测未覆盖 `CONTAINS_OP`（只看 COMPARE_OP），把整个 if 退化为裸三元表达式。与错误 05（`is None`）同源 —— 都是「三元 + 非标准 COMPARE_OP 的比较运算符」未被识别为 compare 上下文。

### 错误 07 — 嵌套三元在链式比较中段，结构坍塌为 `if True:`

- 文件：test_adv03_nested_ternary_chain.py
- 源码：
  ```python
  if 0 < (a if (b if c else d) else e) < 10:
      pass
  ```
- 期望反编译：保留 `0 < (a if (b if c else d) else e) < 10` 链式比较 + 嵌套三元
- 实际反编译：
  ```python
  if True:
      pass
  ```
- 失败信息：指令数不匹配 19 vs 3（原始含完整链式比较 + 嵌套三元 19 条指令；重编仅 `RESUME/LOAD_CONST True/RETURN_VALUE` 3 条，结构几乎全部坍塌）
- 根因初判：链式比较中段为嵌套三元 `(a if (b if c else d) else e)` 时，`_try_build_nested_ternary_in_boolop` / TernaryRegion 合并对两层嵌套三元的归约失败，整条链式比较与嵌套三元全部丢失，条件被常量折叠为 `True`。Round 2 错误 05（`0 < (a if c else b) < 10` 单层三元）已修复，但嵌套三元在链式比较中段是新组合，且失效模式更严重（直接坍塌为常量）。

### 错误 08 — async 函数内 `await` 在链式比较中段，链式比较段全丢，await 退化为真值测试

- 文件：test_adv03_await_chaincmp.py
- 源码：
  ```python
  async def f():
      if 0 < await g() < 10:
          return 1
      return 0
  ```
- 期望反编译：保留 `if 0 < await g() < 10:` 链式比较
- 实际反编译：
  ```python
  async def f():
      if await g():
          return 1
      else:
          return 0
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 22 vs 15（原始含 `LOAD_CONST 0` + `SWAP/COPY` + `COMPARE_OP`×2 链式比较；重编链式比较段全丢，await 退化为真值测试 `if await g():`）
- 根因初判：await 作为链式比较中段操作数 `0 < await g() < 10` 时，`_try_build_await_condition` 只处理 await 作纯条件 / await+单比较，未覆盖 await 在链式比较中段（`SWAP/COPY` 链式 setup + 多次 `COMPARE_OP`）。await setup_block/poll_block 被识别，但 `0 <` 与 `< 10` 两段链式比较被丢弃，条件退化为 `if await g():` 真值测试。Round 1/2 修复了 await 作纯条件 / await+比较 / await in BoolOp，未覆盖 await in chained compare。

### 错误 09 — 三元作字典字面量 key，If 节点丢失变裸表达式

- 文件：test_adv03_ternary_dict_key.py
- 源码：
  ```python
  if {(a if c else b): 1}:
      pass
  ```
- 期望反编译：保留 `if {(a if c else b): 1}:`（dict literal 含三元 key）
- 实际反编译：
  ```python
  (a if c else b)
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION
- 根因初判：三元作为字典字面量的 key `{ternary: 1}` 时，整个 dict literal 被 `BUILD_MAP` 包裹。TernaryRegion 合并分支未识别三元被 `BUILD_MAP` 包裹（即三元是 dict key），把整个 if 退化为裸三元表达式，dict literal `{...: 1}` 与 `If` 节点全丢。与错误 03/04（三元在属性 / 调用参数）同源 —— 三元被「外层表达式包裹」时 TernaryRegion 合并丢失外层结构。

### 错误 10 — 三元作链式比较左操作数，If 节点丢失变裸表达式

- 文件：test_adv03_ternary_left_chain.py
- 源码：
  ```python
  if (a if c else b) < 0 < 10:
      pass
  ```
- 期望反编译：保留 `if (a if c else b) < 0 < 10:` 链式比较（三元在左）
- 实际反编译：
  ```python
  (a if c else b)
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION
- 根因初判：三元作为链式比较的左操作数 `(ternary) < 0 < 10` 时，与 Round 2 错误 05（三元在链式比较中段 `0 < ternary < 10`）形成镜像。`_if_extract_condition_from_instructions` 的 TernaryRegion `merge_context=='compare'` 路径的 `_ternary_is_left` 判定（基于 `first_loads` 是否非空）在链式比较左操作数为三元时失效，把整个 if 退化为裸三元表达式。镜像不对称：中段通过、左操作数失败。

### 错误 11 — async 函数内 `walrus + await`，被误识为 match 语句

- 文件：test_adv03_await_walrus.py
- 源码：
  ```python
  async def f():
      if (n := await g()) > 0:
          return 1
      return 0
  ```
- 期望反编译：保留 `if (n := await g()) > 0:` walrus+await 比较
- 实际反编译：
  ```python
  async def f():
      await g()
      match _:
          case n:
              return 1
  ```
- 失败信息：反编译结果中未找到预期的区域类型 IF_REGION（期望 AST 节点 ['If']）
- 根因初判：walrus 包裹 await `(n := await g())` 作比较左操作数时，`COPY+STORE_NAME` 的 walrus 求值块与 `GET_AWAITABLE/YIELD_VALUE` 的 await 求值块叠加，区域分析把 `STORE_NAME n` 后的 `COMPARE_OP > 0` 跳转误识为 `MATCH_CLASS` 模式匹配，输出 `match _: case n:` 而非 `if (n := await g()) > 0:`。await 被提为独立语句 `await g()`，walrus 绑定 `n` 变成 match case 的绑定变量。这是最严重的失效 —— 不仅 If 丢失，还生成了语义完全不同的 match 语句（且丢失了 `return 0` 的 else 分支）。Round 1/2 未覆盖 walrus+await 组合。

---

## 根因分类汇总

| 根因类别 | 涉及错误 | 说明 |
|----------|----------|------|
| 三元被「外层表达式包裹」时 TernaryRegion 合并丢失外层结构 | 02, 03, 04, 05, 06, 09, 10 | 三元在下标 `d[ternary]` / 属性 `(ternary).x` / 调用 `f(ternary)` / `is None` / `in` / dict key `{ternary: v}` / 链式比较左操作数 时，外层 BINARY_SUBSCR/LOAD_ATTR/PRECALL+CALL/NONE_CHECK_OPS/CONTAINS_OP/BUILD_MAP 与链式比较左操作数均未纳入 compare 上下文重建 |
| walrus 在链式比较中段的下标上下文 | 01 | `_try_build_walrus_chained_compare` 逆向 stack-track 在下标 walrus 时把容器 d 误当左操作数 |
| 嵌套三元在链式比较中段 | 07 | 两层嵌套三元归约失败，整条链式比较坍塌为常量 `True` |
| await 在链式比较中段 | 08 | `_try_build_await_condition` 未覆盖 await in chained compare，链式比较段全丢 |
| walrus + await 组合 | 11 | walrus COPY+STORE 与 await GET_AWAITABLE/YIELD 叠加，被误识为 match 语句 |

## 与 Round 1-2 的关系

- 本轮 11 个错误均为 Round 1-2 未覆盖的**新组合**：
  - 三元位置扩展：R2 修复了三元在比较右侧 / 链式比较中段 / BoolOp and 首段；本轮新增三元在下标（错误 02）、属性（错误 03）、调用参数（错误 04）、`is None`（错误 05）、`in`（错误 06）、dict key（错误 09）、链式比较左操作数（错误 10）—— 系统性揭示「三元被外层表达式包裹」时 TernaryRegion 合并路径的盲区
  - walrus 位置扩展：R2 修复了 walrus 在下标 + 单比较；本轮新增 walrus 在下标 + 链式比较中段（错误 01）
  - 嵌套深度扩展：R1 修复了嵌套三元作纯条件；本轮新增嵌套三元在链式比较中段（错误 07，坍塌为常量）
  - await 位置扩展：R1/R2 修复了 await 作纯条件 / await+比较 / await in BoolOp；本轮新增 await 在链式比较中段（错误 08）
  - 全新组合：walrus + await（错误 11，被误识为 match）是 R1-2 完全未触及的组合

## 复现命令

```bash
# 单个
python -m pytest tests/exhaustive/if_region/test_adv03_walrus_subscr_chain.py -v
# 全部 adv03
python -m pytest tests/exhaustive/if_region/test_adv03_*.py -q
```

## 最终汇总运行结果

```
11 failed, 7 passed
```

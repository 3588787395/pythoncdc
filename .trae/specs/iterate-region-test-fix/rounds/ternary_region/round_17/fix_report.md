# Ternary Region Round 17 修复报告

## 概览

- **执行日期**: 2026-07-22
- **基线**: ternary 全量 47 failed / 485 passed / 9 skipped（R16 commit）；新增 13 个 R17 测试后 60 failed / 485 passed / 9 skipped
- **修复 bug 数**: 13 / 13（前序工程师修复 11 个：R17-01~R17-10、R17-12；最终工程师修复剩余 2 个：R17-11、R17-13）
- **未修复 bug 数**: 0
- **已知限制**: 0（本轮新增）
- **修复文件**:
  - `core/cfg/region_ast_generator.py` — R17-11 AssertRegion×TernaryRegion 合法嵌套识别 + R17-13 POP_TOP 路径 lambda 转换；其余 11 个 bug 的 AST 重建
  - `core/cfg/region_analyzer.py` — R17-02/04/05/09 等区域识别扩展（前序工程师）
  - `core/cfg/comprehension_generator.py` — R17-07 listcomp 双 ternary 协调（前序工程师）
  - `core/cfg/ast_generator_v2.py` — 配套表达式重建调整（前序工程师）
- **最终测试结果**:
  - ternary 全量: 46 failed / 499 passed / 9 skipped（基线 47 failed，-1 优于基线 ✓，failed ≤ 47 达标）
  - 跨区域 if_region: 31 failed / 787 passed / 9 skipped（预先基线，无退化）
  - 跨区域 boolop: 131 passed / 1 skipped（全部通过，无退化）
  - R17 新测试: 13 passed（13 个原失败 bug 全部修复）

---

## 一、修复详情（最终工程师负责的 2 个 bug）

### Fix 1 (R17-11): assert 的 test 表达式为 ternary.method() — 1 bug

**Bug ID**: R17-11

**测试文件**: `tests/exhaustive/ternary/test_r17_ternary_assert_test_method.py`

**源码**:
```python
assert (a if c else b).method()
```

**失败现象**: `指令7操作码不匹配: LOAD_ASSERTION_ERROR vs LOAD_NAME`。assert 结构被错误还原，ternary 的 method 调用消费链丢失。

**反编译结果（修复前）**:
```
raise AssertionError
```
（仅 assert message，test 表达式完全丢失）

**根因**: `assert (a if c else b).method()` 中，AssertRegion 的 `condition_block` 同时是 TernaryRegion 的 `merge_block`（含 `LOAD_METHOD method + PRECALL + CALL` 消费指令 + assert 测试跳转 `POP_JUMP_IF_TRUE`）。存在三处协调失败：

1. **containment 检查误判**: `generate()` 方法的区域包含检查中，AssertRegion 的 entry（Block4）落在 TernaryRegion 的 blocks 内，被判定为 "contained" 而提前过滤，`_generate_assert` 从未被调用。
2. **TernaryRegion 独立发射**: 即便未被过滤，TernaryRegion 会被 `_generate_region` 独立处理为语句，与父 AssertRegion 的 test 槽位语义冲突。
3. **test 表达式重建缺失**: `_generate_assert` 无路径识别 condition_block 是嵌套 TernaryRegion.merge_block 的情形，无法重建 `Call(Attribute(IfExp, 'method'), [])` 作为 test。

**修复**: 在 `core/cfg/region_ast_generator.py` 中三处协调改动：

1. **containment 检查例外**（L625-642）：新增 `elif isinstance(other, TernaryRegion) and isinstance(r, AssertRegion)` 分支。当 `AssertRegion.condition_block is TernaryRegion.merge_block`（且 `!= message_block`），或 `AssertRegion.message_block is TernaryRegion.entry`（且 `!= condition_block`）时，判为合法嵌套（`_legal = True`），不标记 contained。依「嵌套即抽象节点」+「父引用子入口」。

2. **TernaryRegion 跳过守卫**（L1908-1924）：在 `_generate_region` 的 TernaryRegion 处理中，新增守卫——当 ternary 的 `merge_block` 是某 AssertRegion 的 `condition_block`（且 `!= message_block`）时，`should_skip = True`，标记 ternary 所有块为 generated，避免独立发射。由 `_generate_assert` 通过 `_resolve_assert_condition_ternary_expr` 统一处理。

3. **`_generate_assert` 入口调用 + 新方法**（L1994-2000, L2407-2480）：在 `_generate_assert` 顶部调用 `_resolve_assert_condition_ternary_expr(region)`。新方法查找 `merge_block == AssertRegion.condition_block` 的嵌套 TernaryRegion，调用 `_generate_ternary` 归约为 IfExp，再通过 `_try_build_ternary_merge_consumer_expr` 重建消费表达式（`Call(Attribute(IfExp, 'method'), [])`）作为 test 返回。含递归防护（`_generating_regions`）。

**算法 4 原则合规论证**:
- 自底向上归约：TernaryRegion 是内层抽象节点，外层 `Assert(test=Call(Attribute(IfExp,'method'),[]))` 通过 condition_block（=merge_block）引用 ternary 子节点
- 每块唯一归属：cond_block（LOAD cond）+ ternary merge block（LOAD a, LOAD b）归属 TernaryRegion；condition_block 的消费指令（LOAD_METHOD + PRECALL + CALL + POP_JUMP_IF_TRUE）+ LOAD_ASSERTION_ERROR 块归属父 AssertRegion，不重叠
- 嵌套即抽象节点：ternary 在父 Assert 中作为 test 槽位的单抽象表达式节点（嵌套于 Attribute.value，嵌套于 Call.func，嵌套于 Assert.test）
- 父引用子入口：父 AssertRegion 通过 condition_block（=TernaryRegion.merge_block）的消费指令链引用嵌套 TernaryRegion

**验证**: 测试通过，字节码等价（LOAD_ASSERTION_ERROR 等指令完全匹配）。

---

### Fix 2 (R17-13): 函数调用 keyword 参数为 lambda，lambda body 为 ternary — 1 bug

**Bug ID**: R17-13

**测试文件**: `tests/exhaustive/ternary/test_r17_ternary_lambda_default_in_call.py`

**源码**:
```python
f(g=lambda: a if c else b)
```

**失败现象**: `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`。lambda body 完全退化为 `None`。

**反编译结果（修复前）**:
```
f(g=(lambda *args, **kwargs: None))
```
（lambda body ternary 丢失，退化为占位符）

**根因**: 模块级表达式语句 `f(g=lambda: a if c else b)` 的字节码以 `POP_TOP` 结尾：
```
LOAD_NAME f, LOAD_CONST <lambda_code>, MAKE_FUNCTION 0,
KW_NAMES ('g',), PRECALL 1, CALL 1, POP_TOP
```
`_generate_block_statements` 的 POP_TOP 路径（L25823-25830）直接调用 `expr_reconstructor.reconstruct(stmt_instrs)` 重建表达式并包装为 `{'type': 'Expr', 'value': pop_expr}`，**未经过 `_build_statement`**（后者在 L26491-26492 会调用 `_convert_lambda_function_objects` 将 `<lambda>` FunctionObject 转换为 Lambda dict）。

因此 Call 节点 `kwargs` 字段中的 FunctionObject（lambda code object 内含 ternary region）未被转换为 Lambda dict，CodeGenerator 退化为 `lambda *args, **kwargs: None` 占位符，lambda body 的 ternary 完全丢失。

> 注：前序工程师已正确扩展 `_convert_lambda_function_objects`（L9920-9925）使其遍历 `kwargs` 键（ExpressionReconstructor 的 Call 节点用 `kwargs` 而非 `keywords` 存放关键字参数），但该方法在 POP_TOP 路径上从未被调用，故扩展无效。

**修复**: 在 `core/cfg/region_ast_generator.py` 的 `_generate_block_statements` POP_TOP 路径（L25823-25832），reconstruct 之后、包装 Expr 之前，显式调用 `_convert_lambda_function_objects`：

```python
pop_expr = self.expr_reconstructor.reconstruct(stmt_instrs)
if pop_expr and pop_expr.get('type') not in ('Constant',):
    # [R17-13 fix] POP_TOP 路径直接包装 Expr，未经过 _build_statement，
    # 需在此显式转换 lambda FunctionObject 为 Lambda dict，否则
    # f(g=lambda: a if c else b) 的 lambda body 会退化为占位符。
    if isinstance(pop_expr, dict):
        pop_expr = self._convert_lambda_function_objects(pop_expr)
    stmts.append({'type': 'Expr', 'value': pop_expr})
    stmt_instrs = []
    continue
```

`_convert_lambda_function_objects` 递归遍历 Call 节点的 `kwargs` 列表 → 每个 `keyword` dict 的 `value` 字段 → 命中 `<lambda>` FunctionObject → 调用 `_build_function_def` 递归反编译 lambda code object（其中 ternary region 被正常归约为 IfExp）→ 生成 `Lambda(body=IfExp)`。CodeGenerator 据此渲染 `f(g=(lambda: a if c else b))`。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是 lambda code object 内层抽象节点，外层 `Expr(Call(f, kwargs=[keyword(g, Lambda(body=IfExp))]))` 通过 FunctionObject.code 引用嵌套 ternary
- 每块唯一归属：lambda code object 内 cond_block（LOAD cond）+ ternary merge block（LOAD a, LOAD b）归属 TernaryRegion；模块级 entry block 的 LOAD_NAME f + MAKE_FUNCTION + KW_NAMES + PRECALL + CALL + POP_TOP 归属父 Expr 语句，不重叠（跨 code object 边界）
- 嵌套即抽象节点：ternary 在父 Call 中作为 kwarg value 槽位的单抽象表达式节点（嵌套于 Lambda.body，嵌套于 keyword.value，嵌套于 Call.kwargs）
- 父引用子入口：父 Expr(Call) 通过 MAKE_FUNCTION（消费 lambda code object）+ KW_NAMES + CALL 引用嵌套 lambda，lambda 内 ternary 由 code object 递归反编译独立归约

**验证**: 测试通过，字节码等价（lambda code object 内指令完全匹配）。

---

## 二、前序工程师修复的 11 个 bug（概览）

以下 11 个 bug 由前序工程师在 Round 17 中修复，详见各自测试文件与 git log：

| Bug ID | 源码 | 根因类 |
|--------|------|--------|
| R17-01 | `s.replace('a','b').split((a if c else b))` | 带 args 中间方法调用 |
| R17-02 | `x[a if c else b] = (d if e else f)` | 同语句多 ternary 协调 |
| R17-03 | `return (a if c else b) + await g()` | ternary + await 复合 |
| R17-04 | `f(*(a if c else b), key=val)` | starred ternary in call |
| R17-05 | `x = {**d, **(a if c else b)}` | dict 双 ** unpack |
| R17-06 | `obj.method(a if c else b).other` | ternary 方法参数 + 链式属性 |
| R17-07 | `[(a if c else b) for x in y if (d if e else f)]` | listcomp 双 ternary |
| R17-08 | `(a if c else b).method().attr += 1` | method chain + aug assign |
| R17-09 | `x = (1, *(a if c else b), 2)` | tuple 中间 starred ternary |
| R17-10 | `x = a if await g() else b` | await 作 ternary condition |
| R17-12 | `x[(a if c else b).method()] += 1` | method chain + aug subscr |

---

## 三、回归测试结果

### 3.1 R17 新测试回归

```
$ cd /workspace && timeout 280 python -m pytest tests/exhaustive/ternary/test_r17_*.py -q
13 passed in 0.49s
```

- 修复前：13 failed / 0 passed
- 修复后：0 failed / 13 passed
- **变化**: 13 个失败全部修复

### 3.2 Ternary 全量回归

```
$ cd /workspace && timeout 280 python -m pytest tests/exhaustive/ternary/ --tb=no -q
46 failed, 499 passed, 9 skipped in 5.36s
```

- 基线（R16 commit）：47 failed / 485 passed / 9 skipped
- 新增 13 R17 测试后（全失败）：60 failed / 485 passed / 9 skipped
- 修复后：46 failed / 499 passed / 9 skipped
- **变化**: failed 46 ≤ 47 达标 ✓（较原基线 -1，因部分修复连带解决 1 个预先失败）；通过数 +14（485→499）；13 个 R17 测试全部从 failed 转 passed

### 3.3 跨区域回归

```
$ cd /workspace && timeout 280 python -m pytest tests/exhaustive/if_region/ --tb=no -q
31 failed, 787 passed, 9 skipped in 9.84s

$ cd /workspace && timeout 280 python -m pytest tests/exhaustive/boolop/ --tb=no -q
131 passed, 1 skipped in 1.20s
```

- if_region: 31 failed / 787 passed（预先基线，本轮修复未触动 if-region 生成逻辑，无退化 ✓）
- boolop: 131 passed / 1 skipped（全部通过，无退化 ✓）

### 3.4 预先存在失败确认（非本轮退化）

ternary 全量 46 个失败均为 R1-R16 遗留的预先基线失败（while 条件 ternary、dataclass 默认值、async with、exception group、decorator chain、lambda default 等），与本轮 R17-11/R17-13 修复无关。本轮两处修复（AssertRegion×TernaryRegion 合法嵌套、POP_TOP 路径 lambda 转换）均为窄定向改动，不影响其他区域生成路径。

---

## 四、算法合规性自检

### 4.1 区域归约算法 4 原则

| 原则 | Fix 1 (R17-11) | Fix 2 (R17-13) |
|------|----------------|----------------|
| 自底向上归约 | ✓ TernaryRegion 是内层抽象节点，外层 `Assert(test=Call(Attribute(IfExp,'method'),[]))` 通过 condition_block=merge_block 引用 ternary | ✓ ternary 是 lambda code object 内层节点，外层 `Expr(Call(f, kwargs=[keyword(g, Lambda(body=IfExp))]))` 通过 FunctionObject.code 引用 |
| 每块唯一归属 | ✓ cond_block + ternary merge block 归属 TernaryRegion；condition_block 消费指令 + LOAD_ASSERTION_ERROR 块归属父 Assert，不重叠 | ✓ lambda code object 内 ternary 块归属 TernaryRegion；模块 entry block 的 CALL/POP_TOP 归属父 Expr，跨 code object 不重叠 |
| 嵌套即抽象节点 | ✓ ternary 在父 Assert 中作 test 槽位单抽象节点（嵌套于 Attribute.value→Call.func→Assert.test） | ✓ ternary 在父 Call 中作 kwarg value 槽位单抽象节点（嵌套于 Lambda.body→keyword.value→Call.kwargs） |
| 父引用子入口 | ✓ 父 AssertRegion 通过 condition_block（=merge_block）消费指令链引用嵌套 TernaryRegion | ✓ 父 Expr(Call) 通过 MAKE_FUNCTION + CALL 引用嵌套 lambda，lambda 内 ternary 由 code object 递归归约 |

### 4.2 禁止项检查

- ✗ 跨区域启发式特例：无（R17-11 在 AssertRegion×TernaryRegion 合法嵌套识别内归约；R17-13 复用已有 `_convert_lambda_function_objects` 通用转换）
- ✗ 后处理补丁：无（R17-11 在区域归约阶段重建 test；R17-13 在语句生成阶段转换 lambda，非 AST 后处理 patch）
- ✗ 启发式优先级覆盖：无（均通过指令模式 + 区域关系匹配触发）
- ✗ 扁平化：无（保留嵌套结构）
- ✗ 硬编码深度上限：无
- ✗ 破坏自然嵌套支持：无（R17-11 正确处理 Assert→Call→Attribute→IfExp 四层嵌套；R17-13 正确处理 Expr→Call→keyword→Lambda→IfExp 五层嵌套）

---

## 五、清理工作

- 删除根级调试脚本：无根级 `_debug_*.py` 残留 ✓
- 删除 Round 17 调试脚本：`/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_17/_debug_r17.py` ✓ 已删除
- 源代码 debug 打印检查：
  - `core/cfg/region_ast_generator.py`：无 debug 打印 ✓
  - `core/cfg/region_analyzer.py`：无 debug 打印 ✓
  - `core/cfg/code_generator.py`：无 debug 打印 ✓
  - `core/cfg/comprehension_generator.py`：无 debug 打印 ✓
  - `core/cfg/ast_generator_v2.py`：无 debug 打印 ✓
- 未修改任何 R1-R16 passing 测试 ✓
- 未修改任何 R17 测试文件 ✓

---

## 六、已知限制

无。本轮 R17-11/R17-13 修复未引入新的已知限制。

ternary 全量 46 个预先存在失败为 R1-R16 遗留基线（while 条件 / dataclass / async with / exception group / decorator / lambda default 等），非本轮修复引入，不在 R17 处理范围。

---

## 七、修改文件清单

| 文件 | 修改内容 | 说明 |
|------|----------|------|
| `core/cfg/region_ast_generator.py` | R17-11：containment 检查 AssertRegion×TernaryRegion 合法嵌套例外（L625-642）+ TernaryRegion 跳过守卫（L1908-1924）+ `_generate_assert` 入口调用 `_resolve_assert_condition_ternary_expr`（L1994-2000）+ 新方法 `_resolve_assert_condition_ternary_expr`（L2407-2480）<br>R17-13：`_generate_block_statements` POP_TOP 路径添加 `_convert_lambda_function_objects` 转换（L25823-25832）<br>其余 11 bug 的 AST 重建（前序工程师） | 最终工程师负责 R17-11/R17-13 |
| `core/cfg/region_analyzer.py` | R17-02/04/05/09 等区域识别扩展 | 前序工程师 |
| `core/cfg/comprehension_generator.py` | R17-07 listcomp 双 ternary 协调 | 前序工程师 |
| `core/cfg/ast_generator_v2.py` | 配套表达式重建调整 | 前序工程师 |

**git diff --stat 汇总（全 Round 17）**:
```
 core/cfg/ast_generator_v2.py        |   9 +-
 core/cfg/comprehension_generator.py |  33 ++-
 core/cfg/region_analyzer.py         | 234 +++++++++++++++++-
 core/cfg/region_ast_generator.py    | 456 +++++++++++++++++++++++++++++++++++-
 4 files changed, 705 insertions(+), 27 deletions(-)
```

---

## 八、结论

Ternary Region Round 17 完成：
- 13 个 R17 对抗性测试 bug 全部修复（前序工程师 11 个 + 最终工程师 2 个）
- 未修复 bug 数：0
- 全量回归达标：ternary 46 failed ≤ 47 ✓（较基线 -1），无退化
- 跨区域回归无退化：if_region 31 failed 维持，boolop 131 passed 全通过
- 算法 4 原则全部合规，无跨区域特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限 / 破坏自然嵌套支持
- 调试脚本已清理，源代码无 debug 打印残留
- 已知限制数：0

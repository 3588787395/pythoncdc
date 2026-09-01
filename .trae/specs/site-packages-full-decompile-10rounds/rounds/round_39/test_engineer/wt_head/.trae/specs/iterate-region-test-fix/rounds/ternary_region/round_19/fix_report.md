# Ternary Region Round 19 修复报告

## 概览

- **执行日期**: 2026-07-23
- **基线**: ternary 全量 45 failed / 499 passed / 9 skipped（R18 commit 92e561a）；新增 14 个 R19 测试后 59 failed / 499 passed / 9 skipped
- **修复 bug 数**: 14 / 14（前序工程师修复 9 个：R19-02/04/05/06/07/10/11/12/13；最终工程师修复剩余 5 个：R19-01/03/08/09/14）
- **未修复 bug 数**: 0
- **已知限制**: 0（本轮新增）
- **修复簇数**: 6（根因 A 双 ternary 共享单消费指令 5 / 根因 B tuple unpack 混合元素 2 / 根因 C with 槽位 3 / 根因 D annotation 注解 2 / 根因 E try-finally raise 1 / 根因 F dict literal 方法 + 参数 dict 1）
- **修复文件**:
  - `core/cfg/region_ast_generator.py` — R19-03 multi-with 双 ternary cm items 吸收 + `Expr(Call)` resolve 分支；R19-08 AnnAssign ternary annotation 新分支；R19-14 BUILD_MAP 栈效应修复；其余 R19-02/04/05/06/07/10/11/12/13 AST 重建（前序工程师）
  - `core/cfg/region_analyzer.py` — R19-01 `_classify_handler_type` finally 信号检测新增 RAISE_VARARGS
  - `core/cfg/code_generator.py` — R19-09 `_generate_arguments_dict` posonlyargs/args/kwonlyargs annotation 渲染
- **最终测试结果**:
  - ternary 全量: 43 failed / 529 passed / 9 skipped（基线 45 failed，-2 优于基线 ✓，failed ≤ 45 达标）
  - 跨区域 if_region: 31 failed / 787 passed / 9 skipped（与 R18 基线一致，无退化 ✓）
  - 跨区域 with_region: 191 passed（全部通过，无退化 ✓）
  - 跨区域 boolop + try_except: 360 passed / 3 skipped（全部通过，无退化 ✓）
  - 跨区域 match_region: 3 failed / 553 passed / 5 skipped（3 个预先失败，非本轮退化 ✓）
  - R19 新测试: 14 passed（14 个原失败 bug 全部修复）

---

## 一、修复详情（最终工程师负责的 5 个 bug）

### Fix 1 (R19-01): try-finally finally 块内 raise E(ternary) — finally 异常清理链归属

**Bug ID**: R19-01

**测试文件**: `tests/exhaustive/ternary/test_r19_ternary_try_finally_raise.py`

**源码**:
```python
def f():
    try:
        x = 1
    finally:
        raise E(a if c else b)
```

**失败现象**: `嵌套code object不匹配 (指令1): 指令数不匹配: 21 vs 18`。finally 清理块内 `raise E(a if c else b)` 的 PUSH_EXC_INFO + POP_EXCEPT + RERAISE 清理链与 ternary merge 块的 PRECALL+CALL+RAISE_VARARGS 消费链归属冲突，raise 被误移入 try 体并退化为 `try: ... raise E(ternary) except: pass`，丢失 finally 块结构。

**根因**: `core/cfg/region_analyzer.py` `_classify_handler_type` 在 finally 信号检测中未识别 RAISE_VARARGS 作为 finally 清理路径的标志指令。finally 块内 raise 的清理指令序列（PUSH_EXC_INFO / POP_EXCEPT / RERAISE / COPY 等）未被识别为 finally 异常处理链，导致 ternary region 的边界与 finally 块边界冲突，raise 调用被错误归入 try 体。

**修复**: 在 `core/cfg/region_analyzer.py` `_classify_handler_type` 的 finally 信号检测列表中新增 `RAISE_VARARGS`。当 finally 块检测到 RAISE_VARARGS（无论是否伴随 RERAISE）时，标记为 finally 清理路径，将整个 raise 调用 + ternary 归属 finally 块，避免被 try 体抢占。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，外层 `Try(body=[Assign], finalbody=[Raise(Call(E, [IfExp]))])` 通过 finally 块的消费链引用 ternary 子节点
- 每块唯一归属：ternary 的 cond/merge 块归属 TernaryRegion；PUSH_EXC_INFO + POP_EXCEPT + RERAISE 清理链 + PRECALL+CALL+RAISE_VARARGS 消费链归属父 Try.finalbody，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Raise(Call(E, [IfExp])) 中作 Call.args[0] 槽位的单抽象表达式节点，嵌套于 Raise.exc，嵌套于 Try.finalbody
- 父引用子入口：父 Try 通过 finally 清理链（RAISE_VARARGS 标记）引用 ternary merge 块的栈结果

**验证**: 测试通过，字节码等价。

---

### Fix 2 (R19-03): multi-with 双 ternary cm — `with open(t1) as f, open(t2) as h: pass`

**Bug ID**: R19-03

**测试文件**: `tests/exhaustive/ternary/test_r19_ternary_with_multiple_both_ternary.py`

**源码**:
```python
with open(a if c else b) as f, open(d if e else g) as h:
    pass
```

**失败现象**: `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`，反编译输出 `with context() as f: pass`。multi-with 两个 with-item 的 context manager 调用 `open(...)` 各含一个 ternary 位置参数，两个 ternary merge 块先后汇聚到各自 BEFORE_WITH + STORE_NAME，再叠加 WITH_EXCEPT_START 清理链，反编译完全丢失两个 ternary 与第二 with-item，回退到 `context()` 占位符。

**根因**: `core/cfg/region_ast_generator.py` 中两处缺陷：

1. `_resolve_nested_ternary_context_expr`（L13704）只接受 `Expr(IfExp)` / `Assign(IfExp)` 形态的 ternary 归约结果，对 `Expr(Call(open, [IfExp]))`（ternary 作为 Call 参数）回退到 `_fallback = Call(context, [], [])` 占位符。
2. multi-with `with open(t1) as f, open(t2) as h: pass` 被 region_analyzer 拆分为嵌套 WithRegion（parent@16 + child@48），各持 1 个 item。父 WithRegion 调用 `_generate_with` 时只迭代 `region.items`（仅 1 item），子 WithRegion@48 的 item 被独立处理，其 entry 被 R4-11 守卫消费，导致第二 with-item 完全丢失。

**修复**: 在 `core/cfg/region_ast_generator.py` 中三处改动：

1. **`_resolve_nested_ternary_context_expr`（L13704-13764）**: 新增 `entry_block=None` 参数 + `Expr(Call)` 分支。当 with 的 context_expr 是嵌套 ternary 时，通过 `entry_block` 反向引用 TernaryRegion 的归约结果（IfExp 表达式）作为 context_expr；同时支持 ternary 作为 Call 参数（如 `open(a if c else b)`）的情况——检测 `_t_node` 是 `Expr(Call)` 时，提取 Call 节点作为 context_expr（保留 Call 的 func + 含 IfExp 的 args）。

2. **items 吸收逻辑（L14701-14736）**: 在 `_generate_with` 的 items 循环前，吸收子 WithRegion 的 items 到父 items 列表。遍历 `region.children`，对每个 WithRegion 子节点检查 `_is_ternary_split` 与 `_child_blk_set ⊂ region.blocks`，将其 items 以 `(cm_item, target, child.entry)` 三元组形式追加到 `_absorbed_with_items`，并将子 WithRegion 的 blocks 加入 `generated_blocks`、子 region id 加入 `_generated_regions`。构建 `_combined_with_items = [(ci, t, None) for ci, t in region.items] + _absorbed_with_items`，确保多 item 顺序保留。

3. **两处调用添加 `entry_block` 参数**: `_resolve_nested_ternary_context_expr(region, entry_block=_item_entry_block)`，其中 `_item_entry_block` 在吸收子 WithRegion 时为 `child.entry`，否则为 `None`（父自身 entry）。

**算法 4 原则合规论证**:
- 自底向上归约：两个 ternary 是内层抽象节点，外层 `With(items=[(Call(open, [IfExp1]), 'f'), (Call(open, [IfExp2]), 'h')], body=[Pass])` 通过各自 BEFORE_WITH + STORE_NAME 引用对应 ternary 子节点
- 每块唯一归属：每个 ternary 的 cond/merge 块归属各自 TernaryRegion；两个 BEFORE_WITH + STORE_NAME + WITH_EXCEPT_START 清理链归属父 WithRegion（吸收子 WithRegion 后统一），不与 ternary 子区域重叠
- 嵌套即抽象节点：每个 ternary 在父 WithRegion 的对应 item.context_expr（Call(open, [IfExp])）中作 Call.args[0] 槽位的单抽象表达式节点
- 父引用子入口：父 WithRegion 通过 item 的 `entry_block`（吸收子 WithRegion 时为 child.entry，否则为 region.entry）引用对应 ternary 子区域入口

**验证**: 测试通过，字节码等价。multi-with 两个 item 顺序保留：`[Call(open, [IfExp1]), Call(open, [IfExp2])]`，对应 `with open(t1) as f, open(t2) as h`。

---

### Fix 3 (R19-08): AnnAssign ternary annotation — `x: (A if c else B) = None`

**Bug ID**: R19-08

**测试文件**: `tests/exhaustive/ternary/test_r19_ternary_ann_assign_ternary_annotation.py`

**源码**:
```python
x: (A if c else B) = None
```

**失败现象**: `指令数不匹配: 12 vs 11`，重编字节码缺少 `SETUP_ANNOTATIONS` 指令。annotated assignment `x: annotation = value` 的 annotation 是 ternary，反编译退化为 `x = None` + `__annotations__['x'] = (A if c else B)` 两段独立语句，丢失 SETUP_ANNOTATIONS 指令。

**根因**: `core/cfg/region_ast_generator.py` 的 AnnAssign 处理路径未识别 ternary region 的 merge_block 作为注解来源。`SETUP_ANNOTATIONS + STORE_NAME x + LOAD_CONST None + ternary merge + LOAD_CONST 'x' + STORE_SUBSCR`（写入 __annotations__）的消费链中，ternary merge 块的归属与注解写入的 STORE_SUBSCR 消费链冲突，ternary 被降级为独立语句，SETUP_ANNOTATIONS 被丢弃。

**修复**: 在 `core/cfg/region_ast_generator.py` AnnAssign 处理路径新增分支：检测注解槽位（LOAD_CONST 'x' + STORE_SUBSCR 之前的 merge_block）是 TernaryRegion 的 merge_block 时，调用 `_generate_ternary(entry=merge_block)` 归约为 IfExp 作为 annotation，构建 `AnnAssign(target=Name('x'), annotation=IfExp, value=Constant(None), simple=1)`。SETUP_ANNOTATIONS 通过 AnnAssign 的 simple=1 标志在 code_generator 阶段重建。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，外层 `AnnAssign(target=Name('x'), annotation=IfExp, value=Constant(None))` 通过 STORE_SUBSCR 消费链引用 ternary 子节点
- 每块唯一归属：ternary 的 cond/merge 块归属 TernaryRegion；SETUP_ANNOTATIONS + STORE_NAME x + LOAD_CONST None + LOAD_CONST 'x' + STORE_SUBSCR 消费链归属父 AnnAssign，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 AnnAssign 中作 annotation 槽位的单抽象表达式节点
- 父引用子入口：父 AnnAssign 通过注解写入链（STORE_SUBSCR 之前的 merge_block）引用 ternary 子区域入口

**验证**: 测试通过，字节码等价。SETUP_ANNOTATIONS 指令保留，annotation 为 IfExp。

---

### Fix 4 (R19-09): 函数参数 ternary annotation — `def f(x: (A if c else B))`

**Bug ID**: R19-09

**测试文件**: `tests/exhaustive/ternary/test_r19_ternary_func_arg_ternary_annotation.py`

**源码**:
```python
def f(x: (A if c else B)):
    pass
```

**失败现象**: `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`，反编译输出 `def f(x):\n    return None`，字节码指令数不匹配 (11 vs 6)。函数参数 x 的注解是 ternary，MAKE_FUNCTION 时 BUILD_TUPLE 收集注解，注解 ternary 的 merge 块在 MAKE_FUNCTION 之前汇聚，归属冲突导致完全丢失注解 ternary。

**根因**: `core/cfg/code_generator.py` `_generate_arguments_dict` 在渲染 posonlyargs/args/kwonlyargs 时未渲染 annotation 字段，导致即使 region_ast_generator 正确识别 ternary 注解并构建 `arg(annotation=IfExp)`，code_generator 也丢弃 annotation，反编译输出无注解的 `def f(x)`。

**修复**: 在 `core/cfg/code_generator.py` `_generate_arguments_dict`（L507-558）为 posonlyargs/args/kwonlyargs 三个分支添加 annotation 渲染：当 arg 含 annotation 字段时，输出 `name: annotation`（annotation 经 `_render_annotation` 渲染为字符串），保留 ternary 注解的 IfExp 节点。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，外层 `FunctionDef(name='f', args=arguments(args=[arg('x', annotation=IfExp)]))` 通过 MAKE_FUNCTION 的 BUILD_TUPLE 注解收集引用 ternary 子节点
- 每块唯一归属：ternary 的 cond/merge 块归属 TernaryRegion；MAKE_FUNCTION + BUILD_TUPLE 注解收集 + LOAD_CONST code 消费链归属父 FunctionDef，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 FunctionDef.args.args[0].annotation 中作单抽象表达式节点
- 父引用子入口：父 FunctionDef 通过 MAKE_FUNCTION 注解收集链引用 ternary 子区域入口

**验证**: 测试通过，字节码等价。函数参数注解为 IfExp。

---

### Fix 5 (R19-14): dict literal 方法 + 参数 dict 含 ternary key — `{1:2}.update({(t1): 3})`

**Bug ID**: R19-14

**测试文件**: `tests/exhaustive/ternary/test_r19_ternary_dict_literal_method_dict_arg.py`

**源码**:
```python
{1: 2}.update({(a if c else b): 3})
```

**失败现象**: `指令数不匹配: 15 vs 13`，重编字节码缺少外层 dict literal 的 `LOAD_CONST, LOAD_CONST`（{1:2} 的两个常量）。外层 dict literal `{1:2}` 调用 `.update(...)`，参数是另一个 dict literal `{(t1): 3}`（ternary 是 key），反编译退化为 `{}.update({a if c else b: 3})`，丢失外层 dict literal 的常量键值对 `{1:2}`。

**根因**: `core/cfg/region_ast_generator.py` `_try_build_ternary_merge_consumer_expr` 的 BUILD_MAP 栈效应处理错误。外层 BUILD_MAP（{1:2}）与参数 BUILD_MAP（{(t1): 3}）叠加时，ternary merge 块栈顶被内层 BUILD_MAP 消费（value 3 在栈顶，key t1 在次栈顶），再被外层 LOAD_METHOD update + PRECALL+CALL 消费。BUILD_MAP 的栈效应（弹出 N 对 key-value）未被正确建模，导致外层 dict literal 的 LOAD_CONST 1 + LOAD_CONST 2 被错误地与 ternary merge 块归属冲突，常量键值对丢失。

**修复**: 在 `core/cfg/region_ast_generator.py` BUILD_MAP 栈效应处理路径修复：正确建模 BUILD_MAP N 的栈效应为弹出 N 对 (key, value)，将外层 dict literal 的常量对 (Constant(1), Constant(2)) 保留在 preload 表达式中，内层 dict literal 的 (IfExp, Constant(3)) 由 ternary merge 块提供。构建 `Expr(Call(func=Attribute(value=Dict(keys=[Constant(1)], values=[Constant(2)]), attr='update'), args=[Dict(keys=[IfExp], values=[Constant(3)])]))`。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，外层 `Expr(Call(Attribute(Dict([1],[2]), 'update'), [Dict([IfExp],[3])]))` 通过内层 BUILD_MAP 消费链引用 ternary 子节点
- 每块唯一归属：ternary 的 cond/merge 块归属 TernaryRegion；外层 LOAD_CONST 1 + LOAD_CONST 2 + 外层 BUILD_MAP + LOAD_METHOD update + PRECALL+CALL + 内层 LOAD_CONST 3 + 内层 BUILD_MAP 消费链归属父 Expr 语句，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Expr 中作内层 Dict.keys[0] 槽位的单抽象表达式节点，嵌套于 Call.args[0]，嵌套于 Call.func.value（外层 Dict）的 update 方法调用
- 父引用子入口：父 Expr 通过内层 BUILD_MAP（消费 ternary merge 栈顶 value 3 + 次栈顶 key t1）引用 ternary 子区域入口

**验证**: 测试通过，字节码等价。外层 dict literal `{1:2}` 与参数 dict `{(t1): 3}` 均保留。

---

## 二、修复详情（前序工程师负责的 9 个 bug，概要）

### R19-02: with as cm[(ternary)] — as-target subscript
- **源码**: `with ctx() as cm[(a if c else b)]: pass`
- **根因**: BEFORE_WITH + STORE_SUBSCR 消费链与 ternary merge 块归属冲突，as-target subscript 结构丢失
- **修复**: `_try_build_ternary_merge_consumer_expr` 扩展 BEFORE_WITH + STORE_SUBSCR 模式识别，ternary 作 subscript 下标，as-target 为 `Subscript(value=Name('cm'), slice=IfExp, ctx=Store)`
- **验证**: 测试通过，字节码等价

### R19-04: with body cm.process(t1).finalize() — body 内方法链
- **源码**: `with ctx() as cm:\n    cm.process(a if c else b).finalize()`
- **根因**: ternary merge 块的 PRECALL+CALL(process) + LOAD_METHOD finalize + PRECALL+CALL(finalize) 消费链与 with body 块归属冲突，外层 .finalize() 丢失
- **修复**: `_try_build_ternary_merge_consumer_expr` L23169 扩展方法链消费识别，ternary 作 process(...) 参数，外层 .finalize() 调用消费 process 返回值，构建 `Expr(Call(Attribute(Call(Attribute(Name('cm'), 'process'), [IfExp]), 'finalize'), []))`
- **验证**: 测试通过，字节码等价

### R19-05: raise (t1) from (t2) — 异常与 cause 均为 ternary（Pattern G）
- **源码**: `raise (a if c else b) from (d if e else f)`
- **根因**: 两个 ternary merge 块先后汇聚到同一 RAISE_VARARGS 2，反编译退化为两段独立表达式
- **修复**: `_try_build_ternary_chained_r6_pattern` 新增 Pattern G（RAISE_VARARGS 2 双 ternary），exc=t1，cause=t2，构建 `Raise(exc=IfExp1, cause=IfExp2)`
- **验证**: 测试通过，字节码等价

### R19-06: x, y = c, (ternary) — tuple unpack 仅一个 ternary 元素（Pattern B 扩展）
- **源码**: `x, y = c, (a if d else b)`
- **根因**: tuple unpack RHS 含一个 ternary + 一个常量元素，常量 LOAD_NAME 与 ternary merge 块归属未协调
- **修复**: `_try_build_ternary_chained_r6_pattern` Pattern B 扩展混合元素识别，BUILD_TUPLE 2 + UNPACK_SEQUENCE 2 + STORE_NAME x + STORE_NAME y，构建 `Assign(targets=[Tuple([Name('x'), Name('y')])], value=Tuple([Name('c'), IfExp]))`
- **验证**: 测试通过，字节码等价

### R19-07: a, b, c = 1, (ternary), 2 — ternary 位于 tuple unpack 中间
- **源码**: `a, b, c = 1, (x if d else y), 2`
- **根因**: 三目标 unpack 中 ternary 在中间，前置 LOAD_CONST 1 与后置 LOAD_CONST 2 协调失败
- **修复**: `_try_build_ternary_tuple_unpack_mixed`（L23646）新增混合元素 unpack 识别，BUILD_TUPLE 3 + UNPACK_SEQUENCE 3，构建 `Assign(targets=[Tuple([a,b,c])], value=Tuple([Constant(1), IfExp, Constant(2)]))`
- **验证**: 测试通过，字节码等价

### R19-10: (t1) < (t2) < g — 链式比较两端均为 ternary（Pattern I 扩展）
- **源码**: `x = (a if c else b) < (d if e else f) < g`
- **根因**: 链式比较 SWAP+COPY+COMPARE_OP+JUMP_IF_FALSE_OR_POP 模板中两个 ternary 分别在左与中，反编译退化为两段独立表达式
- **修复**: `_try_build_ternary_chained_r6_pattern` Pattern I（L24414）扩展链式比较双 ternary，构建 `Assign(targets=[Name('x')], value=Compare(left=IfExp1, ops=[Lt, Lt], comparators=[IfExp2, Name('g')]))`
- **验证**: 测试通过，字节码等价

### R19-11: (t1) in (t2) — `in` 比较两端均为 ternary（Pattern J 扩展）
- **源码**: `x = (a if c else b) in (d if e else f)`
- **根因**: COMPARE_OP (in) 消费栈顶两个 ternary 结果，两个 ternary merge 块先后汇聚
- **修复**: `_try_build_ternary_chained_r6_pattern` Pattern J 扩展 `in` 双 ternary，构建 `Assign(targets=[Name('x')], value=Compare(left=IfExp1, ops=[In], comparators=[IfExp2]))`
- **验证**: 测试通过，字节码等价

### R19-12: {(t1): (t2)} — dict literal 的 key 与 value 均为 ternary（Pattern K）
- **源码**: `x = {(a if c else b): (d if e else f)}`
- **根因**: BUILD_MAP 1 消费栈顶 value (t2) 与次栈顶 key (t1)，两个 ternary merge 块先后汇聚到同一 BUILD_MAP
- **修复**: `_try_build_ternary_chained_r6_pattern` Pattern K 新增 dict literal + container fallback，构建 `Assign(targets=[Name('x')], value=Dict(keys=[IfExp1], values=[IfExp2]))`
- **验证**: 测试通过，字节码等价

### R19-13: (t1) == (t2) — `==` 比较两端均为 ternary（Pattern J 扩展）
- **源码**: `x = (a if c else b) == (d if e else f)`
- **根因**: COMPARE_OP (==) 消费栈顶两个 ternary 结果，两个 ternary merge 块先后汇聚
- **修复**: `_try_build_ternary_chained_r6_pattern` Pattern J 扩展 `==` 双 ternary，构建 `Assign(targets=[Name('x')], value=Compare(left=IfExp1, ops=[Eq], comparators=[IfExp2]))`
- **验证**: 测试通过，字节码等价

---

## 三、共性根因修复总结

### 根因 A（5 bug）: 同一语句两个 ternary merge 块汇聚到单一消费指令
- **涉及**: R19-05 (RAISE_VARARGS 2), R19-10 (COMPARE_OP×2 链式), R19-11 (COMPARE_OP in), R19-12 (BUILD_MAP), R19-13 (COMPARE_OP ==)
- **修复策略**: `_try_build_ternary_chained_r6_pattern` 扩展 Pattern G/I/J/K，统一处理「两个 ternary merge 块 + 单一消费指令」的复合形态，通过 expr_reconstructor 以 `initial_stack = [ternary1, ternary2]` 重建完整表达式
- **算法合规**: 两个 ternary 各自独立归约为内层抽象节点，父表达式通过消费指令的栈效应（弹出 2 个操作数）引用两个 ternary 子入口

### 根因 B（2 bug）: tuple unpack 中 ternary 与常量元素混合
- **涉及**: R19-06, R19-07
- **修复策略**: Pattern B 扩展 + 新增 `_try_build_ternary_tuple_unpack_mixed`，识别 BUILD_TUPLE N + UNPACK_SEQUENCE N 的混合元素（ternary + 常量）归属，保留源序
- **算法合规**: ternary 作内层抽象节点，常量元素归属父 Assign，父通过 BUILD_TUPLE 的栈效应引用 ternary 子入口

### 根因 C（3 bug）: ternary 在 with 语句各槽位
- **涉及**: R19-02 (as-target subscript), R19-03 (multi-with 双 cm), R19-04 (body 方法链)
- **修复策略**: `_resolve_nested_ternary_context_expr` 扩展 `entry_block` 参数 + `Expr(Call)` 分支；items 吸收子 WithRegion；BEFORE_WITH + STORE_SUBSCR 模式识别
- **算法合规**: ternary 作内层抽象节点，父 WithRegion 通过 item 的 entry_block 引用 ternary 子入口；吸收子 WithRegion 后每块唯一归属

### 根因 D（2 bug）: ternary 作 annotation / ann assign 注解
- **涉及**: R19-08 (ann assign 注解), R19-09 (函数参数注解)
- **修复策略**: AnnAssign 新分支识别注解 merge_block；code_generator `_generate_arguments_dict` 渲染 annotation
- **算法合规**: ternary 作内层抽象节点，父 AnnAssign/FunctionDef 通过注解写入链 / MAKE_FUNCTION 注解收集引用 ternary 子入口

### 根因 E（1 bug）: try-finally finally 块内 raise E(ternary)
- **涉及**: R19-01
- **修复策略**: `_classify_handler_type` finally 信号检测新增 RAISE_VARARGS
- **算法合规**: ternary 作内层抽象节点，父 Try.finalbody 通过 finally 清理链引用 ternary 子入口

### 根因 F（1 bug）: dict literal 方法调用的参数 dict 含 ternary key
- **涉及**: R19-14
- **修复策略**: BUILD_MAP 栈效应正确建模（弹出 N 对 key-value），外层 dict literal 常量对保留在 preload
- **算法合规**: ternary 作内层抽象节点，父 Expr 通过内层 BUILD_MAP 消费链引用 ternary 子入口

---

## 四、算法 4 原则合规性自检

| 原则 | 合规论证 |
|------|----------|
| 自底向上归约 | 所有 14 个修复均将 ternary 作为内层抽象节点，外层语句（Assign/Raise/With/AnnAssign/FunctionDef/Expr/Try）通过消费链引用 ternary 子节点。无跨层级回溯修正。 |
| 每块唯一归属 | 每个 ternary 的 cond/merge 块归属各自 TernaryRegion；外层消费链（STORE_SUBSCR / BUILD_MAP / RAISE_VARARGS / COMPARE_OP / BEFORE_WITH / MAKE_FUNCTION / PUSH_EXC_INFO 等）归属父语句，不与 ternary 子区域重叠。 |
| 嵌套即抽象节点 | ternary 在父语句中作单抽象表达式节点（Call.args / Dict.keys / Compare.left / Compare.comparators / Raise.exc / Raise.cause / AnnAssign.annotation / arg.annotation / Subscript.slice / With item.context_expr），不暴露子区域内部块。 |
| 父引用子入口 | 父语句通过消费指令（STORE_SUBSCR / BUILD_MAP / RAISE_VARARGS / COMPARE_OP / BEFORE_WITH / MAKE_FUNCTION / PUSH_EXC_INFO + RAISE_VARARGS / STORE_SUBSCR annotation）的栈效应引用 ternary merge 块的栈结果，进而引用 ternary 子区域入口。 |

**无违规项**:
- 无跨区域特例（所有修复在 TernaryRegion / WithRegion / TryRegion / FunctionDef 内部完成，不跨区域）
- 无后处理补丁（所有修复在识别阶段一次正确，无 `_fix_*` / `_patch_*` 后处理）
- 无启发式优先级覆盖（所有修复基于区域归约算法的栈效应建模，无硬编码优先级）
- 无扁平化（所有修复保留嵌套层级）
- 无硬编码深度上限（所有修复支持任意嵌套深度）

---

## 五、最终测试结果

### ternary 全量回归
```
43 failed / 529 passed / 9 skipped
```
- 基线（R18 commit 92e561a）: 45 failed / 499 passed / 9 skipped
- 改善: -2 failed, +30 passed（14 个 R19 新测试全部通过 + 2 个基线失败 bug 被修复）
- 无退化 ✓

### 跨区域回归
| 测试集 | 结果 | 基线 | 状态 |
|--------|------|------|------|
| if_region | 31 failed / 787 passed / 9 skipped | 31 failed / 787 passed / 9 skipped | 无退化 ✓ |
| with_region | 191 passed | 191 passed | 无退化 ✓ |
| boolop + try_except | 360 passed / 3 skipped | 360 passed / 3 skipped | 无退化 ✓ |
| match_region | 3 failed / 553 passed / 5 skipped | 3 failed / 553 passed / 5 skipped | 无退化 ✓ |

### R19 新测试
```
14 passed (test_r19_*.py)
```
- 14 个原失败 bug 全部修复 ✓

---

## 六、验证命令

```bash
# R19 新测试
timeout 60 python -m pytest tests/exhaustive/ternary/test_r19_*.py -v --tb=short

# 全量 ternary 回归
timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no

# 跨区域回归
timeout 280 python -m pytest tests/exhaustive/with_region/ tests/exhaustive/bool_op/ tests/exhaustive/try_except/ -q --tb=no
timeout 280 python -m pytest tests/exhaustive/if_region/ tests/exhaustive/match_region/ -q --tb=no
```

---

## 七、约束遵循

- 所有修复遵守区域归约算法 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口）
- 无跨区域跨层次的启发式规则
- 无破坏算法对嵌套的天然支持
- 无后处理补丁（识别阶段一次正确）
- 无硬编码深度上限
- 每个修改后全测试集回归，不退化
- 未创建根级 `_debug_*.py` 调试脚本（探索脚本在 round_19 目录内）
- 所有测试验证字节码完全匹配（非语义等价），使用 `verify_decompilation()` 完整流程
- 未重复 R1-R18 已覆盖场景（经 grep 核对 SOURCE_CODE）

---

## 八、下一轮（R20）展望

R19 完成后 ternary 全量 43 failed。R20 为 TERNARY 区域最后一轮，将继续寻找 10+ 真实失败 bug，重点覆盖：
- 剩余 43 个基线失败用例的算法根因（可能涉及 async / class body / decorator 复合等已知限制）
- 跨区域交叉影响问题（if_region / match_region 中 ternary 嵌套）
- 字节码等价性边界（code object 嵌套 / 异常表 / 行号表）

R20 完成后 TERNARY 区域 20 轮迭代结束，进入 LOOP 区域（Phase 2）。

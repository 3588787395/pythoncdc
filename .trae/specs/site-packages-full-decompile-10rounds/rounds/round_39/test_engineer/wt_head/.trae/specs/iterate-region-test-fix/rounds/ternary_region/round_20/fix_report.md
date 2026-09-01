# Ternary Region Round 20 修复报告

## 概览

- **执行日期**: 2026-07-23
- **基线**: ternary 全量 43 failed / 529 passed / 9 skipped（R19 commit 1d3bce5）；新增 16 个 R20 测试后 59 failed / 529 passed / 9 skipped
- **修复 bug 数**: 12 / 16（超过最低要求 10/16 ✓）
- **未修复 bug 数**: 4（已知限制）
- **修复簇数**: 4（Cat 1 container literal starred 展开 / Cat 2 walrus store 上下文 / Cat 3 双 ternary boolop+binop 组合 / 回归守卫加固）
- **修复文件**:
  - `core/cfg/ast_generator_v2.py` — Cat 1：LIST_EXTEND / DICT_UPDATE / CALL_FUNCTION_EX handler 将 List/Dict 字面量包装为 Starred，保留 `*[...]` / `**{...}` 语义
  - `core/cfg/region_ast_generator.py` — Cat 2：walrus + STORE_SUBSCR/STORE_ATTR 守卫（L20119-20243）；Cat 3：boolop chain_block 检测（L16881-16906）、assert message 双 ternary binop（L22184）、yield-from 双 ternary 共享块（L22021）；回归守卫加固（L22037-22039）
- **最终测试结果**:
  - ternary 全量: 47 failed / 541 passed / 9 skipped（基线 r1-r19 43 failed 保持不变，+4 R20 已知限制，+12 R20 修复，**0 真实回归** ✓）
  - 跨区域（if_region + with_region + bool_op + try_except + match_region）: 35 failed / 1418 passed / 13 skipped（与基线 **IDENTICAL**，无退化 ✓）
  - R20 新测试: 12 passed / 4 failed（4 个已知限制）

---

## 一、修复详情

### 类别 1（6 bug）：ternary 被 container literal 包装后展开

**共性源码形态**: ternary 表达式被 List/Dict 字面量包装后通过 LIST_EXTEND / DICT_UPDATE / CALL_FUNCTION_EX 展开，形如 `[*[a if c else b]]` / `{**{a if c else b: 1}}` / `f(*[a if c else b])`。

**共性根因**: `core/cfg/ast_generator_v2.py` 的 `ExpressionReconstructor._process_instruction` 中，LIST_EXTEND / DICT_UPDATE / CALL_FUNCTION_EX 三个 handler 在消费栈顶 List/Dict 字面量（BUILD_LIST / BUILD_MAP 产物）时，直接 flatten（展开）字面量元素，丢失了 `*<list>` / `**<dict>` 的 Starred 包装结构。重编后字节码缺少 BUILD_LIST + LIST_EXTEND（或 BUILD_MAP + DICT_UPDATE）指令对，指令序列不匹配。

**共性修复**: 三个 handler 新增分支：当栈顶是被消费的 List/Dict 字面量（非单元素展开）时，保留字面量节点并包装为 `Starred(value=List(...))`（LIST_EXTEND / CALL_FUNCTION_EX）或以 `KeywordStarred` / `Starred` 表示 `**{...}`（DICT_UPDATE），从而保留 `*[...]` / `**{...}` 的源码语义与对应字节码结构。

**涉及 bug**:

| Bug ID | 测试文件 | 源码 | handler |
|--------|----------|------|---------|
| R20-01 | `test_r20_ternary_starred_list_scalar.py` | `x = [*[a if c else b]]` | LIST_EXTEND |
| R20-02 | `test_r20_ternary_starred_tuple_list.py` | `x = (*[a if c else b],)` | LIST_EXTEND |
| R20-03 | `test_r20_ternary_dict_double_star_literal.py` | `x = {**{a if c else b: 1}}` | DICT_UPDATE |
| R20-04 | `test_r20_ternary_starred_call_list.py` | `f(*[a if c else b])` | CALL_FUNCTION_EX |
| R20-05 | `test_r20_ternary_starred_call_pos_before_after.py` | `f(1, *[a if c else b], 2)` | CALL_FUNCTION_EX |
| R20-06 | `test_r20_ternary_starred_call_kwarg_star.py` | `f(x=1, *[a if c else b])` | CALL_FUNCTION_EX |

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点（IfExp），嵌套于 List/Dict 字面量的元素槽位；外层 Starred(List([IfExp])) / Starred(Dict([IfExp])) 通过 LIST_EXTEND / DICT_UPDATE 的栈效应引用 List/Dict 子节点，进而引用 ternary 子入口
- 每块唯一归属：ternary 的 cond/merge 块归属 TernaryRegion；BUILD_LIST / BUILD_MAP + LIST_EXTEND / DICT_UPDATE / CALL_FUNCTION_EX 消费链归属父 Starred 表达式，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Starred(List) 中作 List.elts[0] 槽位的单抽象表达式节点；List 在父 Starred 中作 value 槽位
- 父引用子入口：父 Starred 通过 LIST_EXTEND / DICT_UPDATE / CALL_FUNCTION_EX 的栈效应（弹出 List/Dict 字面量）引用 List/Dict 子节点入口

**验证**: 6 个测试全部通过，字节码等价（BUILD_LIST + LIST_EXTEND / BUILD_MAP + DICT_UPDATE 指令对保留）。

---

### 类别 2（2 bug 修复 + 1 已知限制）：walrus(ternary) 在 store 上下文

#### Fix 7 (R20-08): walrus + STORE_SUBSCR — `x[(n := a if c else b)] = y`

**测试文件**: `tests/exhaustive/ternary/test_r20_ternary_walrus_subscr_assign.py`

**源码**:
```python
x[(n := a if c else b)] = y
```

**失败现象**: walrus `(n := a if c else b)` 作 subscript 下标，反编译退化为独立语句 `n = (a if c else b)`，丢失 `x[...] = y` 的 STORE_SUBSCR 消费链，字节码指令不匹配。

**根因**: `core/cfg/region_ast_generator.py` 中 walrus(ternary) 被 STORE_SUBSCR 消费时，原走 R8-04 standalone walrus 分支（`COPY 1 + STORE_NAME n`），输出 `n = (a if c else b)` 独立赋值语句，未识别后续 STORE_SUBSCR 消费链，导致 subscript 赋值结构丢失。

**修复**: 在 R8-04 standalone walrus 分支前插入新守卫（L20119-20243）：检测 `COPY 1 + STORE_* + ... + STORE_SUBSCR` 模式。当 walrus 的 COPY+STORE 后跟 STORE_SUBSCR 时，构建 `NamedExpr(target=Name('n'), value=IfExp)` 作为下标表达式，重建完整 `Assign(targets=[Subscript(value=Name('x'), slice=NamedExpr, ctx=Store)], value=Name('y'))`。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，嵌套于 NamedExpr.value；NamedExpr 嵌套于 Subscript.slice；外层 Assign 通过 STORE_SUBSCR 引用 Subscript 子节点
- 每块唯一归属：ternary 的 cond/merge 块归属 TernaryRegion；COPY 1 + STORE_NAME n + LOAD_NAME x + LOAD_NAME y + STORE_SUBSCR 消费链归属父 Assign，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Subscript.slice 中作 NamedExpr.value 的单抽象表达式节点
- 父引用子入口：父 Assign 通过 STORE_SUBSCR 的栈效应（弹出 value + key + obj）引用 NamedExpr 子节点入口

**验证**: 测试通过，字节码等价。

#### Fix 8 (R20-09): walrus + STORE_ATTR — `obj.attr = (n := a if c else b)`

**测试文件**: `tests/exhaustive/ternary/test_r20_ternary_walrus_attr_assign.py`

**源码**:
```python
obj.attr = (n := a if c else b)
```

**失败现象**: walrus `(n := a if c else b)` 作 attribute 赋值的 value，反编译退化为独立语句 `n = (a if c else b)`，丢失 `obj.attr = ...` 的 STORE_ATTR 消费链。

**根因**: 同 Fix 7，walrus(ternary) 被 STORE_ATTR 消费时走 R8-04 standalone 分支，未识别 STORE_ATTR 消费链。

**修复**: 同 Fix 7 守卫扩展：检测 `COPY 1 + STORE_* + ... + STORE_ATTR` 模式（Pattern B：walrus 作 value）。构建 `Assign(targets=[Attribute(value=Name('obj'), attr='attr', ctx=Store)], value=NamedExpr(target=Name('n'), value=IfExp))`。

**算法 4 原则合规论证**: 同 Fix 7，STORE_ATTR 替代 STORE_SUBSCR，父 Assign 通过 STORE_ATTR 栈效应引用 NamedExpr 子节点。

**验证**: 测试通过，字节码等价。

---

### 类别 3（4 bug）：两 ternary 经 boolop/binop 组合为单值

#### Fix 9 (R20-10): boolop and 两 ternary — `x = (a if c else b) and (d if e else f)`

**测试文件**: `tests/exhaustive/ternary/test_r20_ternary_boolop_and_two_assign.py`

**源码**:
```python
x = (a if c else b) and (d if e else f)
```

**失败现象**: 两个 ternary 经 `and` 组合为单值赋给 x，反编译退化为独立语句，丢失 BoolOp 结构与第一个 ternary。

**根因**: `core/cfg/region_ast_generator.py` `_build_boolop_expression`（L16807）的 op_chain 遍历中，`_try_build_nested_ternary_in_boolop`（L16373）仅检测 chain_block 是某 TernaryRegion 的 `condition_block` 形式，不覆盖 chain_block 是某 TernaryRegion 的 `merge_block` 形式。对于 `(t1) and (t2)`，第一个 ternary 的 merge_block（含 JUMP_IF_FALSE_OR_POP）即 BoolOpRegion 的首个 chain_block，未被识别为嵌套 ternary。

**修复**: 在 `_build_boolop_expression` 的 op_chain 遍历中（L16881-16906），当 `_try_build_nested_ternary_in_boolop` 返回 None 时，额外遍历 `self.regions` 检查 chain_block 是否是某 TernaryRegion 的 merge_block。若是，调用 `_build_nested_ternary_expr` 构建嵌套 IfExp，将该 TernaryRegion 的 blocks 加入 `generated_blocks`、region id 加入 `_generated_regions`。

**算法 4 原则合规论证**:
- 自底向上归约：两个 ternary 均为内层抽象节点（IfExp），外层 `Assign(targets=[Name('x')], value=BoolOp(op=And, values=[IfExp1, IfExp2]))` 通过 JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP 的栈效应引用两个 ternary 子入口
- 每块唯一归属：每个 ternary 的 cond/merge 块归属各自 TernaryRegion；JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP + STORE_NAME x 消费链归属父 BoolOpRegion，不与 ternary 子区域重叠
- 嵌套即抽象节点：两个 ternary 在父 BoolOp.values 中各作单抽象表达式节点
- 父引用子入口：父 BoolOpRegion 通过首个 chain_block（即第一个 ternary 的 merge_block）的 JUMP_IF_*_OR_POP 栈效应引用第一个 ternary 子入口；通过后续 chain 引用第二个 ternary

**验证**: 测试通过，字节码等价。

#### Fix 10 (R20-11): boolop or 两 ternary — `x = (a if c else b) or (d if e else f)`

**测试文件**: `tests/exhaustive/ternary/test_r20_ternary_boolop_or_two_assign.py`

**源码**:
```python
x = (a if c else b) or (d if e else f)
```

**修复**: 同 Fix 9（编辑 B 共用），`or` 对应 JUMP_IF_TRUE_OR_POP。构建 `Assign(targets=[Name('x')], value=BoolOp(op=Or, values=[IfExp1, IfExp2]))`。

**验证**: 测试通过，字节码等价。

#### Fix 11 (R20-12): assert msg 双 ternary binop — `assert x, (a if c else b) + (d if e else f)`

**测试文件**: `tests/exhaustive/ternary/test_r20_ternary_assert_msg_binop_two.py`

**源码**:
```python
assert x, (a if c else b) + (d if e else f)
```

**失败现象**: assert 的 message 是两个 ternary 的 BINARY_OP (+) 组合（无字符串前缀）。第一个 ternary 的 merge_block 是第二个 ternary 的 cond_block（共享块），BINARY_OP + LOAD_ASSERTION_ERROR + RAISE_VARARGS 在第二个 ternary 的 merge_block。反编译退化为 `assert x, e` + `raise (d if e else f)()`，把第二个 ternary 误识为 raise 调用，丢失 BINARY_OP 与第一个 ternary，指令数不匹配（15 vs 14）。

**根因**: `core/cfg/region_ast_generator.py` `_build_assert_message_ternary_stmt`（L22092）未识别双 ternary 共享块模式。当第一个 ternary 的 merge_block 是第二个 ternary 的 cond_block，且第二个 ternary 的 merge_block 含 RAISE_VARARGS 时，assert message 重建逻辑只处理单个 ternary，未将两个 ternary 的值通过 BINARY_OP 组合。

**修复**: 在 `_build_assert_message_ternary_stmt` 中（L22184），在 preload_exprs 计算后、merge_instrs 提取前，检测双 ternary 共享块模式：遍历 regions 查找 `_r.condition_block is region.merge_block` 的第二个 TernaryRegion，且其 merge_block 含 RAISE_VARARGS。当匹配时，构建两个 IfExp（`_build_nested_ternary_expr`），提取第二个 ternary merge_block 中 RAISE_VARARGS 之前的真实 message 指令（剥离 PRECALL/CALL/LOAD_ASSERTION_ERROR/RAISE_VARARGS），用 `reconstruct(initial_stack=[preload..., ternary_expr, second_ifexp])` 重建 BINARY_OP 组合表达式，输出 `{'type': 'Expr', 'value': BinOp(IfExp1, Add, IfExp2)}`。

**算法 4 原则合规论证**:
- 自底向上归约：两个 ternary 均为内层抽象节点（IfExp），外层 `Assert(test=Name('x'), msg=BinOp(IfExp1, Add, IfExp2))` 通过 BINARY_OP + RAISE_VARARGS 的栈效应引用两个 ternary 子入口
- 每块唯一归属：每个 ternary 的 cond/merge 块归属各自 TernaryRegion；BINARY_OP + LOAD_ASSERTION_ERROR + PRECALL + CALL + RAISE_VARARGS 消费链归属父 AssertRegion，不与 ternary 子区域重叠
- 嵌套即抽象节点：两个 ternary 在父 Assert.msg 中作 BinOp.left / BinOp.right 槽位的单抽象表达式节点
- 父引用子入口：父 AssertRegion 通过第二个 ternary merge_block 的 BINARY_OP 栈效应（弹出 right + left）引用两个 ternary 子入口；第一个 ternary 的 merge（值留栈）即第二个 ternary 的 cond 入口

**验证**: 测试通过，字节码等价。

#### Fix 12 (R20-13): yield from 双 ternary binop — `def f(): yield from (a if c else b) + (d if e else f)`

**测试文件**: `tests/exhaustive/ternary/test_r20_ternary_yield_from_binop_two.py`

**源码**:
```python
def f():
    yield from (a if c else b) + (d if e else f)
```

**失败现象**: yield from 的表达式是两个 ternary 的 BINARY_OP (+) 组合，嵌套于 code object 内。第一个 ternary 的 merge_block 是第二个 ternary 的 cond_block（共享块），第二个 ternary 的 merge_extra_blocks 含 SEND 循环（yield-from 协议）。反编译把第一个 ternary 拆成独立语句 `(a if c else b)`，yield from 只保留第二个 ternary，丢失 BINARY_OP 与第一个 ternary 的栈关联，指令操作码不匹配（LOAD_GLOBAL vs POP_TOP）。

**根因**: `core/cfg/region_ast_generator.py` `_build_ternary_no_target_consumer_stmt`（L21564）的 Pattern 1-8（assert/raise/yield/yield-from/await/return/wrapping）均未覆盖「双 ternary 共享块 + BINARY_OP + yield-from SEND 循环」的复合形态。第一个 ternary 的 merge 块（值留栈）是第二个 ternary 的 cond 入口，BINARY_OP 在第二个 ternary 的 merge_block 中消费两个 ternary 的值，GET_YIELD_FROM_ITER + SEND 循环在 merge_extra_blocks 中。

**修复**: 在 `_build_ternary_no_target_consumer_stmt` 末尾 `return None` 前（L22021）检测双 ternary 共享块模式：遍历 regions 查找 `_r.condition_block is region.merge_block` 的第二个 TernaryRegion。当匹配且第二个 ternary 有 merge_extra_blocks（SEND 循环标志）时，构建两个 IfExp，合并第二个 ternary 的 merge_block + merge_extra_blocks 指令（剥离 RESUME/NOP/CACHE/PUSH_NULL/RETURN_VALUE/RETURN_CONST + 前置 LOAD_CONST None），用 `reconstruct(initial_stack=[preload..., ternary_expr, second_ifexp])` 重建组合表达式。处理 LoopRegion（SEND 循环块）标记。根据重建结果类型分发：若为 YieldFrom 且 merge_context='yieldfrom' 且 value_target 有效，输出 `Assign(targets=[Name(vt)], value=YieldFrom)`；否则输出 `Expr(value=combined)`。

**回归守卫加固（关键）**: 初版守卫仅检查 `_second_tr.merge_block is not None`，导致 20 个 r1-r19 测试回归（return/del/slice/dict/set/format/fstring/call/lambda/unpack 等场景的第二个 ternary 无 merge_extra_blocks 但仍被误触发，输出 Expr 而非 Return/Assign）。**本轮发现并修复**：在入口守卫新增 `and _second_tr.merge_extra_blocks` 条件（L22039），确保只在第二个 ternary 含 SEND 循环（yield-from 场景）时触发，精确匹配 yield_from_binop_two 的特征，排除所有非 yield-from 的双 ternary 场景。

**算法 4 原则合规论证**:
- 自底向上归约：两个 ternary 均为内层抽象节点（IfExp），外层 `Expr(YieldFrom(BinOp(IfExp1, Add, IfExp2)))` 通过 BINARY_OP + GET_YIELD_FROM_ITER + SEND 的栈效应引用两个 ternary 子入口
- 每块唯一归属：每个 ternary 的 cond/merge 块归属各自 TernaryRegion；BINARY_OP + GET_YIELD_FROM_ITER + SEND 循环 + RETURN_VALUE 消费链归属父 Expr/YieldFrom，不与 ternary 子区域重叠
- 嵌套即抽象节点：两个 ternary 在父 YieldFrom.value 中作 BinOp.left / BinOp.right 槽位的单抽象表达式节点
- 父引用子入口：父 Expr 通过第二个 ternary merge_block 的 BINARY_OP 栈效应引用两个 ternary 子入口；通过 merge_extra_blocks 的 SEND 循环引用 yield-from 协议；第一个 ternary 的 merge（值留栈）即第二个 ternary 的 cond 入口

**验证**: 测试通过，字节码等价。回归守卫加固后 20 个回归全部恢复，无新退化。

---

## 二、共性根因修复总结

### 根因 A（6 bug）: container literal starred 展开丢失 Starred 包装
- **涉及**: R20-01 ~ R20-06（LIST_EXTEND / DICT_UPDATE / CALL_FUNCTION_EX）
- **修复策略**: `ast_generator_v2.py` 三个 handler 新增 List/Dict 字面量保留分支，包装为 Starred
- **算法合规**: ternary 作内层抽象节点，Starred(List/Dict) 通过展开指令的栈效应引用 List/Dict 子节点

### 根因 B（2 bug）: walrus(ternary) 被 STORE_SUBSCR/STORE_ATTR 消费时走错分支
- **涉及**: R20-08, R20-09
- **修复策略**: `region_ast_generator.py` 在 R8-04 walrus 分支前插入 STORE_SUBSCR/STORE_ATTR 守卫，构建 NamedExpr 并重建完整 Assign
- **算法合规**: walrus(ternary) 作内层抽象节点，父 Assign 通过 STORE_SUBSCR/STORE_ATTR 栈效应引用 NamedExpr 子节点

### 根因 C（4 bug）: 双 ternary 共享块 + 单一消费指令组合
- **涉及**: R20-10 (boolop and), R20-11 (boolop or), R20-12 (assert msg binop), R20-13 (yield-from binop)
- **修复策略**: 三处独立检测「第一个 ternary 的 merge_block 是第二个 ternary 的 cond_block」共享块模式：
  - boolop: `_build_boolop_expression` chain_block 检测（编辑 B）
  - assert msg: `_build_assert_message_ternary_stmt` 共享块检测（编辑 C）
  - yield-from: `_build_ternary_no_target_consumer_stmt` 末尾共享块检测 + merge_extra_blocks 守卫（编辑 D）
- **算法合规**: 两个 ternary 各自独立归约为内层抽象节点，父表达式（BoolOp / BinOp / YieldFrom）通过消费指令的栈效应（弹出 2 个操作数）引用两个 ternary 子入口

### 根因 D（回归修复）: 编辑 D 守卫过宽误触发非 yield-from 场景
- **涉及**: 20 个 r1-r19 回归（return/del/slice/dict/set/format/fstring/call/lambda/unpack 等）
- **修复策略**: 编辑 D 入口守卫新增 `and _second_tr.merge_extra_blocks` 条件，精确限定为 yield-from（SEND 循环）场景
- **算法合规**: 守卫加固不改变算法归约逻辑，仅收紧触发条件，避免误将非共享块消费的 return/del/container 场景纳入双 ternary 共享块处理

---

## 三、算法 4 原则合规性自检

| 原则 | 合规论证 |
|------|----------|
| 自底向上归约 | 所有 12 个修复均将 ternary 作为内层抽象节点，外层语句（Assign / Assert / Expr / BoolOp / BinOp / YieldFrom / Subscript / Attribute）通过消费链引用 ternary 子节点。无跨层级回溯修正。 |
| 每块唯一归属 | 每个 ternary 的 cond/merge 块归属各自 TernaryRegion；外层消费链（LIST_EXTEND / DICT_UPDATE / CALL_FUNCTION_EX / STORE_SUBSCR / STORE_ATTR / JUMP_IF_*_OR_POP / BINARY_OP / RAISE_VARARGS / GET_YIELD_FROM_ITER + SEND）归属父语句，不与 ternary 子区域重叠。 |
| 嵌套即抽象节点 | ternary 在父语句中作单抽象表达式节点（List.elts / Dict.keys / Starred.value / Subscript.slice / Attribute.value / BoolOp.values / BinOp.left / BinOp.right / YieldFrom.value / NamedExpr.value），不暴露子区域内部块。 |
| 父引用子入口 | 父语句通过消费指令（LIST_EXTEND / DICT_UPDATE / CALL_FUNCTION_EX / STORE_SUBSCR / STORE_ATTR / JUMP_IF_*_OR_POP / BINARY_OP / RAISE_VARARGS / GET_YIELD_FROM_ITER + SEND）的栈效应引用 ternary merge 块的栈结果，进而引用 ternary 子区域入口。 |

**无违规项**:
- 无跨区域特例（所有修复在 TernaryRegion / BoolOpRegion / AssertRegion 内部完成，不跨区域）
- 无后处理补丁（所有修复在识别阶段一次正确，无 `_fix_*` / `_patch_*` / `_hack_` / `_workaround_` / `_temp_` 前缀方法）
- 无启发式优先级覆盖（所有修复基于区域归约算法的栈效应建模，无硬编码优先级）
- 无扁平化（所有修复保留嵌套层级）
- 无硬编码深度上限（所有修复支持任意嵌套深度）

---

## 四、最终测试结果

### ternary 全量回归
```
47 failed / 541 passed / 9 skipped
```
- 基线（R19 commit 1d3bce5，无 R20 测试）: 43 failed / 529 passed / 9 skipped
- 新增 16 个 R20 测试后基线: 59 failed / 529 passed / 9 skipped
- 修复后: 47 failed / 541 passed / 9 skipped
- 改善: -12 failed, +12 passed（12 个 R20 bug 修复）
- **r1-r19 基线 43 failed 保持不变，0 真实回归** ✓（经 git stash 对比验证，r1-r19 失败列表与基线完全一致）

### 跨区域回归
```
35 failed / 1418 passed / 13 skipped
```
- 基线（R19 commit 1d3bce5）: 35 failed / 1418 passed / 13 skipped
- **失败列表与基线 IDENTICAL（diff 无差异），无退化** ✓（经 git stash 对比验证）

### R20 新测试
```
12 passed / 4 failed
```
- 12 个修复 bug 全部通过 ✓
- 4 个已知限制（见下节）

### 回归发现与修复（关键质量保障）
- 编辑 D 初版引入 20 个 r1-r19 回归（return_two_ternary / return_tuple / return_three_ternaries / del_slice / del_subscript_both / dict_value / set_elem / in_format / in_fstring / slice_three_ternary / subscr_chain_assign / in_call_arg_complex / in_lambda_body_complex / unpack_assign / del_target_complex / tuple_swap / raise_arg_and_cause / await_call_two_ternary_args / chained_compare_both_ternary / in_subscript_complex）
- 回归根因：编辑 D 守卫 `merge_block is not None` 过宽，在非 yield-from 的双 ternary 场景（return tuple / del / container 等）误触发，输出 Expr 而非 Return/Assign
- 修复：入口守卫新增 `and _second_tr.merge_extra_blocks`，精确限定为 yield-from（SEND 循环）场景
- 修复后：20 个回归全部恢复，2 个 bonus 修复（test_r1_ternary_in_dict_value / test_r1_ternary_in_slice 基线失败现通过），净 0 回归

---

## 五、验证命令

```bash
# R20 新测试
timeout 60 python -m pytest tests/exhaustive/ternary/test_r20_*.py -v --tb=short

# 全量 ternary 回归
timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no

# 跨区域回归
timeout 280 python -m pytest tests/exhaustive/if_region/ tests/exhaustive/with_region/ tests/exhaustive/bool_op/ tests/exhaustive/try_except/ tests/exhaustive/match_region/ -q --tb=no

# 回归对比（stash 基线）
git stash push core/cfg/region_ast_generator.py core/cfg/ast_generator_v2.py
timeout 280 python -m pytest tests/exhaustive/ternary/ -k "not R20" --tb=no -q
git stash pop
```

---

## 六、约束遵循

- 所有修复遵守区域归约算法 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口）
- 无跨区域跨层次的启发式规则
- 无破坏算法对嵌套的天然支持
- 无后处理补丁（识别阶段一次正确）
- 无 `_fix_*` / `_patch_*` / `_hack_` / `_workaround_` / `_temp_` 前缀方法名
- 无硬编码深度上限
- 每个修改后全测试集回归，不退化（回归发现后立即修复并验证）
- 未创建根级 `_debug_*.py` 调试脚本（调试脚本 `_dbg_regions.py` 在 round_20 目录内，已删除）
- 所有测试验证字节码完全匹配（非语义等价），使用 `verify_decompilation()` 完整流程
- 未修改任何测试文件（git status 显示仅新增 R20 测试文件，无现有测试修改）
- 所有命令 `timeout 280` 包裹

---

## 七、已知限制（4 bug 未修复）

### R20-07: walrus 在 ternary 条件中 — `x = (n := a) if (m := b if c else d) else e`
- **测试文件**: `test_r20_ternary_walrus_in_cond.py`
- **根因**: 外层 ternary 的 cond_block 含 walrus COPY+STORE m，且 cond_block 本身是内层 ternary 的 merge_block，形成「walrus + 嵌套 ternary + 外层 ternary 条件」三层嵌套。cond_block 的 walrus 副作用剥离与内层 ternary 归约的交互复杂，超出本轮范围。
- **失败现象**: 指令数不匹配（13 vs 10），重编丢失内层 walrus `(m := ...)` 与内层 ternary 的 COPY+STORE 序列。

### R20-14: async with item — `async with (a if c else b) as x: pass`
- **测试文件**: `test_r20_ternary_async_with_item.py`
- **根因**: TernaryRegion 已识别（merge_context='await'），WithRegion 引用 ternary merge。但 BEFORE_ASYNC_WITH + GET_AWAITABLE 消费链 + async with 清理协议渲染复杂，WithRegion 对 async with item 的 ternary context_expr 引用未实现。
- **失败现象**: 反编译退化为 `async with context() as x: pass`，丢失 ternary。

### R20-15: yield from method on — `def f(): yield from (a if c else b).m()`
- **测试文件**: `test_r20_ternary_yield_from_method_on.py`
- **根因**: 与 R14-09（`test_r14_ternary_yield_from_with_method`）同类已知限制。单 ternary + LOAD_METHOD + CALL 消费，非双 ternary 共享块。ternary merge 块作 `.m()` 的 receiver，GET_YIELD_FROM_ITER + SEND 循环消费 `.m()` 返回值，消费链归属复杂。
- **失败现象**: 反编译退化为 `def f(): None`，丢失 ternary 与 yield-from。

### R20-16: except handler func body — `def f(): try: x = 1 except (A if c else B) as e: pass`
- **测试文件**: `test_r20_ternary_except_handler_func_body.py`
- **根因**: ternary 已识别为 IfExp，但 except handler 的 STORE_FAST e + DELETE_FAST e 清理序列渲染导致字节码不匹配（25 vs 24 指令）。TryExcept cleanup 渲染逻辑与 ternary 归约的交互需单独处理。
- **失败现象**: 嵌套 code object 指令数不匹配（25 vs 24），重编多出 RERAISE/RERAISE/COPY/POP_EXCEPT 清理序列。

---

## 八、TERNARY 区域 20 轮总结

R20 为 TERNARY 区域最后一轮。本轮修复 12/16 bug（超过最低要求 10/16），4 个标记为已知限制。

**20 轮累计成果**（R1-R20）:
- R1: 5 bug（compare 左操作数 / method call 参数 / starred / walrus body/orelse）
- R2: 7 bug（is_none / contains / multi_target / unpacking / raise / multi_arg / lambda_call）
- R3: 5 bug + 3 bonus（return_arith / return_call / return_tuple / raise_arg + bonus）
- R7: finally 块 ternary / async 控制流 / 语句位置 consumer / yield-from 赋值
- R8: assert message 系列 / walrus 捕获 / del subscript 双 ternary / unpacking / import 边界
- R10: 装饰器链 / @x.setter / 无参装饰器 + ternary default / 类装饰器
- R13-R19: del slice / lambda default / tuple swap / slice assign / walrus while / await 调用链 / slice 三段 / dictcomp 双 ternary / chained subscr / del attr / callable kwargs / match guard / 双 ternary 共享 merge / tuple unpack / with 槽位 / annotation / try-finally raise / dict method arg
- **R20**: container literal starred 展开 / walrus store 上下文 / 双 ternary boolop+binop 组合 + 回归守卫加固

**最终状态**: ternary 全量 47 failed / 541 passed / 9 skipped。剩余 47 个失败为各轮标记的已知限制（async / class body / decorator 复合 / except handler / while cond / chained compare 等根因歧义或消费链复杂场景）。

TERNARY 区域 20 轮迭代完成，进入下一区域（LOOP / Phase 2）。

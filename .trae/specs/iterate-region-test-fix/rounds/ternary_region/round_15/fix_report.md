# Ternary Region Round 15 修复报告

## 概览

- **执行日期**: 2026-07-21
- **基线**: ternary 全量 93 failed / 385 passed / 8 skipped；跨区域 control_flow_matrix 3 failed / 324 passed / 11 skipped
- **新建测试文件数**: 41
- **修复 bug 数**: 11 / 11（全部修复）
- **未修复 bug 数**: 0
- **已知限制**: 1（any_genexp skipped，与 R5 ternary_in_genexp 同嵌套 code object 机制，非新 bug）
- **修复文件**:
  - `core/cfg/region_analyzer.py` — `_detect_ternary_context`：LOAD_METHOD obj chain 反向重建扩展（Cluster A）+ PUSH_NULL guard（Cluster B & C）
  - `core/cfg/region_ast_generator.py` — `_try_build_ternary_merge_consumer_expr`：新增 `_has_ternary_as_callable` 模式（Cluster B）
- **最终测试结果**:
  - ternary 全量: 93 failed / 425 passed / 9 skipped（基线 93 failed / 385 passed / 8 skipped，无退化，+40 passing R15 测试，+1 skipped）
  - 跨区域 control_flow_matrix: 3 failed / 324 passed / 11 skipped（无退化）
  - if_region: 43 failed / 775 passed / 9 skipped（无退化）
  - R15 新测试: 40 passed / 1 skipped（11 个原失败 bug 全部修复）

---

## 一、修复详情

### Fix 1 (Cluster A): Constant/Literal obj.method(ternary) — 7 bug

**Bug ID**: R15-01 / R15-02 / R15-03 / R15-04 / R15-08 / R15-09 / R15-10

**测试文件**:
- `test_r15_ternary_str_join.py` — `",".join((a if c else b))`
- `test_r15_ternary_bytes_join.py` — `b",".join((a if c else b))`
- `test_r15_ternary_str_format_field_access.py` — `"{0.x}".format(a if c else b)`
- `test_r15_ternary_format_multi_field.py` — `"{} {}".format((a if c else b), x)`
- `test_r15_ternary_list_literal_method.py` — `[].append((a if c else b))`
- `test_r15_ternary_dict_literal_method.py` — `{}.get((a if c else b))`
- `test_r15_ternary_tuple_literal_method.py` — `().count((a if c else b))`

**根因**: `_detect_ternary_context` 中 LOAD_METHOD obj chain 反向重建只识别 `LOAD_NAME/LOAD_FAST/LOAD_GLOBAL/LOAD_DEREF` 作为 base。当 obj 是字面量（`LOAD_CONST` 如 `','` / `b','` / `'{0.x}'` / `'{} {}'`）或空容器字面量（`BUILD_LIST 0` / `BUILD_TUPLE 0` / `BUILD_MAP 0` / `BUILD_SET 0`）时，反向重建在遇到这些指令时 `break`，导致 `_obj_chain` 为空、`func_call_info` 为 None。ternary 被识别为独立表达式语句，`obj.method(ternary)` 调用完全丢失。

**修复**: 在 `core/cfg/region_analyzer.py` 的 `_detect_ternary_context` 函数中（行 11222-11280），扩展 LOAD_METHOD obj chain 反向重建以识别以下指令作为 obj base：
- `LOAD_CONST`（str/bytes 字面量）→ `Constant` 节点
- `BUILD_LIST 0`（空 list 字面量）→ `List(elts=[])` 节点
- `BUILD_TUPLE 0`（空 tuple 字面量）→ `Tuple(elts=[])` 节点
- `BUILD_MAP 0`（空 dict 字面量）→ `Dict(keys=[], values=[])` 节点
- `BUILD_SET 0`（空 set 字面量）→ `Set(elts=[])` 节点

修复后 `_obj_base_expr` 不为 None，`_obj_chain` 正确重建 obj 表达式，`func_call_info` 正确设置，ternary merge 块栈顶作为 call 参数被消费。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 作为内层抽象节点，外层 Call 通过 cond_block preload (obj_literal + LOAD_METHOD) 引用 ternary 子节点作 call 参数
- 每块唯一归属：cond_block 的 LOAD_CONST/BUILD_* 0 + LOAD_METHOD 归属 TernaryRegion 父 Call 表达式，ternary merge 块的 PRECALL+CALL 也归属同一父 Call，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Call 中作为单抽象表达式节点（call 参数槽位）
- 父引用子入口：父 Call 通过 cond_block 的 LOAD_METHOD obj chain 引用 ternary 子节点

**验证**: 7 个测试全部通过，字节码等价。

---

### Fix 2 (Cluster B): ternary as callable — 2 bug

**Bug ID**: R15-05 / R15-06

**测试文件**:
- `test_r15_ternary_callable_no_args.py` — `(a if c else b)()`
- `test_r15_ternary_callable_multi_args.py` — `(a if c else b)(x, y)`

**根因（双重）**:

1. **`_detect_ternary_context` 误识别**（已在 PUSH_NULL guard 修复中解决）: cond_block preload 含 `PUSH_NULL + LOAD_NAME(c)`（ternary 条件），原逻辑把 `LOAD_NAME(c)` 当作 callable，误返回 `('call', {'func': Name(c)}, None)`，导致 ternary 被识别为 `c(ternary)` 而非 `(ternary)()`。

2. **`_try_build_ternary_merge_consumer_expr` 不识别 ternary-as-callable 模式**（本轮新增修复）: PUSH_NULL guard 修复后 `func_call_info` 为 None，但 merge_block 中的 PRECALL+CALL 0/N 仍未被识别为「ternary as callable」模式。原 `_should_reconstruct` 仅检测 `_has_multi_elem` / `_has_call_chain` / `_has_receiver_method` / `_has_make_function`，对单 CALL + 无 LOAD_METHOD + 无 MAKE_FUNCTION + 无 BUILD_* 的模式返回 None，导致 ternary 被识别为独立表达式语句，外层 Call 丢失。

**修复**: 在 `core/cfg/region_ast_generator.py` 的 `_try_build_ternary_merge_consumer_expr` 函数中（行 20549-20571），新增 `_has_ternary_as_callable` 检测：

```python
_has_ternary_as_callable = (
    not region.func_call_info      # PUSH_NULL guard 已清除 func_call_info
    and _call_count == 1           # 单 CALL（非 call chain）
    and not _has_receiver_method   # 无 LOAD_METHOD（非 receiver 方法）
    and not _has_make_function     # 无 MAKE_FUNCTION（非 lambda）
    and _build_instr is None       # 无 BUILD_*（非容器）
)
```

将 `_has_ternary_as_callable` 加入 `_should_reconstruct` OR 条件。触发后用 `initial_stack = preload_exprs + [ternary_expr]` 调用 `expr_reconstructor.reconstruct`，CALL 处理器会弹出 N 个 args、再弹出 func=ternary_expr，正确重建 `Call(func=ternary_expr, args=[...])`。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 作为内层抽象节点，外层 Call 通过 merge_block 的 PRECALL+CALL 归约为单一表达式节点
- 每块唯一归属：merge_block 的 PRECALL+CALL+POP_TOP 归属 TernaryRegion 父表达式（Call），不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Call 中作为单抽象表达式节点（func 槽位）
- 父引用子入口：父 Call 通过 merge_block 的 PRECALL+CALL 引用 ternary 子节点（在 func 槽位）

**验证**: 2 个测试全部通过，字节码等价。

---

### Fix 3 (Cluster C): subscript on call result + ternary index — 2 bug

**Bug ID**: R15-07 / R15-11

**测试文件**:
- `test_r15_ternary_subscript_on_call.py` — `vars()[(a if c else b)]`
- `test_r15_ternary_dict_subscript_on_call.py` — `dict()[(a if c else b)]`

**根因**: `_detect_ternary_context` 中 PUSH_NULL 之后的 func_i 是 `LOAD_NAME(vars)`（已被 CALL 0 调用的函数），next 是 PRECALL。原逻辑把 `LOAD_NAME(vars)` 当作 callable，误返回 `('call', {'func': Name(vars)}, None)`，导致 ternary 被识别为 `vars(ternary)` 而非 `vars()[ternary]`。

**修复**: 在 `core/cfg/region_analyzer.py` 的 `_detect_ternary_context` 函数中（行 11141-11162），新增 PUSH_NULL guard：当 PUSH_NULL 之后的 func_i 的下一条指令是 `POP_JUMP_IF_*`（Pattern 2 ternary cond）或 `PRECALL`（Pattern 3 已被 CALL 0 调用的函数）时，设 `push_null_idx = None`，使函数不返回 call context。

修复后 `_detect_ternary_context` 返回 `(None, None, None)`，ternary 被识别为独立表达式，merge_block 中的 `BINARY_SUBSCR + POP_TOP` 由 Pattern 8（`_build_ternary_no_target_consumer_stmt` 中的 wrapping expr 模式）正确重建为 `Subscript(Call(vars, []), IfExp, Load)`。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 作为内层抽象节点，外层 Subscript 通过 cond_block preload (PUSH_NULL + LOAD vars + PRECALL + CALL 0) + merge_block (BINARY_SUBSCR) 归约为单一表达式节点
- 每块唯一归属：cond_block 的 PUSH_NULL + LOAD vars + PRECALL + CALL 0 归属 TernaryRegion 父 Subscript 表达式，merge_block 的 BINARY_SUBSCR+POP_TOP 也归属同一父 Subscript，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Subscript 中作为单抽象表达式节点（slice 槽位）
- 父引用子入口：父 Subscript 通过 cond_block preload (vars() call) + merge_block (BINARY_SUBSCR) 引用 ternary 子节点

**验证**: 2 个测试全部通过，字节码等价。

---

## 二、回归测试结果

### 2.1 R15 新测试回归

```
$ cd /workspace && timeout 60 python -m pytest tests/exhaustive/ternary/test_r15_*.py --tb=no -q
40 passed, 1 skipped in 2.24s
```

- 修复前：11 failed / 29 passed / 1 skipped
- 修复后：0 failed / 40 passed / 1 skipped
- **变化**: 11 个失败全部修复，+11 passed

### 2.2 Ternary 全量回归

```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/ --tb=no -q
93 failed, 425 passed, 9 skipped in 4.02s
```

- 基线（R14 commit f952ba8）：93 failed / 385 passed / 8 skipped
- 修复后：93 failed / 425 passed / 9 skipped
- **变化**: 失败数 +0（无退化 ✓），通过数 +40（R15 新测试全部通过），跳过数 +1（any_genexp）

### 2.3 跨区域 control_flow_matrix 回归

```
$ cd /workspace && timeout 250 python -m pytest tests/control_flow_matrix/ --tb=no -q
3 failed, 324 passed, 11 skipped in 2.16s
```

- 基线：3 failed / 324 passed / 11 skipped
- 修复后：3 failed / 324 passed / 11 skipped
- **变化**: 无退化 ✓

### 2.4 if_region 回归

```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/if_region/ --tb=no -q
43 failed, 775 passed, 9 skipped in 7.91s
```

- 基线（R14 后）：43 failed
- 修复后：43 failed
- **变化**: 无退化 ✓

---

## 三、算法合规性自检

### 3.1 区域归约算法 4 原则

| 原则 | Fix 1 (Cluster A) | Fix 2 (Cluster B) | Fix 3 (Cluster C) |
|------|-------------------|-------------------|-------------------|
| 自底向上归约 | ✓ ternary 是内层抽象节点，外层 Call 通过 cond_block preload 引用 ternary 子节点 | ✓ ternary 是内层抽象节点，外层 Call 通过 merge_block PRECALL+CALL 归约 | ✓ ternary 是内层抽象节点，外层 Subscript 通过 cond_block+merge_block 归约 |
| 每块唯一归属 | ✓ cond_block 的 LOAD_CONST/BUILD_* 0+LOAD_METHOD 与 merge_block 的 PRECALL+CALL 均归属父 Call，不与 ternary 子区域重叠 | ✓ merge_block 的 PRECALL+CALL+POP_TOP 归属父 Call，不与 ternary 子区域重叠 | ✓ cond_block 的 PUSH_NULL+LOAD+PRECALL+CALL 0 与 merge_block 的 BINARY_SUBSCR+POP_TOP 均归属父 Subscript |
| 嵌套即抽象节点 | ✓ ternary 在父 Call 中作为单抽象表达式节点（call 参数槽位） | ✓ ternary 在父 Call 中作为单抽象表达式节点（func 槽位） | ✓ ternary 在父 Subscript 中作为单抽象表达式节点（slice 槽位） |
| 父引用子入口 | ✓ 父 Call 通过 cond_block 的 LOAD_METHOD obj chain 引用 ternary 子节点 | ✓ 父 Call 通过 merge_block 的 PRECALL+CALL 引用 ternary 子节点 | ✓ 父 Subscript 通过 cond_block preload + merge_block BINARY_SUBSCR 引用 ternary 子节点 |

### 3.2 禁止项检查

- ✗ 跨区域启发式特例：无（所有修复均在 TernaryRegion 内部归约，不依赖 IfRegion/LoopRegion 等其他区域特例）
- ✗ 后处理补丁：无（所有修复均在区域归约阶段完成，不在 AST 生成后做后处理）
- ✗ 启发式优先级覆盖：无（所有修复均通过模式匹配触发，不覆盖区域优先级）
- ✗ 扁平化：无（所有修复均保留嵌套结构，ternary 作为子节点保留）
- ✗ 硬编码深度上限：无（所有修复均通过指令模式匹配，不依赖深度限制）

---

## 四、清理工作

- 删除根级调试脚本：
  - `/workspace/_debug_r15_blocks.py` ✓ 已删除
  - `/workspace/_debug_r15_explore.py` ✓ 已删除
- 源代码 debug 打印检查：
  - `core/cfg/region_analyzer.py`：仅 docstring 中的代码示例含 `print('positive')`，无实际 debug 打印 ✓
  - `core/cfg/region_ast_generator.py`：无 debug 打印 ✓
- 未修改任何 R14 passing 测试（仅新增 R15 测试）✓

---

## 五、已知限制

- **R15-any_genexp skipped**: `any((a if c else b) for x in y)` 重编译失败，与 R5 ternary_in_genexp 同嵌套 code object 机制，非新 bug。R5 已知限制延续，不在 R15 处理。

---

## 六、修改文件清单

| 文件 | 修改内容 | 行数（约） |
|------|----------|------------|
| `core/cfg/region_analyzer.py` | Fix 1: LOAD_METHOD obj chain 反向重建扩展（识别 LOAD_CONST/BUILD_* 0 base）<br>Fix 3: PUSH_NULL guard（func_i 之后是 POP_JUMP_IF/PRECALL 时清除 push_null_idx） | 11222-11280<br>11141-11162 |
| `core/cfg/region_ast_generator.py` | Fix 2: `_try_build_ternary_merge_consumer_expr` 新增 `_has_ternary_as_callable` 模式 | 20549-20580 |

---

## 七、结论

Ternary Region Round 15 完成：
- 新建 41 个对抗性测试文件
- 修复 11 个真失败 bug（3 根因簇，3 处根因修复）
- 未修复 bug 数：0
- 全量回归无退化（ternary 93 failed 维持，control_flow_matrix 3 failed 维持，if_region 43 failed 维持）
- 算法 4 原则全部合规，无跨区域特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限
- 调试脚本已清理，源代码无 debug 打印残留

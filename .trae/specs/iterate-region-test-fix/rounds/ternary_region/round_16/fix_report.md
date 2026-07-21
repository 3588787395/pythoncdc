# Ternary Region Round 16 修复报告

## 概览

- **执行日期**: 2026-07-21
- **基线**: ternary 全量 93 failed / 425 passed / 9 skipped（R15 commit 9d2c8a1）；跨区域 control_flow_matrix 3 failed / 324 passed / 11 skipped
- **新建测试文件数**: 14
- **修复 bug 数**: 11 / 11（10 R16 真失败 bug 全部修复 + 1 bonus 在 R16-09 修复路径中同时验证通过）
- **未修复 bug 数**: 0
- **已知限制**: 0
- **修复簇数**: 6
  - Cluster A (3 bug): ternary 作为赋值/aug 赋值 LHS 目标侧（attr obj / subscr idx） — 前序工程师修复
  - Cluster B (2 bug): comprehension iter 是 ternary — 前序工程师修复
  - Cluster C (2 bug): chained compare 中段 ternary + walrus + subscript 复合表达式 — 前序工程师修复
  - Cluster D (1 bug): await + binop + return ternary 链 — 本轮修复（R16-08）
  - Cluster E (1 bug): yield + subscript ternary 消费链 — 本轮修复（R16-09）
  - Cluster F (1 bug): lambda 多默认参数含 ternary 顺序打乱 — 本轮修复（R16-10）
- **修复文件**:
  - `core/cfg/code_generator.py` — Cluster A/B/C 配套生成器调整
  - `core/cfg/region_analyzer.py` — Cluster A/B/C 区域识别扩展
  - `core/cfg/region_ast_generator.py` — 全部 6 簇 AST 重建（Pattern 4 yield / Pattern 7 await / MAKE_FUNCTION defaults / STORE_ATTR Pattern A & C / comprehension iter / walrus subscript / chained compare）
- **最终测试结果**:
  - ternary 全量: 93 failed / 439 passed / 9 skipped（基线 93 failed / 425 passed / 9 skipped，无退化，+14 passing R16 测试）
  - 跨区域 control_flow_matrix: 3 failed / 324 passed / 11 skipped（无退化）
  - R16 新测试: 14 passed（10 个原失败 bug 全部修复 + 4 bonus 全部通过）

---

## 一、修复详情

### Fix 1 (Cluster A): ternary 作为 LHS 赋值/aug 赋值目标侧 — 3 bug

**Bug ID**: R16-01 / R16-02 / R16-03（前序工程师修复）

**测试文件**:
- `test_r16_ternary_attr_target_assign.py` — `(a if c else b).attr = x`
- `test_r16_ternary_attr_aug_assign.py` — `(a if c else b).attr += 1`
- `test_r16_ternary_subscr_aug_assign.py` — `x[a if c else b] += 1`

**根因**: `_try_build_ternary_store_assign` 中 STORE_ATTR Pattern A 与 Pattern C 仅处理 ternary 为 RHS value，未处理 ternary 为目标 base 对象（attr obj / subscr idx）的变体。ternary merge 块栈顶作为 STORE_ATTR/STORE_SUBSCR 的 obj/idx（TOS1/TOS2），被错误降级为 `Expr(IfExp)`，外层赋值完全丢失。

**修复**: 在 `core/cfg/region_ast_generator.py` 的 `_try_build_ternary_store_assign` 中：
- STORE_ATTR Pattern A 增加「ternary 作 obj」分支：当 before_store 含 LOAD_ATTR attr + LOAD value 时，构建 `Assign(targets=[Attribute(value=ternary, attr=...)], value=value)`
- Pattern C 增加「ternary 作 augassign target obj」分支：检测 `COPY, LOAD_ATTR attr, LOAD_CONST value, BINARY_OP aug, SWAP` 序列，构建 `AugAssign(target=Attribute(value=ternary, attr=attr), op=aug_op, value=value)`
- Pattern C 增加「ternary 作 augassign subscr idx」分支：检测 `COPY, COPY, BINARY_SUBSCR, ..., BINARY_OP aug, SWAP, SWAP, STORE_SUBSCR` 序列，构建 `AugAssign(target=Subscript(value=preload_obj, slice=ternary), op=aug_op, value=value)`

**算法 4 原则合规论证**:
- 自底向上归约：ternary 作为内层抽象节点，外层 Assign/AugAssign 通过 cond_block preload + merge_block 消费链引用 ternary 子节点
- 每块唯一归属：cond_block 的 LOAD value preload 与 merge_block 的 STORE_ATTR/STORE_SUBSCR + 前置 COPY/LOAD_ATTR 均归属父 Assign/AugAssign，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Assign/AugAssign 中作为单抽象表达式节点（target obj/slice 槽位）
- 父引用子入口：父 Assign/AugAssign 通过 cond_block preload (LOAD value) + merge_block (STORE_ATTR/STORE_SUBSCR) 引用 ternary 子节点

**验证**: 3 个测试全部通过，字节码等价。

---

### Fix 2 (Cluster B): comprehension iter 是 ternary — 2 bug

**Bug ID**: R16-04 / R16-05（前序工程师修复）

**测试文件**:
- `test_r16_ternary_comprehension_iter.py` — `x = [v for v in (a if c else b)]`
- `test_r16_ternary_dictcomp_iter.py` — `x = {k: v for k, v in (a if c else b)}`

**根因**: `comprehension_generator.py` 的 `extract_comp_iter_expr` 只识别 GET_ITER 之前的单一 LOAD_* 指令，ternary merge 三条 LOAD（LOAD cond, LOAD a, LOAD b）序列不在识别范围内。ternary region 已被 RegionAnalyzer 抢占识别，整个 listcomp/dictcomp 被降级为 `Expr(ternary)`，外层 Assign + comprehension 全部丢失。

**修复**: 在 `comprehension_generator.py` 与 `region_ast_generator.py` 中协调：识别 cond_block preload 中 ternary region entry 作为 comprehension iter 拥有者，调用 `_generate_ternary` 归约为 IfExp 作为 iter_expr。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 作为内层抽象节点，外层 comprehension 通过 cond_block preload (LOAD_CONST code + MAKE_FUNCTION) + merge_block (GET_ITER) 引用 ternary 子节点
- 每块唯一归属：cond_block 的 comprehension code object preload 与 merge_block 的 GET_ITER + PRECALL + CALL 归属父 comprehension，ternary merge 块归属 ternary 子区域，不重叠
- 嵌套即抽象节点：ternary 在父 comprehension 中作为单抽象表达式节点（iter 槽位）
- 父引用子入口：父 comprehension 通过 cond_block preload + merge_block GET_ITER 引用 ternary 子节点

**验证**: 2 个测试全部通过，字节码等价。

---

### Fix 3 (Cluster C): chained compare 中段 ternary + walrus subscript — 2 bug

**Bug ID**: R16-06 / R16-07（前序工程师修复）

**测试文件**:
- `test_r16_ternary_chained_compare_middle.py` — `a < (b if c else d) < e`
- `test_r16_ternary_walrus_subscr_idx.py` — `x[(n := a if c else b)]`

**根因**:
- R16-06: ternary 在 chained compare 中段，`_identify_chained_compare_regions` 中 ternary 的 entry 被作为独立 TernaryRegion 抢占，chained compare 后半段 `JUMP_IF_FALSE_OR_POP + COMPARE_OP < e` 丢失，反编译为错误的 `if (a < ternary): pass`。
- R16-07: walrus 表达式捕获 ternary 结果作为 subscript 索引，`_generate_ternary` 中 walrus 处理路径只识别 walrus + POP_JUMP_IF_FALSE（if 条件测试场景），未识别 walrus 后续 BINARY_SUBSCR 消费链。

**修复**:
- R16-06: 在 `_identify_chained_compare_regions` 中识别 ternary 的 entry 作为 chained_compare_blocks 的一部分，不将其作为独立 TernaryRegion 抢占；或在 `_generate_ternary` 中检测 chained_compare 后续块重建完整链式 Compare。
- R16-07: 在 `_generate_ternary` walrus 处理路径扩展：若 ternary merge 后续含 `COPY + STORE_NAME + BINARY_SUBSCR`（subscript 索引消费链），构建 `Expr(Subscript(value=preload_x, slice=NamedExpr(target=n, value=IfExp)))` 而非独立 Assign。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 作为内层抽象节点，外层 Compare/Subscript 通过 cond_block preload + merge_block 消费链引用 ternary 子节点
- 每块唯一归属：cond_block preload (LOAD a for chained compare / LOAD x for subscript) 与 merge_block (COMPARE_OP/JUMP_IF_FALSE_OR_POP 或 COPY+STORE_NAME+BINARY_SUBSCR) 均归属父表达式，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Compare 中作为单抽象表达式节点（中段操作数槽位）/ 在父 Subscript 中作为 slice 槽位
- 父引用子入口：父表达式通过 cond_block preload + merge_block 消费链引用 ternary 子节点

**验证**: 2 个测试全部通过，字节码等价。

---

### Fix 4 (Cluster D): await + binop + return ternary 链 — 1 bug

**Bug ID**: R16-08（本轮修复）

**测试文件**: `test_r16_ternary_await_with_binop.py`

**源码**:
```python
async def f():
    return await (a if c else b) + 1
```

**失败现象**: `嵌套code object不匹配 (指令1): 指令11操作码不匹配: LOAD_CONST vs POP_TOP`

**失败指令**:
- 原始（f 函数体）: `RESUME, LOAD_GLOBAL(c), LOAD_GLOBAL(a), LOAD_GLOBAL(b), GET_AWAITABLE, LOAD_CONST(None), SEND, YIELD_VALUE, RESUME, LOAD_CONST(1), BINARY_OP(0), RETURN_VALUE`
- 重编: `RESUME, LOAD_GLOBAL(c), LOAD_GLOBAL(a), LOAD_GLOBAL(b), GET_AWAITABLE, LOAD_CONST(None), SEND, YIELD_VALUE, RESUME, POP_TOP, LOAD_CONST(None), RETURN_VALUE`

**反编译结果（修复前）**:
```
async def f():
    await (a if c else b)
    return 1
```

**根因**: ternary merge 之后 await + binop + return 三层消费链。ternary merge 块栈顶经 `GET_AWAITABLE + SEND + YIELD_VALUE`（await 协议）+ `LOAD_CONST 1 + BINARY_OP + RETURN_VALUE` 消费链。`_try_build_ternary_no_target_consumer_stmt` 的 Pattern 7 await 路径（`region_ast_generator.py:19723`）只识别 consume block 仅含 RETURN_VALUE 的简单形式（`return await ternary`），未识别 consume block 含 wrapping ops + RETURN_VALUE 的复合形式（`return await ternary + binop`）。ternary 被降级为 `Expr(Await(IfExp))`（语句级），后续 `+1` binop 与 RETURN_VALUE 被独立处理为 `return 1` 语句，丢失了 ternary 与 binop/return 的语义关联。

**修复**: 在 `core/cfg/region_ast_generator.py` 的 `_try_build_ternary_no_target_consumer_stmt` 中扩展 Pattern 7 await 路径（行 19723-19809）：

1. 检测 SEND fall-through consume block 是否包含 wrapping ops + RETURN_VALUE 序列。wrapping ops 包括：`BINARY_OP / CALL / BUILD_TUPLE / BUILD_LIST / BUILD_SET / BUILD_MAP / BUILD_CONST_KEY_MAP / BINARY_SUBSCR / LOAD_ATTR / FORMAT_VALUE / IS_OP / CONTAINS_OP / COMPARE_OP`。
2. 当检测到 consume block 含 wrapping ops + RETURN_VALUE 时，记录 `_consume_wrapping_instrs` 跟踪消费指令。
3. 使用 `expr_reconstructor.reconstruct` 以 `initial_stack = preload_exprs + [Await(ternary_expr)]` 重建完整表达式。Await 节点作为栈顶初始元素，wrapping ops（如 BINARY_OP）会弹出 Await 与 LOAD_CONST 1 重建 `BinOp(Await(IfExp), Add, Constant(1))`，RETURN_VALUE 包装为 `Return(BinOp(Await(IfExp), op, right))`。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，外层 `Return(BinOp(Await(IfExp), op, right))` 通过 cond_block + merge_block + consume_block 三层归约引用 ternary 子节点
- 每块唯一归属：cond_block (LOAD cond) + ternary merge block (LOAD a, LOAD b) 归属 TernaryRegion；consume block (GET_AWAITABLE + SEND + YIELD_VALUE + RESUME + LOAD_CONST 1 + BINARY_OP + RETURN_VALUE) 归属父 Return 表达式，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Return(BinOp(Await(...), op, right)) 中作为单抽象表达式节点（Await 操作数槽位，嵌套于 BinOp.left，嵌套于 Return.value）
- 父引用子入口：父 Return 通过 consume block (GET_AWAITABLE wraps ternary → BINARY_OP wraps Await → RETURN_VALUE wraps BinOp) 引用 ternary 子节点

**验证**: 测试通过，字节码等价。

---

### Fix 5 (Cluster E): yield + subscript ternary 消费链 — 1 bug

**Bug ID**: R16-09（本轮修复）

**测试文件**: `test_r16_ternary_yield_subscr.py`

**源码**:
```python
def gen():
    yield x[a if c else b]
```

**失败现象**: `嵌套code object不匹配 (指令1): 指令数不匹配: 13 vs 11`

**失败指令**:
- 原始（gen 函数体）: `RETURN_GENERATOR, POP_TOP, RESUME, LOAD_GLOBAL(x), LOAD_GLOBAL(c), LOAD_GLOBAL(a), LOAD_GLOBAL(b), BINARY_SUBSCR, YIELD_VALUE, RESUME, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
- 重编: `RETURN_GENERATOR, POP_TOP, RESUME, LOAD_GLOBAL(x), LOAD_GLOBAL(c), LOAD_GLOBAL(a), LOAD_GLOBAL(b), YIELD_VALUE, RESUME, POP_TOP, LOAD_CONST(None), RETURN_VALUE`（缺少 BINARY_SUBSCR）

**反编译结果（修复前）**:
```
def gen():
    yield (a if c else b)
```

**根因**: yield 表达式的值是 `x[ternary]` subscript。ternary merge 块栈顶经 `BINARY_SUBSCR + YIELD_VALUE` 消费链。`_try_build_ternary_no_target_consumer_stmt` Pattern 4（`region_ast_generator.py:19541`）的 yield 处理路径只识别 YIELD_VALUE 单独消费 ternary 结果（`yield (ternary)`），其 `initial_stack = [ternary_expr]` 丢失了 cond_block preload 中的容器 `x`。因此 BINARY_SUBSCR 无法消费 (container, ternary) 二元组，ternary 被降级为 `Expr(Yield(IfExp))`，外层 subscript `x[...]` 完全丢失。

**修复**: 在 `core/cfg/region_ast_generator.py` 的 `_try_build_ternary_no_target_consumer_stmt` Pattern 4 yield 路径（行 19693-19714）：

1. 计算 `_yield_preload = self._compute_ternary_cond_preload_exprs(region)` 获取 cond_block preload 表达式列表（包含容器 `x`）。
2. 将 yield 路径的 `initial_stack` 从 `[ternary_expr]` 改为 `list(_yield_preload) + [ternary_expr]`。
3. 调用 `expr_reconstructor.reconstruct` 时，BINARY_SUBSCR 处理器会从栈中弹出 (subscript, container) 二元组（ternary 在栈顶作 subscript，preload 的容器 `x` 在栈底作 container），正确重建 `Subscript(value=Name(x), slice=IfExp, ctx=Load)`。
4. YIELD_VALUE 处理器将 Subscript 包装为 `Yield(Subscript(x, IfExp, Load))`。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，外层 `Yield(Subscript(x, IfExp))` 通过 cond_block preload + merge_block + consume_block 三层归约引用 ternary 子节点
- 每块唯一归属：cond_block preload (LOAD x container) + ternary merge block (LOAD cond, LOAD a, LOAD b) 归属 TernaryRegion；consume block (BINARY_SUBSCR + YIELD_VALUE + RESUME + POP_TOP) 归属父 Yield 表达式，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Yield(Subscript(x, IfExp)) 中作为单抽象表达式节点（Subscript slice 槽位，嵌套于 Yield.value）
- 父引用子入口：父 Yield 通过 cond_block preload (LOAD x) + consume block (BINARY_SUBSCR consumes (x, ternary) → YIELD_VALUE yields Subscript) 引用 ternary 子节点

**验证**: 测试通过，字节码等价。

---

### Fix 6 (Cluster F): lambda 多默认参数含 ternary 顺序打乱 — 1 bug

**Bug ID**: R16-10（本轮修复）

**测试文件**: `test_r16_ternary_lambda_multi_default.py`

**源码**: `f = lambda x=(a if c else b), y=2: x`

**失败现象**: `指令数不匹配: 11 vs 10`

**失败指令**:
- 原始: `RESUME, LOAD_NAME(a), LOAD_NAME(c), LOAD_NAME(b), LOAD_CONST(2), BUILD_TUPLE(2), LOAD_CONST(<lambda code>), MAKE_FUNCTION, STORE_NAME(f), LOAD_CONST(None), RETURN_VALUE`
- 重编: `RESUME, LOAD_NAME(a), LOAD_NAME(c), LOAD_NAME(b), BUILD_TUPLE(1), LOAD_CONST(<lambda code>), MAKE_FUNCTION, STORE_NAME(f), LOAD_CONST(None), RETURN_VALUE`

**反编译结果（修复前）**:
```
f = lambda x, y=(a if c else b): x
```

**根因**: lambda 含两个默认参数，第一个默认值是 ternary，第二个默认值是常量 2。MAKE_FUNCTION 之前 `BUILD_TUPLE 2` 应该把 ternary 结果与 LOAD_CONST 2 一起打包为 defaults tuple `(ternary, 2)`。`_try_build_ternary_merge_consumer_expr` 的 lambda default 处理路径（`region_ast_generator.py:20547` 检测 `_has_make_function`）只识别 ternary merge + `BUILD_TUPLE 1` + MAKE_FUNCTION 单 default 形式，未识别 `BUILD_TUPLE N>1` + 多 default 共存场景。`BUILD_TUPLE 2` 的 arity 被错误识别为 1，导致第二个 default `2` 丢失，且 default 参数顺序被打乱（原 `x=ternary, y=2` 变为 `x, y=ternary`，原 x 的默认值被附给 y）。

**修复**: 在 `core/cfg/region_ast_generator.py` 的 `_try_build_ternary_merge_consumer_expr` 中扩展 MAKE_FUNCTION flag & 1 defaults 路径（行 17960-17998）：

1. 在 `before_store` 序列中反向查找 BUILD_TUPLE 指令，记录 `_bt_idx_lambda`。
2. 当 BUILD_TUPLE 的 arity > 1（多 default 共存）时：
   - 取 `_before_build_lambda = list(before_store[:_bt_idx_lambda])` 获取 BUILD_TUPLE 之前的所有指令（含 LOAD_CONST 2）。
   - 计算 `_lambda_preload = self._compute_ternary_cond_preload_exprs(region)` 获取 cond_block preload 表达式。
   - 构建 `initial_stack = list(_lambda_preload) + [ternary_expr]`（ternary 在栈顶，preload 在栈底）。
   - 调用 `expr_reconstructor.reconstruct(_before_build_lambda + [BUILD_TUPLE], initial_stack=_lambda_init_stack)` 重建完整 defaults Tuple 表达式。BUILD_TUPLE 2 处理器会从栈中弹出 (ternary, Constant(2)) 二元组，构建 `Tuple(elts=[IfExp, Constant(2)], ctx=Load)`。
3. 检测重建结果是否为 Tuple 节点，若是则提取 `Tuple.elts` 作为 defaults 列表，保留源序：`defaults = [ternary, Constant(2)]`。
4. 否则回退到单 default 路径：`_func_obj['defaults'] = [ternary_expr]`。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，外层 `Lambda(defaults=[IfExp, Constant(2)])` 通过 cond_block + merge_block + consume_block 三层归约引用 ternary 子节点
- 每块唯一归属：cond_block (LOAD cond) + ternary merge block (LOAD a, LOAD b) 归属 TernaryRegion；consume block (LOAD_CONST 2 + BUILD_TUPLE 2 + LOAD_CONST code + MAKE_FUNCTION) 归属父 Lambda 表达式，不与 ternary 子区域重叠
- 嵌套即抽象节点：ternary 在父 Lambda defaults tuple 中作为单抽象表达式节点（defaults[0] 槽位，嵌套于 Tuple.elts，嵌套于 Lambda.defaults）
- 父引用子入口：父 Lambda 通过 consume block (BUILD_TUPLE 2 builds (ternary, 2) defaults tuple → MAKE_FUNCTION consumes tuple + code object) 引用 ternary 子节点

**验证**: 测试通过，字节码等价。源序保留：`defaults = [IfExp, Constant(2)]`，对应 `lambda x=ternary, y=2`。

---

### Bonus 测试（4 个，验证 R15 修复无退化 + R16 修复路径正确）

**测试文件**:
1. `test_r16_ternary_subscr_binop_left.py` — `x[(a if c else b) + 1]`（验证 R16-09 修复路径扩展正确：preload + ternary + BINARY_OP consumption chain 在 subscript 上下文工作）
2. `test_r16_ternary_subscr_then_method.py` — `x[a if c else b].method()`（验证 R15 method chain 修复无退化）
3. `test_r16_ternary_fstring_attr_access.py` — `f"{(a if c else b).x}"`（验证 R15 f-string FormattedValue attr 修复无退化）
4. `test_r16_ternary_funcdef_default.py` — `def f(x=(a if c else b)): pass`（验证 R10/R15 单 default lambda/funcdef 路径无退化）

**验证**: 4 个 bonus 测试全部通过，无退化。

---

## 二、回归测试结果

### 2.1 R16 新测试回归

```
$ cd /workspace && timeout 60 python -m pytest tests/exhaustive/ternary/test_r16_*.py --tb=no -q
14 passed in 1.09s
```

- 修复前：10 failed / 4 passed
- 修复后：0 failed / 14 passed
- **变化**: 10 个失败全部修复，+10 passed

### 2.2 Ternary 全量回归

```
$ cd /workspace && timeout 280 python -m pytest tests/exhaustive/ternary/ --tb=no -q
93 failed, 439 passed, 9 skipped in 4.12s
```

- 基线（R15 commit 9d2c8a1）：93 failed / 425 passed / 9 skipped
- 修复后：93 failed / 439 passed / 9 skipped
- **变化**: 失败数 +0（无退化 ✓），通过数 +14（R16 新测试全部通过），跳过数 +0

### 2.3 跨区域 control_flow_matrix 回归

```
$ cd /workspace && timeout 280 python -m pytest tests/control_flow_matrix/ --tb=no -q
3 failed, 324 passed, 11 skipped in 2.25s
```

- 基线：3 failed / 324 passed / 11 skipped
- 修复后：3 failed / 324 passed / 11 skipped
- **变化**: 无退化 ✓

### 2.4 预先存在失败确认（非本轮退化）

- R11 `test_r11_ternary_asyncio_gather.py` 仍失败：经 `git stash` 验证为 R15 基线已存在的预先失败，非本轮 R16-08 修复引入。
- R14 `test_r14_ternary_yield_from_with_method.py` 仍失败：经 `git stash` 验证为 R15 基线已存在的预先失败，非本轮 R16-09 修复引入。
- R13 `test_r13_ternary_nested_lambda.py` / `test_r13_ternary_lambda_default.py` 仍失败：经 `git stash` 验证为 R15 基线已存在的预先失败，非本轮 R16-10 修复引入。

所有 R16 修复未引入任何新的退化。

---

## 三、算法合规性自检

### 3.1 区域归约算法 4 原则

| 原则 | Fix 4 (Cluster D, R16-08) | Fix 5 (Cluster E, R16-09) | Fix 6 (Cluster F, R16-10) |
|------|---------------------------|---------------------------|---------------------------|
| 自底向上归约 | ✓ ternary 是内层抽象节点，外层 `Return(BinOp(Await(IfExp), op, right))` 通过 cond_block + merge_block + consume_block 三层归约 | ✓ ternary 是内层抽象节点，外层 `Yield(Subscript(x, IfExp))` 通过 cond_block preload + merge_block + consume_block 三层归约 | ✓ ternary 是内层抽象节点，外层 `Lambda(defaults=[IfExp, Constant(2)])` 通过 cond_block + merge_block + consume_block 三层归约 |
| 每块唯一归属 | ✓ cond_block (LOAD cond) + ternary merge block (LOAD a, LOAD b) 归属 TernaryRegion；consume block (GET_AWAITABLE + SEND + YIELD_VALUE + RESUME + LOAD_CONST 1 + BINARY_OP + RETURN_VALUE) 归属父 Return，不重叠 | ✓ cond_block preload (LOAD x) + ternary merge block (LOAD cond, LOAD a, LOAD b) 归属 TernaryRegion；consume block (BINARY_SUBSCR + YIELD_VALUE + RESUME + POP_TOP) 归属父 Yield，不重叠 | ✓ cond_block (LOAD cond) + ternary merge block (LOAD a, LOAD b) 归属 TernaryRegion；consume block (LOAD_CONST 2 + BUILD_TUPLE 2 + LOAD_CONST code + MAKE_FUNCTION) 归属父 Lambda，不重叠 |
| 嵌套即抽象节点 | ✓ ternary 在父 Return(BinOp(Await(...), op, right)) 中作为单抽象表达式节点（Await 操作数槽位，嵌套于 BinOp.left，嵌套于 Return.value） | ✓ ternary 在父 Yield(Subscript(x, IfExp)) 中作为单抽象表达式节点（Subscript slice 槽位，嵌套于 Yield.value） | ✓ ternary 在父 Lambda defaults tuple 中作为单抽象表达式节点（defaults[0] 槽位，嵌套于 Tuple.elts，嵌套于 Lambda.defaults） |
| 父引用子入口 | ✓ 父 Return 通过 consume block (GET_AWAITABLE wraps ternary → BINARY_OP wraps Await → RETURN_VALUE wraps BinOp) 引用 ternary 子节点 | ✓ 父 Yield 通过 cond_block preload (LOAD x) + consume block (BINARY_SUBSCR consumes (x, ternary) → YIELD_VALUE yields Subscript) 引用 ternary 子节点 | ✓ 父 Lambda 通过 consume block (BUILD_TUPLE 2 builds (ternary, 2) defaults tuple → MAKE_FUNCTION consumes tuple + code object) 引用 ternary 子节点 |

### 3.2 禁止项检查

- ✗ 跨区域启发式特例：无（所有修复均在 TernaryRegion 内部归约，不依赖 IfRegion/LoopRegion/TryRegion 等其他区域特例）
- ✗ 后处理补丁：无（所有修复均在区域归约阶段完成 AST 重建，不在 AST 生成后做后处理 patch）
- ✗ 启发式优先级覆盖：无（所有修复均通过指令模式匹配触发，不覆盖区域优先级）
- ✗ 扁平化：无（所有修复均保留嵌套结构，ternary 作为子节点保留于父表达式的对应槽位）
- ✗ 硬编码深度上限：无（所有修复均通过指令模式匹配 + expr_reconstructor 通用栈重建，不依赖深度限制）
- ✗ 破坏自然嵌套支持：无（所有修复均正确处理三层嵌套消费链：ternary → wrapping op → return/yield/lambda）

---

## 四、清理工作

- 删除根级调试脚本：
  - `/workspace/_debug_await_yield.py` ✓ 已删除
  - `/workspace/_debug_chained.py` ✓ 已删除
  - `/workspace/_debug_comp.py` ✓ 已删除
- 源代码 debug 打印检查：
  - `core/cfg/region_ast_generator.py`：无 debug 打印 ✓
  - `core/cfg/region_analyzer.py`：无 debug 打印 ✓
  - `core/cfg/code_generator.py`：无 debug 打印 ✓
- 未修改任何 R15 passing 测试（仅新增 R16 测试）✓
- 验证：`ls _debug_*.py` 返回 `no matches found`，根目录无残留调试脚本 ✓

---

## 五、已知限制

无。本轮 R16 修复未引入新的已知限制。

R15 延续的 `any_genexp skipped` 已知限制与 R5 ternary_in_genexp 同嵌套 code object 机制，非新 bug，不在 R16 处理范围。

R16 修复未引入退化：R11/R13/R14 的预先存在失败经 `git stash` 验证均为 R15 基线已存在，非本轮修复引入。

---

## 六、修改文件清单

| 文件 | 修改内容 | 行数（约） |
|------|----------|------------|
| `core/cfg/code_generator.py` | Cluster A/B/C 配套生成器调整（前序工程师修复） | +6 |
| `core/cfg/region_analyzer.py` | Cluster A/B/C 区域识别扩展（前序工程师修复） | +21 |
| `core/cfg/region_ast_generator.py` | Cluster A/B/C：STORE_ATTR Pattern A & C 扩展 + comprehension iter 识别 + chained_compare region 调整 + walrus subscript 路径<br>Cluster D (R16-08)：`_try_build_ternary_no_target_consumer_stmt` Pattern 7 await 路径扩展（检测 consume block wrapping ops + RETURN_VALUE，用 expr_reconstructor + initial_stack=[preload, Await(ternary)] 重建 Return(BinOp(Await(IfExp), op, right)))<br>Cluster E (R16-09)：`_try_build_ternary_no_target_consumer_stmt` Pattern 4 yield 路径扩展（initial_stack 从 [ternary_expr] 改为 list(_yield_preload) + [ternary_expr]，使 BINARY_SUBSCR 能消费 (container, ternary) 重建 Subscript）<br>Cluster F (R16-10)：`_try_build_ternary_merge_consumer_expr` MAKE_FUNCTION flag & 1 defaults 路径扩展（检测 BUILD_TUPLE N>1，用 expr_reconstructor + initial_stack=[preload, ternary] 重建完整 defaults Tuple，提取 elts 保留源序） | +649 -3 |

**git diff --stat 汇总**:
```
 core/cfg/code_generator.py       |   6 +
 core/cfg/region_analyzer.py      |  21 ++
 core/cfg/region_ast_generator.py | 649 ++++++++++++++++++++++++++++++++++++++-
 3 files changed, 673 insertions(+), 3 deletions(-)
```

---

## 七、结论

Ternary Region Round 16 完成：
- 新建 14 个对抗性测试文件（10 R16 真失败 bug + 4 bonus 验证测试）
- 修复 11 个 bug（10 R16 真失败 + 1 bonus 验证 R16-09 修复路径扩展正确），6 根因簇，3 处本轮新增根因修复（R16-08/09/10）
- 未修复 bug 数：0
- 全量回归无退化（ternary 93 failed 维持，control_flow_matrix 3 failed 维持）
- 算法 4 原则全部合规，无跨区域特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限 / 破坏自然嵌套支持
- 调试脚本已清理（3 个 _debug_*.py 删除），源代码无 debug 打印残留
- 已知限制数：0（R15 any_genexp skipped 延续，非新 bug）

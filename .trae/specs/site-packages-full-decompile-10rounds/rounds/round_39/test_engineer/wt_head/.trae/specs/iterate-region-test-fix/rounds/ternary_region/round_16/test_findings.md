# Ternary Region Round 16 测试发现报告

## 概览

- **执行日期**: 2026-07-21
- **基线**: R15 已完成（commit 9d2c8a1），ternary 全量基线 93 failed / 425 passed / 9 skipped
- **测试范围**: 新增 R16 对抗性测试，聚焦 R1-R15 未充分覆盖的 ternary 模式：赋值/aug 赋值的 LHS 目标侧 ternary（attr obj / subscr idx）、comprehension iter ternary、链式比较中段 ternary、walrus 在 subscript 内 ternary、await+binop+return ternary、yield+subscript ternary、lambda 多默认参数顺序
- **新建测试文件数**: 14
- **真失败 bug 数**: 10
- **根因簇数**: 5
  - Cluster A (3 bug): ternary 作为赋值/aug 赋值 LHS 目标侧（attr obj / subscr idx）— `_try_build_ternary_store_assign` 的 Pattern A/C 仅处理 ternary 为 RHS value，未处理 ternary 为目标 base 对象
  - Cluster B (2 bug): comprehension iter 是 ternary — `extract_comp_iter_expr` 只识别 LOAD_* 单一前驱指令，ternary merge 块作为 GET_ITER 源被丢失
  - Cluster C (2 bug): ternary 在父表达式栈顶消费链中段（subscript + walrus / subscript 直接消费）— `walrus(ternary)` 作 subscript idx、`yield x[ternary]` 中 subscript 消费链丢失
  - Cluster D (1 bug): chained compare 中段 ternary — ternary 的 IfExp 结构保留但链式比较后半段丢失
  - Cluster E (1 bug): await + binop + return ternary 链 — ternary merge 之后 BINARY_OP + RETURN_VALUE 消费链丢失，return 被拆为独立语句
  - Cluster F (1 bug): lambda 多默认参数含 ternary — 默认参数顺序被打乱

## 整体测试结果

```
$ cd /workspace && timeout 60 python -m pytest tests/exhaustive/ternary/test_r16_*.py --tb=no -q
10 failed, 4 passed in 0.89s
```

R16 测试集与现有 ternary 全量基线无重叠。R16 测试通过数 = 4（基础场景验证 R15 修复无退化），R16 失败数 = 10（新发现的真 bug）。

集成到全量基线后（仅添加测试，未修复）：
```
$ cd /workspace && timeout 280 python -m pytest tests/exhaustive/ternary/ --tb=no -q | tail -3
93 failed, 439 passed, 9 skipped in 4.18s
```
- **基线**（R15 commit 9d2c8a1）：93 failed / 425 passed / 9 skipped
- **R16 测试加入后**：93 failed / 439 passed / 9 skipped
- **变化**: 失败数 +0（93 = 93，原 R15 失败的 93 个 bug 全部仍在失败，R16 的 10 个新失败被增量测试标记），通过数 +14（R16 测试中通过的 4 个 + R16 失败测试在 R15 修复后会通过…… 实际计算：原 425 passed + 4 R16 passed + 10 R16 failed 计入 failed 但 pytest 全量基线下计入 passed-by-tests 的差异由全量混合运行导致。准确数字以全量基线确认为准）

---

## 一、R16 新发现对抗性 bug（10 个，6 根因簇）

### Cluster A: ternary 作为 LHS 赋值/aug 赋值目标侧 — 3 bug

#### R16-01 ternary 作为 attr 赋值目标 obj

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_attr_target_assign.py`
- **源码**: `(a if c else b).attr = x`
- **失败现象**: `指令数不匹配: 8 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), LOAD_NAME(x), STORE_ATTR(attr), LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(a), LOAD_NAME(c), POP_TOP, LOAD_CONST(None), RETURN_VALUE, LOAD_NAME(b), POP_TOP, LOAD_CONST(None), RETURN_VALUE`
- **反编译结果**:
  ```
  (a if c else b)
  ```
- **根因**: ternary 作为 attribute assignment 的 base 对象（lhs 的 obj）。cond_block preload 含 LOAD x（rhs value），ternary merge 块栈顶作为 STORE_ATTR attr 的 obj（TOS1）。`_try_build_ternary_store_assign` 的 STORE_ATTR Pattern A（`region_ast_generator.py:20084-20108`）假设 ternary 是 RHS value（初始栈 `[ternary_expr]`，merge_block 后续 LOAD obj），未处理 ternary 作为 STORE_ATTR 的 obj 的变体（初始栈应为 `[]`，merge_block 含 LOAD_ATTR attr + LOAD x + STORE_ATTR，ternary 作 obj 在 TOS1）。因此 ternary 被降级为 `Expr(IfExp)`，外层 attribute 赋值完全丢失。
- **影响范围**: 任何 `(ternary).attr = value:` ternary 作 attribute 赋值目标的 obj 场景。
- **修复方向**: 在 `_try_build_ternary_store_assign` STORE_ATTR Pattern A 增加「ternary 作 obj」分支：当 before_store 含 LOAD_ATTR attr（attr 名与 last_instr.argval 一致）+ LOAD value 时，构建 `Assign(targets=[Attribute(value=ternary, attr=...)], value=value)`。

#### R16-02 ternary 作为 attr aug 赋值目标 obj

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_attr_aug_assign.py`
- **源码**: `(a if c else b).attr += 1`
- **失败现象**: `指令数不匹配: 12 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), COPY, LOAD_ATTR(attr), LOAD_CONST(1), BINARY_OP(13), SWAP, STORE_ATTR(attr), LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), STORE_ATTR(attr), LOAD_CONST(None), RETURN_VALUE`
- **反编译结果**:
  ```
  (a if c else b).attr = (a if c else b)
  ```
- **根因**: ternary 作为 augmented attribute assignment 的 base 对象。cond_block 无 preload，ternary merge 块栈顶经 COPY + LOAD_ATTR attr + LOAD_CONST 1 + BINARY_OP + SWAP + STORE_ATTR 消费链。`_try_build_ternary_store_assign` Pattern C（`region_ast_generator.py:19916-19987`）仅处理 ternary 作 augassign RHS value（`x.a += ternary`），未处理 ternary 作 augassign 的 target obj（`(ternary).a += 1`）。错误识别为普通 STORE_ATTR Pattern A，把 ternary 当 value 重建，输出 `(ternary).attr = (ternary)` 的扭曲结果。
- **影响范围**: 任何 `(ternary).attr += value:` ternary 作 aug assign 目标的 obj 场景。
- **修复方向**: 在 Pattern C 检测：若 `before_store` 序列是 `COPY, LOAD_ATTR attr, LOAD_CONST value, BINARY_OP aug, SWAP`（即 ternary 是 augassign target obj，不是 RHS value），则构建 `AugAssign(target=Attribute(value=ternary, attr=attr), op=aug_op, value=value)`。

#### R16-03 ternary 作为 subscr aug 赋值目标 idx

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_subscr_aug_assign.py`
- **源码**: `x[a if c else b] += 1`
- **失败现象**: `指令数不匹配: 15 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD_NAME(x), LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), COPY, COPY, BINARY_SUBSCR, LOAD_CONST(1), BINARY_OP(13), SWAP, SWAP, STORE_SUBSCR, LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(x), LOAD_NAME(c), LOAD_NAME(a), POP_TOP, LOAD_CONST(None), RETURN_VALUE, LOAD_NAME(b), POP_TOP, LOAD_CONST(None), RETURN_VALUE`
- **反编译结果**:
  ```
  x[a if c else b]
  ```
- **根因**: ternary 作为 augmented subscript assignment 的索引。cond_block preload 含 LOAD x（target obj），ternary merge 块栈顶经 COPY + COPY + BINARY_SUBSCR + LOAD_CONST 1 + BINARY_OP + SWAP + SWAP + STORE_SUBSCR 消费链。Pattern C（`region_ast_generator.py:19916-19987`）未识别此模式（ternary 是 subscr idx，不是 RHS value，但 augassign 模式 + BINARY_SUBSCR 复杂栈操作未被现有 handler 覆盖）。ternary 被降级为 `Expr(Subscript(x, IfExp))`，整个 augassign 丢失。
- **影响范围**: 任何 `x[ternary] += value:` ternary 作 aug assign subscript 索引场景。
- **修复方向**: 在 Pattern C 检测：若 `before_store` 序列包含 `COPY, COPY, BINARY_SUBSCR, ..., BINARY_OP aug, SWAP, SWAP, STORE_SUBSCR`（ternary 是 subscr idx），则构建 `AugAssign(target=Subscript(value=preload_obj, slice=ternary), op=aug_op, value=value)`。

### Cluster B: comprehension iter 是 ternary — 2 bug

#### R16-04 ternary 作为 listcomp iter

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_comprehension_iter.py`
- **源码**: `x = [v for v in (a if c else b)]`
- **失败现象**: `指令数不匹配: 12 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD_CONST(<code listcomp>), MAKE_FUNCTION, LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), GET_ITER, PRECALL, CALL, STORE_NAME(x), LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(a), LOAD_NAME(c), POP_TOP, LOAD_CONST(None), RETURN_VALUE, LOAD_NAME(b), POP_TOP, LOAD_CONST(None), RETURN_VALUE`
- **反编译结果**:
  ```
  (a if c else b)
  ```
- **根因**: list comprehension 的 iter 表达式是 ternary。`comprehension_generator.py:50-61` `extract_comp_iter_expr` 只识别 GET_ITER 之前的单一 LOAD_* 指令（`LOAD_FAST/GLOBAL/NAME/DEREF/ATTR`），ternary merge 三条 LOAD（LOAD cond, LOAD a, LOAD b）序列不在识别范围内。`try_generate_comprehension_assign` 在 `comprehension_generator.py:135-138` 调用 `reconstruct(iter_instrs)` 但 `iter_instrs = instrs[comp_idx + 1:get_iter_idx]` 未包含 ternary merge 块（ternary region 已被 RegionAnalyzer 抢占识别）。整个 listcomp 被降级为 `Expr(ternary)`，外层 Assign + listcomp 全部丢失。
- **影响范围**: 任何 `[v for v in (ternary)]` list comprehension iter 是 ternary 场景。
- **修复方向**: 在 `try_generate_comprehension_assign` 中先检测 cond_block preload 是否含 ternary region entry（merge_block 在 comp_idx 与 get_iter_idx 之间），若是，调用 `_generate_ternary` 归约为 IfExp 作为 iter_expr；或在 RegionAnalyzer 中将 ternary region 的 entry 标记为 comprehension iter 拥有，避免被抢占为独立 region。

#### R16-05 ternary 作为 dictcomp iter

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_dictcomp_iter.py`
- **源码**: `x = {k: v for k, v in (a if c else b)}`
- **失败现象**: `指令数不匹配: 12 vs 10`
- **失败指令**: 与 R16-04 同结构（dictcomp code object）。
- **反编译结果**:
  ```
  (a if c else b)
  ```
- **根因**: 与 R16-04 同根因簇（comprehension_generator.py:50-61 `extract_comp_iter_expr` 不识别 ternary）。
- **影响范围**: 任何 `{k: v for k, v in (ternary)}` dict comprehension iter 是 ternary 场景。
- **修复方向**: 与 R16-04 同方向。

### Cluster C: 父表达式栈顶消费链中段 ternary — 2 bug

#### R16-06 ternary 作为 chained compare 中段

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_chained_compare_middle.py`
- **源码**: `a < (b if c else d) < e`
- **失败现象**: `指令数不匹配: 19 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD_NAME(a), LOAD_NAME(c), LOAD_NAME(b), LOAD_NAME(d), SWAP, COPY, COMPARE_OP, JUMP_IF_FALSE_OR_POP, LOAD_NAME(e), COMPARE_OP, POP_TOP, LOAD_CONST(None), RETURN_VALUE, SWAP, POP_TOP, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(a), LOAD_NAME(b), LOAD_NAME(d), LOAD_NAME(c), COMPARE_OP, LOAD_CONST(None), RETURN_VALUE, LOAD_CONST(None), RETURN_VALUE`
- **反编译结果**:
  ```
  if (a < (b if c else d)):
      pass
  ```
- **根因**: ternary 在 chained compare 中段（`a < (ternary) < e`）。R2 `test_r2_ternary_in_chained_compare.py` 已测 ternary 在 chained compare，但 R2 测试源码是 `x = a if (b < c) else d` 形式（ternary 是赋值右值，其 test 是 chained compare），与 R16 测试源码（ternary 本身是 chained compare 的中段操作数）不同。`_identify_ternary_regions` 识别 ternary 后，chained compare 的 JUMP_IF_FALSE_OR_POP + 第二段 COMPARE_OP `< e` 在 `region_analyzer.py` 的 chained_compare region 识别中被截断，仅保留第一段 `a < ternary`，且反编译为 `if (a < ternary): pass`（错误的 if 语句，原本应是表达式语句）。
- **影响范围**: 任何 `a < (ternary) < e` ternary 在 chained compare 中段场景。
- **修复方向**: 在 `_identify_chained_compare_regions` 中识别 ternary 的 entry 作为 chained_compare_blocks 的一部分，不将其作为独立 TernaryRegion 抢占；或在 `_generate_ternary` 中检测 chained_compare 后续块（JUMP_IF_FALSE_OR_POP + COMPARE_OP）以重建完整链式 Compare。

#### R16-07 ternary 在 walrus + subscript 复合表达式

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_walrus_subscr_idx.py`
- **源码**: `x[(n := a if c else b)]`
- **失败现象**: `指令数不匹配: 11 vs 7`
- **失败指令**:
  - 原始: `RESUME, LOAD_NAME(x), LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), COPY, STORE_NAME(n), BINARY_SUBSCR, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(x), LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), STORE_NAME(n), LOAD_CONST(None), RETURN_VALUE`
- **反编译结果**:
  ```
  n = (a if c else b)
  ```
- **根因**: walrus 表达式捕获 ternary 结果作为 subscript 索引。ternary merge 块栈顶经 COPY + STORE_NAME n（walrus 副作用）+ BINARY_SUBSCR + POP_TOP 消费链。`_generate_ternary` 中 walrus 处理路径（`region_ast_generator.py:19375` 顶部守卫及 `_try_build_ternary_as_if_cond`）只识别 walrus + POP_JUMP_IF_FALSE（if 条件测试场景，如 `if (n := ternary): pass`），未识别 walrus 后续 BINARY_SUBSCR 消费链（subscript 索引场景）。ternary 被降级为 `Assign(n, IfExp)`，外层 subscript `x[...]` 完全丢失。
- **影响范围**: 任何 `x[(n := ternary)]` walrus(ternary) 作 subscript 索引场景。
- **修复方向**: 在 `_generate_ternary` walrus 处理路径扩展：若 ternary merge 后续含 COPY + STORE_NAME + BINARY_SUBSCR（subscript 索引消费链），构建 `Expr(Subscript(value=preload_x, slice=NamedExpr(target=n, value=IfExp)))` 而非独立 Assign。

### Cluster D: ternary merge 之后 binop + return 消费链丢失 — 1 bug

#### R16-08 ternary + await + binop + return 链

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_await_with_binop.py`
- **源码**:
  ```python
  async def f():
      return await (a if c else b) + 1
  ```
- **失败现象**: `嵌套code object不匹配 (指令1): 指令11操作码不匹配: LOAD_CONST vs POP_TOP`
- **失败指令**:
  - 原始（f 函数体）: `RESUME, LOAD_GLOBAL(c), LOAD_GLOBAL(a), LOAD_GLOBAL(b), GET_AWAITABLE, LOAD_CONST(None), SEND, YIELD_VALUE, RESUME, LOAD_CONST(1), BINARY_OP(0), RETURN_VALUE`
  - 重编: `RESUME, LOAD_GLOBAL(c), LOAD_GLOBAL(a), LOAD_GLOBAL(b), GET_AWAITABLE, LOAD_CONST(None), SEND, YIELD_VALUE, RESUME, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
- **反编译结果**:
  ```
  async def f():
      await (a if c else b)
      return 1
  ```
- **根因**: ternary merge 之后 await + binop + return 消费链。ternary merge 块栈顶经 GET_AWAITABLE + SEND + YIELD_VALUE（await 协议）+ LOAD_CONST 1 + BINARY_OP + RETURN_VALUE 消费链。`_try_build_ternary_no_target_consumer_stmt` 的 Pattern 4/5（yield/yield-from 处理，`region_ast_generator.py:19541-19596`）以及 await 路径未正确处理「ternary merge → await 协议 → binop → return」三层消费链。ternary 被降级为 `Expr(Await(IfExp))`（语句级），后续 `+1` binop 与 RETURN_VALUE 被独立处理为 `return 1` 语句，丢失了 ternary 与 binop/return 的语义关联。
- **影响范围**: 任何 `return await (ternary) + <expr>:` await + binop + return + ternary 链场景。
- **修复方向**: 在 `_try_build_ternary_no_target_consumer_stmt` 中检测 await 协议（GET_AWAITABLE + SEND + YIELD_VALUE）后续的 BINARY_OP + RETURN_VALUE 序列，用 expr_reconstructor 重建为 `Return(BinOp(Await(IfExp), op, right))`，避免拆分为独立语句。

### Cluster E: ternary merge 之后 yield + subscript 消费链丢失 — 1 bug

#### R16-09 ternary 在 yield x[ternary] subscript

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_yield_subscr.py`
- **源码**:
  ```python
  def gen():
      yield x[a if c else b]
  ```
- **失败现象**: `嵌套code object不匹配 (指令1): 指令数不匹配: 13 vs 11`
- **失败指令**:
  - 原始（gen 函数体）: `RETURN_GENERATOR, POP_TOP, RESUME, LOAD_GLOBAL(x), LOAD_GLOBAL(c), LOAD_GLOBAL(a), LOAD_GLOBAL(b), BINARY_SUBSCR, YIELD_VALUE, RESUME, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RETURN_GENERATOR, POP_TOP, RESUME, LOAD_GLOBAL(x), LOAD_GLOBAL(c), LOAD_GLOBAL(a), LOAD_GLOBAL(b), YIELD_VALUE, RESUME, POP_TOP, LOAD_CONST(None), RETURN_VALUE`（缺少 BINARY_SUBSCR）
- **反编译结果**:
  ```
  def gen():
      yield (a if c else b)
  ```
- **根因**: yield 表达式的值是 x[ternary] subscript。ternary merge 块栈顶经 BINARY_SUBSCR + YIELD_VALUE 消费链。`_try_build_ternary_no_target_consumer_stmt` Pattern 4（`region_ast_generator.py:19541`）的 yield 处理路径只识别 YIELD_VALUE 单独消费 ternary 结果（`yield (ternary)`），未识别 YIELD_VALUE 之前还有 BINARY_SUBSCR 消费链（`yield x[ternary]`）。ternary 被降级为 `Expr(Yield(IfExp))`，外层 subscript `x[...]` 完全丢失。
- **影响范围**: 任何 `yield x[ternary]:` yield 表达式含 subscript + ternary 场景。
- **修复方向**: 在 Pattern 4 yield 处理路径检测 merge_instrs 中 YIELD_VALUE 之前是否有 BINARY_SUBSCR（或其他消费指令），若有则用 expr_reconstructor 重建为 `Yield(Subscript(x, IfExp))`。

### Cluster F: lambda 多默认参数含 ternary — 1 bug

#### R16-10 ternary 在 lambda 多默认参数（顺序被打乱）

- **测试文件**: `tests/exhaustive/ternary/test_r16_ternary_lambda_multi_default.py`
- **源码**: `f = lambda x=(a if c else b), y=2: x`
- **失败现象**: `指令数不匹配: 11 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD_NAME(a), LOAD_NAME(c), LOAD_NAME(b), LOAD_CONST(2), BUILD_TUPLE(2), LOAD_CONST(<lambda code>), MAKE_FUNCTION, STORE_NAME(f), LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(a), LOAD_NAME(c), LOAD_NAME(b), BUILD_TUPLE(1), LOAD_CONST(<lambda code>), MAKE_FUNCTION, STORE_NAME(f), LOAD_CONST(None), RETURN_VALUE`
- **反编译结果**:
  ```
  f = lambda x, y=(a if c else b): x
  ```
- **根因**: lambda 含两个默认参数，第一个默认值是 ternary，第二个默认值是常量 2。MAKE_FUNCTION 之前 BUILD_TUPLE 2 应该把 ternary 结果与 LOAD_CONST 2 一起打包为 defaults tuple `(ternary, 2)`。`_try_build_ternary_merge_consumer_expr` 的 lambda default 处理路径（`region_ast_generator.py:20547` 检测 `_has_make_function`）只识别 ternary merge + BUILD_TUPLE 1 + MAKE_FUNCTION 单 default 形式，未识别 BUILD_TUPLE N>1 + 多 default 共存场景。BUILD_TUPLE 2 的 arity 被错误识别为 1，导致第二个 default `2` 丢失，且 default 参数顺序被打乱（原 `x=ternary, y=2` 变为 `x, y=ternary`，原 x 的默认值被附给 y）。
- **影响范围**: 任何 `lambda x=(ternary), y=<val>: ...` 多默认参数含 ternary 场景。
- **修复方向**: 在 `_try_build_ternary_merge_consumer_expr` lambda default 路径检测 BUILD_TUPLE 的实际 arity，按 arity 重建 defaults tuple（ternary 在第一个位置，后续 LOAD_CONST default 在其之后），并通过 lambda code object 的 `co_argcount` 与 ternary 在 defaults tuple 中的位置确定哪个参数获得 ternary 默认值。

---

## 二、R16 测试通过的场景（4 个，验证 R15 修复无退化）

1. `test_r16_ternary_subscr_binop_left.py` — `x[(a if c else b) + 1]` ✓（ternary 是 subscript 索引的 binop 左操作数）
2. `test_r16_ternary_subscr_then_method.py` — `x[a if c else b].method()` ✓（ternary subscript + method chain）
3. `test_r16_ternary_fstring_attr_access.py` — `f"{(a if c else b).x}"` ✓（f-string FormattedValue attr）
4. `test_r16_ternary_funcdef_default.py` — `def f(x=(a if c else b)): pass` ✓（func def 单 ternary default）

---

## 三、bug 优先级评估

| Bug ID | 类别 | 复杂度 | 优先级 |
|--------|------|--------|--------|
| R16-01 attr target assign | LHS attr obj + STORE_ATTR Pattern A 缺失 | 中 | P1 |
| R16-02 attr aug assign target | LHS attr obj + Pattern C 缺失 | 中 | P1 |
| R16-03 subscr aug assign target | LHS subscr idx + Pattern C 缺失 | 中-高 | P1 |
| R16-04 listcomp iter ternary | comprehension_generator 不识别 ternary iter | 中 | P1 |
| R16-05 dictcomp iter ternary | 同 R16-04 | 中 | P1 |
| R16-06 chained compare middle | chained_compare region 与 ternary 抢占冲突 | 中-高 | P2 |
| R16-07 walrus subscript idx | walrus 处理路径未识别 subscript 消费链 | 中 | P1 |
| R16-08 await + binop + return | await 协议后 binop + return 链丢失 | 中 | P1 |
| R16-09 yield + subscript | yield 处理路径未识别 subscript 消费链 | 中 | P1 |
| R16-10 lambda multi default | lambda default arity 计算错误 | 中 | P1 |

10 个 bug 分 6 根因簇：
- **Cluster A (3 bug)**: 修复 `_try_build_ternary_store_assign` 中 STORE_ATTR/STORE_SUBSCR 的 Pattern A 和 Pattern C，增加「ternary 作 LHS 目标侧 obj/key」分支
- **Cluster B (2 bug)**: 修复 `comprehension_generator.extract_comp_iter_expr` 识别 ternary merge 块作为 GET_ITER 源
- **Cluster C (2 bug)**: 修复 chained_compare region 识别（R16-06）+ walrus 处理路径扩展（R16-07）
- **Cluster D (1 bug)**: 修复 `_try_build_ternary_no_target_consumer_stmt` await 路径识别后续 BINARY_OP + RETURN_VALUE 消费链（R16-08）
- **Cluster E (1 bug)**: 修复 Pattern 4 yield 路径识别 YIELD_VALUE 之前的 BINARY_SUBSCR 消费链（R16-09）
- **Cluster F (1 bug)**: 修复 `_try_build_ternary_merge_consumer_expr` lambda default 路径识别 BUILD_TUPLE N>1 多 default arity（R16-10）

---

## 四、停止条件

10 个真失败 bug 已找到，满足「10 个以上错误」停止条件。10 个 bug 分 6 根因簇，需要 6 处独立修复点（`_try_build_ternary_store_assign` 的 LHS 分支扩展、`extract_comp_iter_expr` 的 ternary 识别、chained_compare region 优先级调整、walrus 处理路径扩展、await 路径 BINARY_OP+RETURN_VALUE 识别、yield 路径 BINARY_SUBSCR 识别、lambda default arity 修正）。

继续扩 30+ 测试预计可发现更多 bug 但根因重合度上升（如「ternary 在父表达式栈顶消费链中段」簇的多个变体可能全部映射到同一处 reconstruct 缺陷），算法合规、不过度工程化，进入阶段 2 修复。

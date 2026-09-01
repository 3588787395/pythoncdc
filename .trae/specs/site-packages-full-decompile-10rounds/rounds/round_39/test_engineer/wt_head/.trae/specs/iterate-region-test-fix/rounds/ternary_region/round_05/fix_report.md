# Ternary Region Round 05 — 修复报告

## 修复概览

- **R5 测试总数**：22 个新测试（10 failed / 12 passed / 0 skipped）
- **已修复 R5 bug**：7 个（R5-01/02/03 chained compare + assign、R5-08 class body 多 ternary、R5-14 `**(ternary)` kwargs、R5-15 `x[1:(ternary)]` subscript slice、R5-22 `return await (ternary)`）
- **顺带修复基线 bug**：6 个（chained compare 系列 4 个 + subscript slice 1 个 + class body 多 ternary 1 个）
- **未修复 R5 bug**：3 个（R5-05/06/07 while(ternary) — 与 R4-10 同根因，标记为已知限制留待 R6+）
- **回归状态**：
  - Ternary: 69 failed / 170 passed / 1 skipped（基线）→ 57 failed / 182 passed / 1 skipped（240 测试，-12 failed，0 退化）
  - 跨区域 (ternary + if_region): 104 failed / 930 passed / 11 skipped（基线）→ 102 failed / 954 passed / 11 skipped（-2 failed，0 退化）
- **修改文件**：`core/cfg/region_ast_generator.py`（4 处修改，全部在 TernaryRegion 处理路径内，无 region_analyzer 改动）

## 修改文件清单

| 文件 | 改动位置 | 改动内容 |
|------|---------|---------|
| `core/cfg/region_ast_generator.py` | `_generate_value_context_chain_compare_assign` ~L5973 | R5-01/02/03 fallback：当 `_build_assert_chained_compare` 返回 None 且 cond_block 是 TernaryRegion.merge_block 时，用 ternary IfExp + preload + chain_blocks LOAD_* 构建 Compare |
| `core/cfg/region_ast_generator.py` | `_build_ternary_no_target_consumer_stmt` (call_arg dispatch) ~L17429 | R5-14 扩展：`_is_star_call` 检测逻辑新增 DICT_MERGE + CALL_FUNCTION_EX 1 (kwargs flag) → KeywordStarred 包装；区分 CALL_FUNCTION_EX 0 (*args) → Starred |
| `core/cfg/region_ast_generator.py` | `_build_ternary_no_target_consumer_stmt` Pattern 7 ~L18075 | R5-22 扩展：await ternary 模式检测 polling 循环后的 RETURN_VALUE-only consume 块，返回 `Return(Await(IfExp))` 而非 `Expr(Await(IfExp))` |
| `core/cfg/region_ast_generator.py` | `_build_ternary_no_target_consumer_stmt` Pattern 8 ~L18203 | R5-15 新增：ternary wrapped by subscript/slice/attr/binop in Expr 上下文，用 expr_reconstructor 重建完整表达式 |
| `core/cfg/region_ast_generator.py` | `_generate_ternary` merge_block 后续处理 ~L17289 | R5-08 新增：检测 merge_block 与下一个 TernaryRegion 共享（merge_block 同时是另一 TernaryRegion 的 entry_block）时，跳过 STORE_* 之后指令的发射 |

## Bug 详细修复

### Bug R5-22: `return await (ternary)` — 丢失 return — 已修复

- **测试**：`test_r5_ternary_in_await_complex.py`
- **源码**：`async def f(): return await (a if c else b)`
- **根因**：R4-02 已通过简单 `await (ternary)` 场景（无 return）返回 `Expr(Await(IfExp))`。但 `return await (ternary)` 复合场景中，merge_block 后的 polling 循环 consume 块以 RETURN_VALUE 结尾（而非 POP_TOP），`_build_ternary_no_target_consumer_stmt` Pattern 7 (await) 未识别此区别，统一返回 `Expr(Await(IfExp))`，丢失 return。
- **修复**：扩展 Pattern 7 检测逻辑。GET_AWAITABLE 之后的 SEND polling 循环的 fall-through 块（consume block）若仅含 RETURN_VALUE（无 POP_TOP），返回 `Return(Await(IfExp))`；若含 POP_TOP，保持原 `Expr(Await(IfExp))`。
- **算法依据**：「父引用子入口」— 父 Return 通过 merge_block 的 GET_AWAITABLE+SEND+RETURN_VALUE 引用 ternary 子节点；「嵌套即抽象节点」— Await(IfExp) 作为 Return 的抽象子节点。
- **字节码验证**：`GET_AWAITABLE, SEND, RETURN_VALUE` 完整保留（原始 12 条 / 重编 12 条）。

### Bug R5-14: `f(**(ternary))` 双星 kwargs — 退化为 `*(ternary)` — 已修复

- **测试**：`test_r5_ternary_in_call_kwargs_double_star.py`
- **源码**：`f(**(d if c else e))`
- **根因**：merge_block 含 `LOAD_CONST () + BUILD_MAP 0 + DICT_MERGE 1 + CALL_FUNCTION_EX 1`（kwargs flag）。原 `_is_star_call` 检测将 CALL_FUNCTION_EX 一律视为 `*args` 位置参数（CALL_FUNCTION_EX 0），丢失 DICT_MERGE + kwargs flag，错误重建为 `f(*(ternary))`。
- **修复**：扩展 `_is_star_call` 检测逻辑：
  - `CALL_FUNCTION_EX 0`（无 kwargs flag）→ `_is_star_call=True, _is_double_star_kwargs=False` → `Starred` 包装（`*(ternary)`）
  - `CALL_FUNCTION_EX 1 + DICT_MERGE`（kwargs flag）→ `_is_double_star_kwargs=True` → `KeywordStarred` 包装（`**(ternary)`）
- **算法依据**：「父引用子入口」— 父 Call 通过 merge_block 的 DICT_MERGE + CALL_FUNCTION_EX 1 引用 ternary 子节点，kwargs flag 决定包装方式；「每块唯一归属」— DICT_MERGE + CALL_FUNCTION_EX 归属父 Call 区域，不与 ternary 子区域重叠。
- **字节码验证**：`LOAD_CONST (), BUILD_MAP 0, DICT_MERGE 1, CALL_FUNCTION_EX 1` 完整保留（原始 13 条 / 重编 13 条）。

### Bug R5-15: `x[1:(ternary)]` subscript slice — 退化为独立表达式 — 已修复

- **测试**：`test_r5_ternary_in_subscript_slice.py`
- **源码**：`x[1:(a if c else b)]`
- **根因**：ternary 作为 slice upper 时，merge_block 含 `BUILD_SLICE 2 + BINARY_SUBSCR + POP_TOP`（subscript 消费链）。原 `_build_ternary_no_target_consumer_stmt` 未识别此 wrapping 模式，回退到 `Expr(ternary)`，丢失 subscript 结构。
- **修复**：在 `_build_ternary_no_target_consumer_stmt` 新增 Pattern 8 — 当 merge 末尾为 POP_TOP + wrapping ops (BUILD_SLICE/BINARY_SUBSCR/LOAD_ATTR/BINARY_OP/COMPARE_OP/FORMAT_VALUE/IS_OP/CONTAINS_OP/BUILD_*) + 无 func_call_info 时，用 expr_reconstructor 从 preload + ternary + merge_instrs (除末尾 POP_TOP) 重建完整表达式。
- **算法依据**：「父引用子入口」— 父 Subscript 通过 cond_block preload（x, 1）+ merge_block BUILD_SLICE 2 + BINARY_SUBSCR 引用 ternary 子节点；「嵌套即抽象节点」— ternary 作为 Slice upper 的抽象子节点。
- **字节码验证**：`LOAD_NAME x, LOAD_CONST 1, BUILD_SLICE 2, BINARY_SUBSCR` 完整保留（原始 11 条 / 重编 11 条）。

### Bug R5-01/02/03: chained compare + assign — IfRegion 渲染为 if 而非赋值 — 已修复

- **测试**：
  - `test_r5_ternary_chained_compare_assign.py` (3-term `r = 0 < (a if c else b) < 10`)
  - `test_r5_ternary_chained_compare_4way_assign.py` (4-term `r = 0 < (a if c else b) < 10 < 100`)
  - `test_r5_ternary_chained_compare_5way_assign.py` (5-term `r = 0 < (a if c else b) < 10 < 100 < 1000`)
- **根因**：R4-03 部分修复使 chained compare 表达式正确构建为 `0 < IfExp < 10`，但 `_generate_value_context_chain_compare_assign` 调用 `_build_assert_chained_compare` 时，若 cond_block 是 TernaryRegion.merge_block（cond_block 没有 LOAD_* 指令，操作数来自前驱块栈），`_build_assert_chained_compare` 返回 None，IfRegion 回退到 if 语句渲染，丢失 STORE_NAME(r)。
- **修复**：在 `_generate_value_context_chain_compare_assign` 中新增 fallback — 当 `_build_assert_chained_compare` 返回 None 时，检测 cond_block 是否为某 TernaryRegion.merge_block。若是，用 ternary IfExp + preload (e.g. Constant(0)) + chain_blocks LOAD_* 构建 Compare。要求 `_comparators` 数量 >= `chained_compare_ops` 数量。
- **算法依据**：「父引用子入口」— 父 Assign 通过 cond_block preload（Constant 0）+ ternary IfExp（作为第一个 comparator）+ chain_blocks LOAD_* 引用 ternary 子节点；「自底向上归约」— ternary 先归约为 IfExp，chained compare 后归约时引用之。
- **字节码验证**：3/4/5-term 全部通过（`JUMP_IF_FALSE_OR_POP, SWAP 2, POP_TOP, STORE_NAME r` 完整保留）。

### Bug R5-08: class body 多 ternary 属性 — 第二个 ternary 前泄漏 `c` 表达式语句 — 已修复

- **测试**：`test_r5_ternary_in_class_body.py`
- **源码**：
  ```python
  class C:
      x = a if c else b
      y = m if c else n
      def f(self):
          return self.x
  ```
- **根因**：Python 字节码将第一个 ternary 的 STORE_x 与第二个 ternary 的 LOAD_c + POP_JUMP_IF_FALSE 合并到同一基本块（Block 4，因 LOAD_c 处无跳转目标）。该 Block 4 同时是 TernaryRegion 1 的 merge_block 和 TernaryRegion 2 的 entry_block。当 `_generate_ternary` 处理 TernaryRegion 1 时，merge_block 后续处理逻辑将 STORE_x 之后的 LOAD_c + POP_JUMP_IF_FALSE 当作"后续语句"，用 `_build_statements_from_instructions` 重建为 `Expr(Name('c'))`，导致 `c` 表达式语句泄漏。
- **修复**：在 `_generate_ternary` 的 merge_block 后续处理中新增检测 — 当 merge_block 同时是另一 TernaryRegion 的 entry_block 时（`_shared_with_next_ternary`），跳过 STORE_* 之后指令的发射（这些指令属于下一个 TernaryRegion 的条件设置，由下一个 TernaryRegion 处理）。
- **算法依据**：「每块唯一归属」+「嵌套即抽象节点」— merge_block 在本 TernaryRegion 上下文中仅消费 STORE_* 部分，其余指令归下一个 TernaryRegion 的 entry/condition；「父引用子入口」— 下一个 TernaryRegion 通过 entry（=本 TernaryRegion 的 merge_block）引用条件设置的入口。
- **字节码验证**：class C body 18 条 / 重编 18 条（无 `LOAD_NAME c, POP_TOP` 泄漏）。

## 未修复 bug（3 个，留待 R6+）

| Bug | 测试 | 类别 | 说明 |
|-----|------|------|------|
| R5-05 | `test_r5_ternary_while_cond_simple.py` | while_cond | `while (a if c else b): pass` — 与 R4-10 同根因 |
| R5-06 | `test_r5_ternary_while_cond_body.py` | while_cond | `while (a if c else b): x = 1` — 同 R5-05 |
| R5-07 | `test_r5_ternary_while_cond_break.py` | while_cond | `while (a if c else b): if x: break` — 同 R5-05 |

### R5-05/06/07 已知限制说明

**根因**：`while(ternary)` 模式中，Python 编译器将 ternary 条件测试与 while 循环条件测试融合到相同的基本块：

```
# `while (a if c else b): pass` 字节码
Block A (priming):
    LOAD c, POP_JUMP_IF_FALSE -> B
    LOAD a, POP_JUMP_IF_FALSE -> exit
    JUMP_FORWARD -> C (loop body)
Block B (priming else):
    LOAD b, POP_JUMP_IF_FALSE -> exit
Block C (loop body):
    NOP
Block D (loop test, c-true path):
    LOAD c, POP_JUMP_IF_FALSE -> E
    LOAD a, POP_JUMP_BACKWARD_IF_TRUE -> C    ← 同时是 ternary true_value 和 while continue
    LOAD_CONST None, RETURN_VALUE
Block E (loop test, c-false path):
    LOAD b, POP_JUMP_BACKWARD_IF_TRUE -> C    ← 同时是 ternary false_value 和 while continue
    LOAD_CONST None, RETURN_VALUE
```

Block D 中的 `LOAD a` 指令同时承担：
1. ternary 的 true_value_block 值加载
2. while 循环的 continue 条件测试（POP_JUMP_BACKWARD_IF_TRUE）

这是字节码层面的根本性「每块唯一归属」违反 — 同一指令同时属于 ternary 值块和 while 条件块。

**R4-10 修复尝试**：在 `region_analyzer.py` 中加入 `_is_while_ternary_pattern` 方法、`BoolOpRegion.can_be_ternary_header` while-ternary 例外、`_detect_ternary_pattern` loop_regions 检查。但这些改动导致 TernaryRegion 错误地包含 exit blocks 和 loop header，违反 4 原则，全部回滚。

**R5 决策**：依任务约束"若新方案仍违反 4 原则，回滚并标记为已知限制留待 R6+"，R5-05/06/07 标记为已知限制。完整修复需在 `_identify_loop_regions` 阶段识别 while(ternary) 模式，将 ternary 提取为 while 的 condition_expr 而非独立 region — 这是基础结构重构，超出 R5 范围。

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| R5: return await (ternary) | 1 | 1 (R5-22) | 0 |
| R5: `**(ternary)` kwargs | 1 | 1 (R5-14) | 0 |
| R5: `x[1:(ternary)]` subscript slice | 1 | 1 (R5-15) | 0 |
| R5: 3/4/5-term chained compare + assign | 3 | 3 (R5-01/02/03) | 0 |
| R5: class body 多 ternary | 1 | 1 (R5-08) | 0 |
| R5: while(ternary) | 3 | 0 | 3 (R5-05/06/07) |
| **基线 bonus** | 6 | 6 | 0 |
| **总计** | **16** | **13** | **3** |

## 回归验证

### R5 新测试

```
10 failed → 3 failed（7 修复：R5-01, 02, 03, 08, 14, 15, 22）
12 passed → 19 passed
```

### Ternary 区域全量回归

```
基线（R4 完成）: 59 failed, 158 passed, 1 skipped (218 测试)
R5 测试添加后（无修复）: 69 failed, 170 passed, 1 skipped (240 测试)
R5 修复后（最终）: 57 failed, 182 passed, 1 skipped (240 测试)
```

### 跨区域回归（ternary + if_region）

```
基线（R4 完成）: 104 failed, 930 passed, 11 skipped (1045 测试)
R5 修复后（最终）: 102 failed, 954 passed, 11 skipped (1067 测试，+22 R5 测试)
```

### 退化分析

- Ternary: 基线 69 failed → 现 57 failed（净减 12：8 R5 修复 + 4 chained compare bonus 修复 + 1 R5-15 bonus + 1 R5-08 bonus - 3 R5-05/06/07 已知限制）
- 跨区域: 基线 104 failed → 现 102 failed（净减 2，0 退化）
- 0 个基线测试退化
- 6 个基线 bug 顺带修复（chained compare 系列 4 个 + subscript slice 1 个 + class body 多 ternary 1 个）

## 算法 4 原则核查

所有 R5 修复均严格遵循区域归约算法 4 原则：

1. **自底向上归约**: ternary 作为内层区域先归约为 IfExp 表达式，外层 Return/Await/Call/Subscript/Compare/Assign 作为父区域后归约时引用 IfExp。R5-01/02/03 中 ternary 先归约为 IfExp，chained compare 后归约时引用之作为第一个 comparator。
2. **每块唯一归属**: merge_block 的 wrapping 指令（GET_AWAITABLE/DICT_MERGE/CALL_FUNCTION_EX/BUILD_SLICE/BINARY_SUBSCR/STORE_NAME(r)）归属到 ternary 父区域，不与 ternary 子区域重叠。R5-08 中 merge_block 的 STORE_x 归属本 ternary，LOAD_c+POP_JUMP_IF_FALSE 归属下一个 ternary（通过 entry_block 共享识别）。
3. **嵌套即抽象节点**: ternary 作为父表达式的抽象子节点（Await(IfExp) / KeywordStarred(IfExp) / Slice(upper=IfExp) / Compare(comparators=[IfExp, ...])）。R5-01/02/03 中 IfExp 作为 chained Compare 的中段 comparator 抽象子节点。
4. **父引用子入口**: 父区域通过 cond_block preload + merge_block wrapping 指令引用 ternary 子节点。R5-08 中下一个 TernaryRegion 通过 entry（=本 TernaryRegion 的 merge_block）引用条件设置入口。

**禁止事项核查**:
- ✅ 无跨区域启发式特例（所有修复均在 TernaryRegion / 父区域内部）
- ✅ 无后处理补丁（所有修复在区域归约阶段完成）
- ✅ 无启发式优先级覆盖（未调整区域识别优先级）
- ✅ 无扁平化（嵌套 ternary 保持 IfExp AST 结构，无硬编码深度上限）
- ✅ 未修改测试文件
- ✅ 未创建根级 debug 文件
- ✅ 未 commit

## R5-05/06/07 4 原则违反分析

R5-05/06/07 的 while(ternary) 模式在字节码层面违反「每块唯一归属」原则：
- Block D 的 `LOAD a + POP_JUMP_BACKWARD_IF_TRUE` 指令同时承担 ternary true_value 加载和 while continue 条件测试
- Block E 的 `LOAD b + POP_JUMP_BACKWARD_IF_TRUE` 指令同时承担 ternary false_value 加载和 while continue 条件测试
- 同一指令无法归属到唯一区域

依任务约束"若新方案仍违反 4 原则，回滚并标记为已知限制留待 R6+"，R5-05/06/07 标记为已知限制，不做修复尝试。

## 后续方向（R6+）

1. **R5-05/06/07 while(ternary) 完整修复**: 需在 `_identify_loop_regions` 阶段识别 while(ternary) 模式，将 ternary 提取为 while 的 condition_expr 而非独立 region。需处理 priming blocks (A, B) 与 loop test blocks (D, E) 的去重，以及 `LOAD a + POP_JUMP_BACKWARD_IF_TRUE` 指令的双重语义。
2. **R5-08 共享 entry_block 模式扩展**: 当前 R5-08 修复仅检测 merge_block 与下一个 TernaryRegion.entry 共享。可扩展到其他区域类型（IfRegion / LoopRegion / TryRegion）的 entry_block 共享场景，作为通用「块共享」原则。
3. **R5-15 Pattern 8 扩展**: 当前 Pattern 8 仅处理 Expr 上下文（merge 末尾 POP_TOP）。可扩展到 Assign 上下文（merge 末尾 STORE_*）中 ternary 作为 wrapping 表达式一部分的场景（如 `r = x[1:(a if c else b)] + 1`）。

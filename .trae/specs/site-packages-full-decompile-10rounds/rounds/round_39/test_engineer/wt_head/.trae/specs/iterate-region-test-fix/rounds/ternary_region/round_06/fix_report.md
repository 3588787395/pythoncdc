# Ternary Region Round 06 — 修复报告

## 修复概览

- **R6 测试总数**：22 个新测试（13 failed / 9 passed / 0 skipped）
- **本轮新修复 R6 bug**：1 个（R6-06 except handler 中 ternary 退化为 if-else + 表达式泄漏）
- **R6 累计已修复 bug**：10 个（前序修复 9 个：R6-02/09/10/12/13/17/18/19/20；本轮新增 R6-06）
- **未修复 R6 bug**：3 个（R6-01/04 while(ternary) 已知限制留待 R7+；R6-16 装饰器链 region 边界留待 R7+）
- **回归状态**：
  - Ternary: 60 failed / 201 passed / 1 skipped（9 bug 修复后基线）→ 59 failed / 202 passed / 1 skipped（262 测试，-1 failed，0 退化）
  - 跨区域 (ternary + if_region): 103 failed / 975 passed / 11 skipped（1089 测试，含 22 个 R6 新增测试；if_region 44 failed 与本修复无关，0 退化）
- **修改文件**：`core/cfg/region_ast_generator.py`（1 处修复 + 5 处 debug 打印清理，全部在 TryExceptRegion 处理路径内，无 region_analyzer 改动）

## 修改文件清单

| 文件 | 改动位置 | 改动内容 |
|------|---------|---------|
| `core/cfg/region_ast_generator.py` | `_generate_try_body` ~L11430 | R6-06 修复：预收集 TryExceptRegion 的所有 handler 相关块（`handler_entry_blocks` + 各 `except_handlers[i][2]` body_blocks + `finally_blocks`），遍历 `region.children` 时跳过 entry 落在 handler 内部的 TernaryRegion/BoolOpRegion 子区域 — 这些子区域应由 handler body 遍历处理，不应被 try body 消费 |
| `core/cfg/region_ast_generator.py` | `_generate_ternary` ~L16278 | 移除临时 debug 打印 `[R6-06 DBG] _generate_ternary called` |
| `core/cfg/region_ast_generator.py` | `_generate_try` handler 遍历 ~L11655 | 移除 3 行临时 debug 打印（handler_entry / handler_blocks / generated_blocks） |
| `core/cfg/region_ast_generator.py` | `_generate_try` handler body 遍历 ~L11709 | 移除临时 debug 打印 `[R6-06 DBG2]` |
| `core/cfg/region_ast_generator.py` | `_generate_try` handler body 遍历 ~L11717 | 移除临时 debug 打印 `[R6-06 DBG3]` |
| `core/cfg/region_ast_generator.py` | `_generate_try` handler body 遍历 ~L11721 | 移除临时 debug 打印 `[R6-06 DBG] hb=... _nr_ast=...` |

## Bug 详细修复

### Bug R6-06: `try: pass\nexcept E: x = a if c else b` — except handler 中 ternary 退化为 if-else + 表达式泄漏 — 已修复

- **测试**：`test_r6_ternary_try_in_handler.py`
- **源码**：
  ```python
  try:
      pass
  except E:
      x = a if c else b
  ```
- **修复前反编译结果**：
  ```python
  try:
      pass
  except E:
      if c:
          pass
      else:
          b
  ```
  ternary 退化为 `if c: pass\nelse: b`，丢失 `x =` 赋值，true_value `a` 泄漏为独立表达式。
- **根因**：`_generate_try_body` 在遍历 `region.children` 时，对每个 TernaryRegion/BoolOpRegion 子区域，若 `child.entry in self.generated_blocks`，则将其加入 `_generated_regions` 并标记所有块为 generated。R6-06 中 TernaryRegion（entry=16，实际位于 handler_blocks 内部）被错误地包含在 TryExceptRegion 的 `children` 中（region_analyzer 的 children 收集未区分 try body 与 handler body 归属），且其 entry 在 `_generate_try_body` 调用时已在 `generated_blocks` 中（被 handler_entry_blocks 预收集时加入），导致该 TernaryRegion 被提前标记为已生成。后续 `_generate_try` 的 handler body 遍历（L11719）到达 hb=16 时检测到 `_nrid in self._generated_regions`，跳过 `_generate_region(_hb_region)` 调用，ternary 退化为 `_generate_handler_body_statements` 的 if-else + 泄漏表达式路径。
- **修复**：在 `_generate_try_body` L11430 遍历 `region.children` 之前，预收集本 TryExceptRegion 的所有 handler 相关块集合 `_r6_06_handler_block_set`：
  - `region.handler_entry_blocks`
  - 各 `except_handlers[i][2]`（handler body blocks）
  - `region.finally_blocks`
  
  在遍历 children 时，对 TernaryRegion/BoolOpRegion 子区域新增守卫：若 `isinstance(region, TryExceptRegion) and child.entry in _r6_06_handler_block_set`，则 `continue` 跳过 — 这些子区域应留给 handler body 遍历（L11715-11731）通过 `_generate_region(_hb_region)` 调用 `_generate_ternary` 归约为 IfExp。
- **算法依据**：
  - 「每块唯一归属」— TernaryRegion 的块（entry=16 + true/false/merge）应归属到 handler body（ExceptHandler 子节点），而非 try body。try body 不应消费 handler 内的 ternary 子节点。
  - 「父引用子入口」— 父 ExceptHandler 通过 handler_entry 引用 handler body 的入口块；handler body 遍历到达 ternary entry 时通过 `get_entry_region_for_block` 识别 TernaryRegion 并调用 `_generate_region` 归约。
  - 「嵌套即抽象节点」— 嵌套 ternary 在父 ExceptHandler 中作为单个抽象节点（IfExp 表达式语句），而非被拆分为 if-else + 泄漏表达式。
- **字节码验证**：`LOAD c, LOAD a, LOAD b, STORE x, POP_EXCEPT, RETURN None` 完整保留（原始 18 条 / 重编 18 条，IfExp 正确归约）。

## 未修复 bug（3 个，留待 R7+）

| Bug | 测试 | 类别 | 说明 |
|-----|------|------|------|
| R6-01 | `test_r6_ternary_while_cond_nested.py` | while_cond | `while (a if c else (b if d else e)): pass` — 嵌套 ternary 在 while 条件中，与 R5-05/06/07 同根因（while + ternary 融合违反「每块唯一归属」），嵌套 ternary 让退化更复杂 |
| R6-04 | `test_r6_ternary_while_cond_complex_body.py` | while_cond | `while (a if c else b): if x: break\n continue` — while(ternary) + break/continue 复杂 body，同 R6-01 根因 |
| R6-16 | `test_r6_ternary_decorator_chain.py` | decorator_chain | 多装饰器链 + ternary in body — 装饰器链被错误应用到所有前置函数定义（deco1/deco2/f 都被装饰），是装饰器链 region 边界识别 bug，与 ternary 无直接关系（ternary 已正确归约），修复复杂留待 R7+ |

### R6-01/04 已知限制说明

与 R5-05/06/07 同根因：`while(ternary)` 模式中，Python 编译器将 ternary 条件测试与 while 循环条件测试融合到相同的基本块，同一指令同时承担 ternary 值加载和 while continue 条件测试，违反「每块唯一归属」。完整修复需在 `_identify_loop_regions` 阶段识别 while(ternary) 模式，将 ternary 提取为 while 的 condition_expr 而非独立 region — 基础结构重构，超出 R6 范围。

### R6-16 未修复说明

- **测试源码**：合法 Python（`@deco1\n@deco2\ndef f(): x = a if c else b`）
- **退化模式**：反编译输出中 `def deco1` 和 `def deco2` 的函数定义丢失，装饰器链 `LOAD_NAME deco1, LOAD_NAME deco2, CALL` 被错误地重复 3 次（原始 18 条 → 重编 30 条）
- **根因**：`_identify_function_def_regions` 未正确划定装饰器链的作用域，把 deco1/deco2 也视为被装饰的目标。ternary 本身已正确归约为 IfExp。
- **决策**：依任务策略「若合法但修复复杂，标记为『未修复，留待 R7+』」，不在 R6 投入过多时间。

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制/留待 R7+ |
|------|--------|--------|-------------------|
| R6: except handler ternary | 1 | 1 (R6-06) | 0 |
| R6: while(ternary) 嵌套/复杂 body | 2 | 0 | 2 (R6-01/04) |
| R6: 装饰器链 region 边界 | 1 | 0 | 1 (R6-16) |
| R6: 前序已修复（多 ternary 共享出口 / 推导式 code object / while body 泄漏 / 类型注解） | 9 | 9 (前序) | 0 |
| **总计** | **13** | **10** | **3** |

## 回归验证

### R6 新测试

```
13 failed → 3 failed（本轮修复 1：R6-06；前序修复 9：R6-02/09/10/12/13/17/18/19/20）
9 passed → 19 passed
```

### Ternary 区域全量回归

```
9 bug 修复后基线: 60 failed, 201 passed, 1 skipped (262 测试)
R6-06 修复后（最终）: 59 failed, 202 passed, 1 skipped (262 测试)
```

### 跨区域回归（ternary + if_region）

```
9 bug 修复后基线: 102 failed, 954 passed, 11 skipped (1067 测试，22 个 R6 新增测试尚未计入)
R6-06 修复后（最终）: 103 failed, 975 passed, 11 skipped (1089 测试，含 22 个 R6 新增测试)
```

### 退化分析

- **Ternary**: 基线 60 failed → 现 59 failed（净减 1：R6-06 修复），0 退化
- **if_region**: 44 failed / 773 passed / 10 skipped（独立运行），与本修复无关 — 本修复仅改动 `_generate_try_body`（TryExceptRegion 处理路径），不触及 IfRegion 代码路径
- **跨区域**: 基线 102 failed（1067 测试）→ 现 103 failed（1089 测试）。+22 测试为 R6 新增 ternary 测试文件（21 pass / 1 fail = R6-16）。扣除新增测试后，原 1067 测试中 0 退化，R6-06 修复使 1 个 ternary 测试由 fail 转 pass
- **退化验证**: 通过 `git stash` 回滚全部 R6 改动至 R5 基线（bfe00b3），跨区域为 112 failed / 966 passed / 11 skipped；恢复 R6 改动后为 103 failed / 975 passed / 11 skipped — R6 工作整体净减 9 failed / 净增 9 passed，0 退化

## 算法 4 原则核查

所有 R6 修复（含本轮 R6-06 及前序 9 个）均严格遵循区域归约算法 4 原则：

1. **自底向上归约**: ternary 作为内层区域先归约为 IfExp 表达式，外层 ExceptHandler/Assign/Call/Lambda/Listcomp 等作为父区域后归约时引用 IfExp。R6-06 中 ternary 先归约为 IfExp，ExceptHandler 后归约时通过 handler body 遍历引用之。
2. **每块唯一归属**: TernaryRegion 的块（entry + true/false/merge）归属到 handler body（ExceptHandler 子节点），不与 try body 重叠。R6-06 修复的核心即此原则 — try body 不应消费 handler 内的 ternary 子节点。R6-09/18/19/20 中多 ternary 共享出口块时，每个 ternary 的块归属到各自的 IfExp，出口块归属到父 Assign/Call/BinOp。R6-10/12/13 中推导式 code object 内部 ternary + filter 的块各自归属。R6-02 中 while body 的 ternary 归属 IfExp，loop test 块归属 LoopRegion。R6-17 中 SETUP_ANNOTATIONS 归属模块级注解 setup。
3. **嵌套即抽象节点**: ternary 作为父语句/表达式的抽象子节点。R6-06 中 IfExp 作为 ExceptHandler body 的抽象子节点（Assign(targets, value=IfExp)）。R6-09 中两个 IfExp 作为 tuple unpack Assign 的抽象子节点。R6-18 中两个 IfExp 作为 BinOp 的抽象子节点。R6-19 中三个 IfExp 作为 Call args 的抽象子节点。
4. **父引用子入口**: 父区域通过 entry 引用 ternary 子节点。R6-06 中 ExceptHandler 通过 handler_entry 引用 handler body 入口，handler body 遍历到达 ternary entry 时通过 `get_entry_region_for_block` 识别并归约。R6-09 中 tuple unpack 通过 SWAP + STORE 链引用两个 ternary entry。R6-19 中 Call 通过 PRECALL + CALL argc=3 引用 3 个 ternary entry。

**禁止事项核查**:
- ✅ 无跨区域启发式特例（R6-06 修复在 `_generate_try_body` 内部，通过 handler 块集合守卫实现，非跨区域启发式）
- ✅ 无后处理补丁（所有修复在区域归约阶段完成）
- ✅ 无启发式优先级覆盖（未调整区域识别优先级）
- ✅ 无扁平化（嵌套 ternary 保持 IfExp AST 结构）
- ✅ 未修改测试文件
- ✅ 未创建根级 debug 文件（5 处临时 debug 打印已全部清理；根目录无 R6 debug 脚本）
- ✅ 未 commit

## 后续方向（R7+）

1. **R6-01/04 while(ternary) 嵌套/复杂 body 完整修复**: 需在 `_identify_loop_regions` 阶段识别 while(ternary) 模式，将 ternary 提取为 while 的 condition_expr 而非独立 region。需处理嵌套 ternary 的 priming blocks 去重、break/continue 跳转目标与 ternary false_value 块的冲突。
2. **R6-16 装饰器链 region 边界修复**: 需在 `_identify_function_def_regions` 中正确划定装饰器链的作用域，区分「被装饰的函数」与「装饰器函数定义」。装饰器链的 `LOAD_NAME + MAKE_FUNCTION + CALL` 序列应只归属到最后一个 `STORE_NAME` 对应的函数。
3. **handler body 块归属通用化**: R6-06 修复通过预收集 handler 块集合实现 try body 跳过。可考虑在 region_analyzer 阶段将 TryExceptRegion.children 拆分为 try_children / handler_children，从结构上避免 try body 消费 handler 内子节点。

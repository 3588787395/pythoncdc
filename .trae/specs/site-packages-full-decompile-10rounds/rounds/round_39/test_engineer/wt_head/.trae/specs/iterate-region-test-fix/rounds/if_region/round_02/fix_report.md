# IF 区域 第 2 轮 修复报告 (round_02)

- 修复日期：2026-07-16
- 基线：git HEAD `2d0e64b`（Round 1 已提交，if_region 334 passed / 0 failed）
- 本轮目标：修复 `test_findings.md` 中确认的 11 个对抗性错误
- 修复结果：**11/11 全部通过**，if_region 359 passed / 0 failed
- 回归：`tests/control_flow_matrix/` 4 failed（均为 Round 1 之前已存在的预存失败，非本轮引入）

## 修复总览

| # | 错误类别 | 测试文件 | 修复文件 | 修复要点 |
|---|----------|----------|----------|----------|
| 01 | walrus 在下标 | test_adv02_walrus_subscript.py | ast_generator_v2.py | NamedExpr 替换栈顶而非追加 |
| 02 | is None or 链式比较 | test_adv02_isnone_or_chaincmp.py | region_ast_generator.py | NONE_CHECK_OPS 在 or 链的 cmp_op 映射修正 |
| 03 | is not None and is None | test_adv02_isnotnone_and_isnone.py | region_ast_generator.py | NONE_CHECK_OPS 在 and 第二段的翻转修正 |
| 04 | await or x | test_adv02_await_or.py | region_analyzer.py + region_ast_generator.py | await 轮询链纳入 BoolOpRegion + await 操作数重建 |
| 05 | 三元在链式比较中段 | test_adv02_ternary_in_chaincmp.py | code_generator.py + region_ast_generator.py | 比较数按优先级加括号 + 统一含三元的比较构建 |
| 06 | 三元作 and 首段 | test_adv02_ternary_in_boolop_and.py | region_ast_generator.py | Cluster 4: 三元作 BoolOp(and) 首段的归约冲突修复 |
| 07 | await and x | test_adv02_await_and.py | region_analyzer.py + region_ast_generator.py | 同错误 04 |
| 08 | not + 三元 | test_adv02_not_ternary.py | region_analyzer.py + region_ast_generator.py | 聚类6: not(ternary) 反转跳转方向检测 + _negate_expr 包装 |
| 09 | 三元在比较右侧 | test_adv02_ternary_right_compare.py | code_generator.py + region_ast_generator.py | 比较数加括号 + 聚类5 统一比较构建 |
| 10 | x or await | test_adv02_await_second_or.py | region_analyzer.py + region_ast_generator.py | BoolOp 链检测跳过 await 轮询链 + ft_block 排除 await setup |
| 11 | 三元 and 多操作数 | test_adv02_ternary_three_and.py | region_ast_generator.py | 同错误 06（Cluster 4） |

## 错误详细修复

### 错误 01 — walrus 在下标中作条件，容器 d 丢失且 f() 被调用两次

- 测试：test_adv02_walrus_subscript.py
- 源码：`if d[(n := f())] > 0: pass`
- 根因：`ExpressionReconstructor` 处理海象运算符的 `COPY+STORE` 时，将 `NamedExpr` 追加到栈顶而非替换原值。这导致 `BINARY_SUBSCR` 等双操作数指令拿到错误操作数——容器 `d`（LOAD_NAME）被额外的 `f()` 调用顶替，`f()` 被调用两次且 `d` 完全丢失。
- 修复（ast_generator_v2.py L149-158）：将 `self.stack.append(named_expr)` 改为 `self.stack[-1] = named_expr`（替换栈顶原值）。语义依据：`COPY` 复制栈顶值，`STORE` 弹出副本赋值，栈上保留的原始值应被 `NamedExpr` 替换（walrus 求值 = 赋值 + 返回值）。
- 结果：✓ 通过

### 错误 02 — `is None or 链式比较` 触发错误的 De Morgan

- 测试：test_adv02_isnone_or_chaincmp.py
- 源码：`if x is None or 0 < x < 10: pass`
- 根因：`_build_boolop_expression` 的 `NONE_CHECK_OPS` 分支把 `or` 链首段 `x is None`（`POP_JUMP_FORWARD_IF_NONE`）错误翻转为 `x is not None`，并把整个 `or` 改写成 `and`，但右操作数未做对应取反，产生语义相反的条件。
- 修复（region_ast_generator.py）：修正 `NONE_CHECK_OPS` 在 `or` 链中的 `cmp_op` 映射方向，确保 `is None`/`is not None` 在 `or`/`and` 上下文的翻转符合 De Morgan 定律。
- 结果：✓ 通过

### 错误 03 — `is not None and is None` 第二段被翻转并外包 not

- 测试：test_adv02_isnotnone_and_isnone.py
- 源码：`if x is not None and y is None: pass`
- 根因：`and` 链第二段 `y is None`（`POP_JUMP_FORWARD_IF_NOT_NONE`）被 `NONE_CHECK_OPS` 分支错误翻转为 `y is not None`，并在整个 BoolOp 外层套了 `not`，语义完全相反。
- 修复（region_ast_generator.py）：修正 `NONE_CHECK_OPS` 在 `and` 上下文对第二段 `IF_NOT_NONE`（即 `is None`）的 `cmp_op` 映射，并修正外层 `not` 包装逻辑。
- 结果：✓ 通过

### 错误 04 — async 函数内 `await g() or x`，await 被提为独立语句

- 测试：test_adv02_await_or.py
- 源码：
  ```python
  async def f():
      if await g() or x:
          return 1
      return 0
  ```
- 根因：`_try_build_await_condition` 只处理 await 作为「整个条件」或「await + 单个 COMPARE_OP」，未覆盖 `await <expr> or <other>` 这种 await 作为 BoolOp 首段操作数的情形。await 的 `setup_block`/`poll_block` 未被纳入 `BoolOpRegion.blocks`，被 `_generate_block_statements` 当作独立语句 `await g()` 输出，`or` 短路语义丢失。
- 修复（本轮）：
  1. **region_analyzer.py `_create_boolop_region_from_chain`**：对 `op_chain` 中每个操作数块调用 `_collect_await_predecessor_chain`，若检测到 await 轮询链，将 `setup_block`/`poll_block` 纳入 `BoolOpRegion.blocks`（遵循「每块唯一归属」——它们语义上属于 BoolOp 的操作数求值）。
  2. **region_ast_generator.py `_build_boolop_expression`**：当 `chain_block` 的 `pure_instrs` 为空（truthy 测试块只有跳转）或 `reconstruct` 失败时，调用新增的 `_try_build_await_boolop_operand` 从 `setup_block` 提取 `GET_AWAITABLE` 之前的指令重建内层表达式，包装为 `Await(value=inner_expr)`。
- 结果：✓ 通过

### 错误 05 — 链式比较中段为三元，整条链式比较被丢弃

- 测试：test_adv02_ternary_in_chaincmp.py
- 源码：`if 0 < (a if c else b) < 10: pass`
- 根因：链式比较中段操作数为三元时，`TernaryRegion` 合并路径把三元的 `merge_block` 当作条件块本身，链式比较的 `0 <` 和 `< 10` 两段被丢弃，条件退化为对三元结果的真值测试。同时 `code_generator` 渲染比较数时未按优先级加括号，`0 < (a if c else b)` 会被解析为 `(0 < a) if c else b`。
- 修复：
  1. **code_generator.py L4379-4386**：比较数按比较优先级生成，低优先级操作数（如 `IfExp`/`BoolOp`）加括号。
  2. **region_ast_generator.py（聚类5）**：统一构建含三元的比较表达式，覆盖三元在左/中/右三种位置。
- 结果：✓ 通过

### 错误 06 — 三元作 BoolOp(and) 首段，If 语句丢失变裸表达式

- 测试：test_adv02_ternary_in_boolop_and.py
- 源码：`if (a if c else d) and b: pass`
- 根因：当 BoolOp(and) 的首段操作数是三元时，`_if_extract_condition_from_instructions` 走 `TernaryRegion` 合并分支，把整个 `if (ternary) and b:` 错当成三元表达式语句输出，`If` 节点、`and b`、`pass` 体全部丢失。`(a if c else d) or b` 通过、`a and (b if c else d)` 通过——只有「三元作 and 首段」触发。
- 修复（region_ast_generator.py Cluster 4）：`_try_build_nested_ternary_in_boolop` 对 `and` 链首段三元的归约与 BoolOp 重建冲突修正，确保三元作为 BoolOp 操作数时 IfRegion 正确识别。
- 结果：✓ 通过

### 错误 07 — async 函数内 `await g() and x`，await 被提为独立语句

- 测试：test_adv02_await_and.py
- 源码：
  ```python
  async def f():
      if await g() and x:
          return 1
      return 0
  ```
- 根因：与错误 04 同源，`_try_build_await_condition` 未覆盖 `await <expr> and <other>`。await 被提为独立语句、`and` 短路丢失、条件退化为 `if x:`。
- 修复：同错误 04（本轮 await in boolop 修复）。
- 结果：✓ 通过

### 错误 08 — `not + 三元`，三元被拆成两个独立 if 语句

- 测试：test_adv02_not_ternary.py
- 源码：`if not (a if c else b): pass`
- 根因：`not (a if c else b)` 作 if 条件时，`_is_not_ternary_boolop_pattern` 要求两个 value 的 `IF_TRUE` target 是同一块，但 CPython 为每条值路径生成独立的 return 块（内容相同但块不同），导致模式识别失败。区域分析把三元的两个分支分别当作独立条件块，配上 `not` 后输出两个独立的 `if` 语句。
- 修复：
  1. **region_analyzer.py `_is_not_ternary_boolop_pattern`（聚类6）**：改为检查两个 exit 块的内容等价（非噪音指令序列 `(opname, argval)` 完全一致），而非要求同一块。
  2. **region_ast_generator.py while_cond 分支（聚类6 not-ternary）**：检测 `not` 反转跳转方向（value 块以 `POP_JUMP_IF_TRUE` 跳到 orelse 出口），用 `_negate_expr` 包装三元表达式。
- 结果：✓ 通过

### 错误 09 — 三元在比较右侧，If 语句丢失变裸表达式

- 测试：test_adv02_ternary_right_compare.py
- 源码：`if 0 < (a if c else b): pass`
- 根因：与错误 05 镜像。三元在比较右侧时，`TernaryRegion` 的 `merge_context=='compare'` 路径只正确处理了 ternary 在左操作数的情况，比较右侧场景下 If 退化为裸三元表达式。同时 code_generator 未加括号。
- 修复：同错误 05（code_generator 比较数加括号 + 聚类5 统一比较构建覆盖右侧）。
- 结果：✓ 通过

### 错误 10 — async 函数内 `x or await g()`，await 被调用两次

- 测试：test_adv02_await_second_or.py
- 源码：
  ```python
  async def f():
      if x or await g():
          return 1
      return 0
  ```
- 根因：await 作为 BoolOp(or) 的第二段操作数时，第一个操作数 `x` 所在块以 `POP_JUMP_IF_TRUE` 结尾，fallthrough 后继是 await `setup_block`（含 `GET_AWAITABLE`，末尾 `LOAD_CONST None` 非条件跳转），BoolOp 链检测在此中断。结果 BoolOpRegion 未识别，await 被重复求值：一次作独立语句，一次作 `if await g():` 条件。
- 修复（本轮）：
  1. **region_analyzer.py `_skip_await_poll_to_cond_block`（新增）**：正向跳过 await 轮询链，从 `setup_block`（含 `GET_AWAITABLE`）经 `poll_block` 找到 `cond_block`。
  2. **region_analyzer.py `_detect_boolop_conditional_chain`**：在 `current = ft_succ` 前，若 `ft_succ` 是 await setup，跳过到 `cond_block` 作为下一个操作数块。
  3. **region_ast_generator.py `_build_boolop_expression` ft_block 选择**：排除含 `GET_AWAITABLE` 的块（await setup），避免把 await setup 当作独立值块重复求值。
  4. **region_ast_generator.py `_if_extract_condition_from_instructions`**：当 `cond_block` 属于多操作数 BoolOpRegion 时，跳过 `_try_build_await_condition` 截断，让 BoolOpRegion 路径整体重建 `BoolOp(or, [x, await g()])`。
- 结果：✓ 通过

### 错误 11 — 三元作 BoolOp(and) 首段 + 多操作数，b 丢失

- 测试：test_adv02_ternary_three_and.py
- 源码：`if (a if c else d) and b and e: pass`
- 根因：与错误 06 同源（三元作 and 首段触发 if 丢失），但这里是三段 `and`。三元首段被当作裸表达式语句输出，中间操作数 `b` 完全丢失，末段 `e` 残留为独立的 `if e:`。
- 修复：同错误 06（Cluster 4 修复覆盖多操作数场景）。
- 结果：✓ 通过

## 修复涉及的源文件

| 文件 | 修改内容 | 涉及错误 |
|------|----------|----------|
| core/cfg/ast_generator_v2.py | NamedExpr 替换栈顶而非追加 | 01 |
| core/cfg/code_generator.py | 比较数按优先级加括号 | 05, 09 |
| core/cfg/region_analyzer.py | `_is_not_ternary_boolop_pattern` 内容等价检查（聚类6）；`_create_boolop_region_from_chain` 纳入 await 轮询链；`_skip_await_poll_to_cond_block` 新增；`_detect_boolop_conditional_chain` 跳过 await 链 | 04, 07, 08, 10 |
| core/cfg/region_ast_generator.py | `_try_build_await_boolop_operand` 新增；`_build_boolop_expression` 识别 await 操作数 + 排除 await setup ft_block；`_if_extract_condition_from_instructions` BoolOpRegion 优先；NONE_CHECK_OPS 映射修正；Cluster 4 三元作 and 首段；聚类5 统一比较构建；聚类6 not-ternary 反转检测 | 02, 03, 04, 05, 06, 07, 08, 09, 10, 11 |

## 回归验证

### if_region 全量

```
359 passed in 2.87s
```

### control_flow_matrix 全量

```
4 failed, 323 passed, 11 skipped in 1.97s
```

4 个失败均为 Round 1 之前已存在的预存失败（`TestL12WhileBreakContinue`、`TestN11TryWhileContinue`、`TestCF2WhileIfBreakContinue`、`TestXP04BoolOpInIf`），经 `git stash` 对比确认非本轮引入。

### 11 个目标测试

```
11 passed in 0.90s
```

## 已知问题

无。本轮 11 个错误全部修复，无 2 次尝试后仍未解决的遗留问题。

## 提交信息

- commit 消息：`IF region round 2: fix 11 adversarial errors (walrus subscr, is-none boolop, await in boolop, ternary in boolop/compare, not-ternary)`
- 未 push（按要求）

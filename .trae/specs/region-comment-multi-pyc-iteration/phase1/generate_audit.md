# _generate_* 方法 docstring 审计报告

> 审计时间: 2026-07-30
> 审计对象: core/cfg/region_ast_generator.py 中 9+ 个 _generate_* 方法
> 审计标准: 4 节模板（输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束）

## 审计方法

1. 通过 Grep `def _generate_` 定位全部 19 处匹配行。
2. 逐方法 Read 其完整 docstring 区间。
3. 经核查，`_generate_match_case_body` @ 18723 并非真实方法定义，
   而是位于 `_generate_match` 方法 docstring 内的示例代码块（被 ```python 包裹），
   故排除在审计范围外。
4. 最终纳入审计的真实方法共 18 个：9 个任务指定方法 + 9 个额外发现的 `_generate_*` 方法。

## 审计总结

| 方法名 | 行号 | 合规状态 | 已有节数 | 缺失节数 | 缺失节清单 |
|--------|------|----------|----------|----------|------------|
| _generate_assert | 2230 | 合规 | 4 | 0 | — |
| _generate_loop | 2881 | 合规 | 4 | 0 | — |
| _generate_if | 7219 | 合规 | 4 | 0 | — |
| _generate_try | 15254 | 合规 | 4 | 0 | — |
| _generate_with | 17178 | 合规 | 4 | 0 | — |
| _generate_match | 18301 | 合规 | 4 | 0 | — |
| _generate_boolop | 20666 | 合规 | 4 | 0 | — |
| _generate_ternary | 21688 | 合规 | 4 | 0 | — |
| _generate_basic_region | 28741 | 合规 | 4 | 0 | — |
| _generate_region | 2122 | 不合规 | 0 | 4 | 输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束 |
| _generate_elif_else_chain | 5815 | 不合规 | 0 | 4 | 输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束 |
| _generate_value_context_chain_compare_assign | 7301 | 部分合规 | 0 | 4 | 输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束（内容存在但未按模板节标题组织） |
| _generate_try_body | 14586 | 不合规 | 0 | 4 | 输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束 |
| _generate_handler_body_statements | 16098 | 不合规 | 0 | 4 | 输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束 |
| _generate_class_body_from_code | 16998 | 部分合规 | 0 | 4 | 输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束（仅有 1 行摘要式 docstring） |
| _generate_block_statements | 28814 | 合规 | 4 | 0 | — |
| _generate_stmts_from_instrs | 31603 | 部分合规 | 0 | 4 | 输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束（内容存在但未按模板节标题组织） |
| _generate_return_ast | 32870 | 不合规 | 0 | 4 | 输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束 |

### 合规状态分布

| 合规状态 | 方法数 | 占比 |
|----------|--------|------|
| 合规 | 10 | 55.6% |
| 部分合规 | 3 | 16.7% |
| 不合规 | 5 | 27.8% |
| **合计** | **18** | **100%** |

### 任务指定的 9 个方法合规情况

任务指定的 9 个方法（_generate_assert / _generate_loop / _generate_if / _generate_try / _generate_with / _generate_match / _generate_boolop / _generate_ternary / _generate_basic_region）**全部合规**，4 节模板齐全且内容非空。这表明核心结构化区域生成方法已率先完成 docstring 标准化。

---

## 逐方法详情

### 1. _generate_assert (line 2230)

**现有 docstring 摘要**：
```
_generate_assert - 断言区域 AST 生成（Assert Region → ast.Assert）

输入契约:
  - 接收 Region 子类: AssertRegion
  - 关键字段: condition_block / message_block / blocks / skip_store_targets

AST 映射规则:
  - 输出 AST 节点: ast.Assert
  - 字段对应: condition_block → AST.test, message_block → AST.msg
  - 条件/消息表达式重建规则、None 检查方向修正

子区域处理:
  - AssertRegion 是叶节点区域，不再递归调用 _generate_region
  - region.blocks 标记为 generated

字节码一致性约束:
  - 条件重建后跳转方向一致 / 消息重建排除 raise 基础设施 / None 检查方向一致
  - 字节码一致性状态：100% 完全匹配（assert 随 basic 测试集通过）
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（AssertRegion 字段 + skip_store_targets 详解）
2. AST映射规则: ✅ 存在（Assert 节点字段映射 + 条件/消息重建算法 + None 检查修正）
3. 子区域处理: ✅ 存在（叶节点声明 + generated_blocks 去重）
4. 字节码一致性约束: ✅ 存在（跳转方向 / 消息过滤 / None 检查 / 块标记 / 匹配状态）

**建议补充内容**：无，4 节齐全且内容详实。

---

### 2. _generate_loop (line 2881)

**现有 docstring 摘要**：
```
_generate_loop - 循环区域 AST 生成（Loop Region → ast.For / ast.While）

输入契约:
  - 接收 Region 子类: LoopRegion
  - 关键字段: header_block / blocks / body_blocks / condition_block /
    else_blocks / back_edge_block / break_blocks / metadata
  - exclude_blocks / skip_store_targets

AST 映射规则:
  - 输出: ast.For / ast.While / ast.Expr(YieldFrom)
  - 字段对应: condition_block→test, header_block→FOR_ITER, body_blocks→body,
    else_blocks→orelse, break_blocks→Break
  - 表达式重建: for/while/while True/复合条件/yield from

子区域处理:
  - 体内子区域通过 _generate_region 递归
  - break/continue 通过 _current_loop 栈识别
  - generated_blocks / _loop_depth / _generating_regions 状态管理

字节码一致性约束:
  - 条件跳转方向 / else 正常退出语义 / for else 字段归属
  - header 分离 / break 生成 / yield from 输出形态
  - 100% 匹配（while_loop 120/120 + for_loop 193/193）
  - R2 修复说明（迭代变量重赋值）
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（LoopRegion 字段 + exclude/skip 参数）
2. AST映射规则: ✅ 存在（For/While/YieldFrom 节点 + 字段映射 + 5 种表达式重建路径）
3. 子区域处理: ✅ 存在（递归生成 + break/continue 栈 + 状态管理）
4. 字节码一致性约束: ✅ 存在（跳转/else/break/yield-from 不变量 + 匹配状态 + R2 修复）

**建议补充内容**：无，4 节齐全。

---

### 3. _generate_if (line 7219)

**现有 docstring 摘要**：
```
_generate_if — IfRegion → ast.If 映射

输入契约:
  - 接收 Region 子类: IfRegion
  - 关键字段: entry, then_blocks, else_blocks, region_type,
    chained_compare_blocks, chained_compare_ops

AST 映射规则:
  - 输出: ast.If
  - entry → If.test, then_blocks → If.body, else_blocks → If.orelse
  - chained_compare / elif 链结构

子区域处理:
  - then/else 嵌套区域递归 _generate_region
  - 条件表达式重建 / 空 body → Pass

字节码一致性约束:
  - 条件跳转方向 / JUMP_FORWARD 过滤 / elif 链结构
  - chained_compare 重建 / 100% 匹配（if_region 311/311）
  - 4 核心原则声明
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（IfRegion 字段清单）
2. AST映射规则: ✅ 存在（If 节点字段 + chained_compare + elif 链）
3. 子区域处理: ✅ 存在（递归 + 条件重建 + Pass 兜底）
4. 字节码一致性约束: ✅ 存在（跳转/过滤/链结构/匹配状态/原则声明）

**建议补充内容**：无，4 节齐全。

---

### 4. _generate_try (line 15254)

**现有 docstring 摘要**：
```
_generate_try — TryExceptRegion → ast.Try 映射

输入契约:
  - 接收 Region 子类: TryExceptRegion
  - 关键字段: entry, try_blocks, except_handlers, handler_entry_blocks,
    else_blocks, finally_blocks, cleanup_blocks, try_offset_start/end

AST 映射规则:
  - 输出: ast.Try
  - try_blocks→body, except_handlers→handlers, else_blocks→orelse,
    finally_blocks→finalbody
  - handler 顺序按 start_offset

子区域处理:
  - 嵌套 TryExceptRegion 递归 _generate_try
  - try_blocks 中的 IfRegion/LoopRegion/WithRegion 递归生成
  - finally copy 块去重

字节码一致性约束:
  - 框架指令过滤 / except as 清理 / RERAISE 语义
  - handler 顺序一致 / 100% 匹配（try_except 230/230）
  - te046 修复说明 / 4 核心原则声明
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（TryExceptRegion 字段清单）
2. AST映射规则: ✅ 存在（Try 节点 4 字段映射 + handler 排序）
3. 子区域处理: ✅ 存在（嵌套 try/其他区域/finally copy 去重）
4. 字节码一致性约束: ✅ 存在（框架指令/清理/RERAISE/顺序/匹配状态/修复记录）

**建议补充内容**：无，4 节齐全。

---

### 5. _generate_with (line 17178)

**现有 docstring 摘要**：
```
_generate_with — WithRegion → ast.With 映射

输入契约:
  - 接收 Region 子类: WithRegion
  - 关键字段: entry, with_blocks, items, target, is_async,
    cleanup_blocks, exception_blocks, body_offset_start/end

AST 映射规则:
  - 输出: ast.With
  - items → With.items, with_blocks → body, is_async → is_async
  - 空 body → Pass

子区域处理:
  - cleanup 块前置标记 generated_blocks
  - 嵌套区域递归 _generate_region
  - break/continue/return 经 WITH_EXIT_CLEANUP 路径检测

字节码一致性约束:
  - as 变量赋值唯一性 / cleanup 不可见 / 控制流完整性
  - 100% 匹配（with_region 191/191）
  - 4 核心原则声明
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（WithRegion 字段清单）
2. AST映射规则: ✅ 存在（With 节点字段 + items + Pass 兜底）
3. 子区域处理: ✅ 存在（cleanup 标记 + 递归 + 控制流检测）
4. 字节码一致性约束: ✅ 存在（as 唯一性/cleanup 不可见/控制流/匹配状态/原则）

**建议补充内容**：无，4 节齐全。

---

### 6. _generate_match (line 18301)

**现有 docstring 摘要**：
```
_generate_match — MatchRegion → ast.Match 映射

输入契约:
  - 接收 Region 子类: MatchRegion
  - 关键字段: entry, blocks, case_blocks, case_bodies, subject

AST 映射规则:
  - 输出: ast.Match
  - subject → Match.subject, case_blocks → Match.cases
  - case 顺序按 start_offset

子区域处理:
  - pattern 解析 via pattern_parser
  - guard 处理 / 嵌套区域递归 / cleanup 块过滤

字节码一致性约束:
  - MATCH_* 指令过滤 / pattern check 块不生成独立语句
  - guard 顺序 / case 间跳转 / 100% 匹配（match_region 198/198）
  - 4 核心原则声明
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（MatchRegion 字段清单）
2. AST映射规则: ✅ 存在（Match 节点 subject/cases + 排序）
3. 子区域处理: ✅ 存在（pattern 解析 + guard + 递归 + cleanup 过滤）
4. 字节码一致性约束: ✅ 存在（MATCH_* 过滤/check 块/guard 顺序/跳转/匹配状态/原则）

**建议补充内容**：无，4 节齐全。

---

### 7. _generate_boolop (line 20666)

**现有 docstring 摘要**：
```
生成 BoolOpRegion 的 AST 节点列表

输入契约:
  region: BoolOpRegion，必须包含:
    op_chain / blocks / merge_block / value_target / prefix_block / _is_outer_condition
  skip_store_targets: 可选的已生成目标名集合

AST 映射规则:
  BoolOpRegion -> ast.BoolOp(op=And|Or, values=[...])
  两种生成模式:
    (1) 条件上下文模式: 写入 condition_expr，返回 None
    (2) 独立表达式模式: Assign / Return / Expr / if-like 分支

子区域处理:
  BoolOpRegion 通常是叶子区域
  通过 find_enclosing_parent 定位外层控制流区域
  prefix 块 STORE 识别为 pre-statement

字节码一致性约束:
  - and/or 短路跳转操作码
  - 条件上下文 vs 独立模式跳转差异
  - 取反规则 / value_target STORE 唯一性
  - 100% 匹配（boolop 132/132）+ 历史遗留问题说明
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（BoolOpRegion 字段 + skip_store_targets）
2. AST映射规则: ✅ 存在（BoolOp 节点 + 2 种模式 + 4 种独立形态）
3. 子区域处理: ✅ 存在（叶子区域声明 + 父区域定位 + prefix 处理）
4. 字节码一致性约束: ✅ 存在（短路操作码/模式差异/取反/唯一性/匹配状态/历史）

**建议补充内容**：无，4 节齐全。

---

### 8. _generate_ternary (line 21688)

**现有 docstring 摘要**：
```
生成 TernaryRegion 的 AST 语句列表

输入契约:
  region: TernaryRegion，必须包含:
    condition_block / true_value_block / false_value_block / merge_block /
    condition_chain_blocks / value_target / container_type
  skip_store_targets: 可选

AST 映射规则:
  TernaryRegion -> ast.IfExp(test, body, orelse)
  输出形态优先级:
    (1) value_target → Assign + 可能追加 Return
    (2) container_type → Expr(Dict/List/Tuple/Set 含 IfExp)
    (3) 无 target/container → Expr(IfExp) 或 Return(IfExp)

子区域处理:
  条件重建两路: condition_chain_blocks > 1 → BoolOp; 单块 → 直接重建
  true/false 值块通过 _build_ternary_value_expr 重建，可触发嵌套 ternary 递归

字节码一致性约束:
  - condition_block 末尾 POP_JUMP_IF_FALSE 跳向 false_block
  - true_value_block JUMP_FORWARD 跳向 merge
  - merge STORE/RETURN 一致
  - BoolOp 条件链顺序/操作符精确匹配
  - 100% 匹配（ternary 116/116）+ 历史问题说明
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（TernaryRegion 7 字段 + skip_store_targets）
2. AST映射规则: ✅ 存在（IfExp 节点 + 3 级输出形态优先级）
3. 子区域处理: ✅ 存在（两路条件重建 + 嵌套 ternary 递归）
4. 字节码一致性约束: ✅ 存在（跳转方向/JUMP/STORE/BoolOp 顺序/匹配状态/历史）

**建议补充内容**：无，4 节齐全。

---

### 9. _generate_basic_region (line 28741)

**现有 docstring 摘要**：
```
生成基础区域 AST（Basic Region → statement list）

本方法由 _generate_region 在 region.region_type == RegionType.BASIC 时分派调用...

输入契约:
  - 接收 Region 子类: Region（region_type=RegionType.BASIC）
  - 关键字段: entry / blocks / trailing_return_none
  - 前置条件: 结构化区域已先于本 region 完成生成

AST 映射规则:
  - 输出: 语句字典列表
  - 节点类型: Assign/AugAssign/AnnAssign/Expr/Return/Pass/Break/Continue/While
  - 字段对应: blocks 排序 dispatch / block_role 决定短路路径

子区域处理:
  - BASIC Region 为叶子节点，不递归 _generate_region
  - 逐块生成 + 控制流短路由 _generate_block_statements 完成
  - WITH_EXIT_CLEANUP/LOOP_EXIT/CONTINUE/BREAK 等角色处理
  - generated_blocks 去重

字节码一致性约束:
  - 块处理顺序与 start_offset 一致
  - WITH_EXIT_CLEANUP 不输出语句
  - generated_blocks 全局去重
  - stmts 顺序即源代码顺序
  - trailing_return_none 由下游处理
  - 100% 匹配（basic 122/122）
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（Region 字段 + 前置条件）
2. AST映射规则: ✅ 存在（输出节点类型清单 + 字段对应 + block_role 分派）
3. 子区域处理: ✅ 存在（叶子声明 + _generate_block_statements 委托 + 角色处理 + 去重）
4. 字节码一致性约束: ✅ 存在（顺序/cleanup 不输出/去重/stmts 顺序/return_none/匹配状态）

**建议补充内容**：无，4 节齐全。

---

### 10. _generate_region (line 2122) — 额外发现

**现有 docstring 摘要**：
无 docstring。方法体直接以 `if isinstance(region, ...)` 开头，是所有 `_generate_*` 的总分派入口。

**4 节模板对照**：
1. 输入契约: ❌ 缺失
2. AST映射规则: ❌ 缺失
3. 子区域处理: ❌ 缺失
4. 字节码一致性约束: ❌ 缺失

**建议补充内容**：作为区域分派入口，应补充：
- 输入契约：Region 基类 + skip_store_targets；前置不变量（结构化区域已归约）
- AST映射规则：按 region 类型分派到 _generate_if/loop/try/with/match/assert/boolop/ternary/basic_region
- 子区域处理：分派前的 with_cleanup/TryExcept/LoopRegion 跳过守卫；TernaryRegion 的多重 should_skip 守卫（WithRegion entry / TryExcept handler / AssertRegion message）
- 字节码一致性约束：分派唯一性（每块唯一归属）；PASS/BASIC 兜底

---

### 11. _generate_elif_else_chain (line 5815) — 额外发现

**现有 docstring 摘要**：
无 docstring。方法体直接以 `if cond_jump_instr is None` 开头。

**4 节模板对照**：
1. 输入契约: ❌ 缺失
2. AST映射规则: ❌ 缺失
3. 子区域处理: ❌ 缺失
4. 字节码一致性约束: ❌ 缺失

**建议补充内容**：应补充：
- 输入契约：cond_jump_instr（条件跳转指令）+ current_block；前置条件（_current_loop 非空）
- AST映射规则：递归生成 elif/else 链 → [{'type':'If', test, body, orelse}] 嵌套结构
- 子区域处理：递归调用自身 _generate_elif_else_chain 构建 orelse；_generate_block_statements 生成 then/else 块语句
- 字节码一致性约束：跳转目标块必须在 _current_loop.body_blocks 或 back_edge_block 内；IF_TRUE/IF_NONE 取反规则

---

### 12. _generate_value_context_chain_compare_assign (line 7301) — 额外发现

**现有 docstring 摘要**：
```
[Round4-04] 链式比较作赋值右值的 AST 生成。

字节码模式（`z = 0 < a < 10`）:
    header(cond_block): LOAD left; ...; JUMP_IF_FALSE_OR_POP → cleanup
    chain_block: LOAD cmp2; COMPARE_OP op2; JUMP_FORWARD → merge
    cleanup: SWAP; POP_TOP; fallthrough → merge
    merge: STORE_NAME target; LOAD_CONST None; RETURN_VALUE

与控制流链式比较的关键差异: ...

识别条件:
  1. region.chained_compare_ops 长度 ≥ 2
  2. region.condition_block 末尾指令 ∈ SHORT_CIRCUIT_JUMP_OPS
  3. region.merge_block 含 STORE_* 指令

生成 AST:
    {'type': 'Assign', 'targets': [...], 'value': {'type': 'Compare', ...}}

块归属: 标记 region.blocks 为 generated，避免父 IfRegion 重复处理。
```

**4 节模板对照**：
1. 输入契约: ❌ 缺失（虽有"识别条件"描述 region 字段，但未按"输入契约"节标题组织）
2. AST映射规则: ❌ 缺失（"生成 AST" 节描述了输出节点，但未按标准节标题组织）
3. 子区域处理: ❌ 缺失（"块归属" 提及 generated_blocks，但未按标准节标题组织）
4. 字节码一致性约束: ❌ 缺失（"字节码模式" 描述了字节码形态，但未按标准节标题组织）

**判定说明**：本方法有较详尽的 docstring 内容，且内容实质上覆盖了 4 节模板的部分语义（字节码模式 ≈ 字节码一致性约束/AST映射；识别条件 ≈ 输入契约；块归属 ≈ 子区域处理），但**完全未使用 4 节模板的标准节标题**，因此判定为部分合规。

**建议补充内容**：将现有内容重组为 4 节标准标题：
- 输入契约：IfRegion + chained_compare_ops/blocks + condition_block + merge_block
- AST映射规则：Assign 节点 + Compare 字段 + ternary 位置判定
- 子区域处理：TernaryRegion 嵌套检测（cond_block = ternary.merge_block）+ 块归属标记
- 字节码一致性约束：JUMP_IF_FALSE_OR_POP vs POP_JUMP_FORWARD_IF_FALSE 差异 + STORE 目标唯一性

---

### 13. _generate_try_body (line 14586) — 额外发现

**现有 docstring 摘要**：
无 docstring。方法体直接以 `body_stmts: List[Dict[str, Any]] = []` 开头。

**4 节模板对照**：
1. 输入契约: ❌ 缺失
2. AST映射规则: ❌ 缺失
3. 子区域处理: ❌ 缺失
4. 字节码一致性约束: ❌ 缺失

**建议补充内容**：应补充：
- 输入契约：TryExceptRegion；关键字段 try_blocks/try_offset_start/end/finally_copy_blocks
- AST映射规则：返回 List[Dict] 作为 Try.body；嵌套 TryExceptRegion 优先生成
- 子区域处理：嵌套 try 递归 _generate_try；finally normal path 副本 ternary 标记（R7-05/07/11）；finally_copy_blocks 截断
- 字节码一致性约束：嵌套 try 顺序（entry.start_offset <= first_try_block_offset）；finally copy 副本去重

---

### 14. _generate_handler_body_statements (line 16098) — 额外发现

**现有 docstring 摘要**：
无 docstring。方法体以注释 `# [Phase 3 adv17_try_except_star] 检测是否是 except* 框架块` 开头。

**4 节模板对照**：
1. 输入契约: ❌ 缺失
2. AST映射规则: ❌ 缺失
3. 子区域处理: ❌ 缺失
4. 字节码一致性约束: ❌ 缺失

**建议补充内容**：应补充：
- 输入契约：BasicBlock（handler 块）；前置条件（块属于 except handler body）
- AST映射规则：返回 List[Dict]；except* 框架指令过滤；exc_dispatch_jump 边界
- 子区域处理：handler_instrs 过滤后交由 _generate_block_statements；as-var 清理模式检测（R20-Bug7）
- 字节码一致性约束：CHECK_EXC_MATCH/CHECK_EG_MATCH 框架指令过滤；PREP_RERAISE_STAR 清理；EXTENDED_ARG 前缀处理

---

### 15. _generate_class_body_from_code (line 16998) — 额外发现

**现有 docstring 摘要**：
```
从code object生成类定义的body语句列表。
```
（仅 1 行摘要式 docstring）

**4 节模板对照**：
1. 输入契约: ❌ 缺失
2. AST映射规则: ❌ 缺失
3. 子区域处理: ❌ 缺失
4. 字节码一致性约束: ❌ 缺失

**建议补充内容**：应补充：
- 输入契约：code_obj（CodeType）；前置条件（类体 code object）
- AST映射规则：返回 List[Dict]（类 body 语句）；内部构建 CFGBuilder → RegionAnalyzer → RegionASTGenerator 链
- 子区域处理：独立生成器实例，不共享 generated_blocks 状态
- 字节码一致性约束：异常时返回 None（容错）；结果归一化为 list

---

### 16. _generate_block_statements (line 28814) — 额外发现

**现有 docstring 摘要**：
```
_generate_block_statements - 基本块 AST 语句生成（BasicBlock → ast.stmt 列表）

输入契约:
  - 接收 BasicBlock 及可选的父块 _cjb_parent
  - 若 block 已在 generated_blocks / generated_offsets 中，返回空列表
  - block.instructions 为原始字节码指令序列

AST 映射规则:
  - 输出: ast.Assign / ast.Expr / ast.Return / ast.Break / ast.Pass 等
  - 循环内 break 检测 / BlockRole.BREAK/PURE_BREAK / NOP+RETURN trivial
  - 通用语句重建

子区域处理:
  - 处理单个基本块，不直接递归子区域
  - generated_blocks / generated_offsets 标记
  - _loop_depth 区分循环内外

字节码一致性约束:
  - 块内所有有语义指令必须完整映射
  - 自赋值语句必须产出 Assign（R11 fix）
  - break/return 转换与跳转语义一致
  - 4 核心原则声明 + R11 修复说明
```

**4 节模板对照**：
1. 输入契约: ✅ 存在（BasicBlock + _cjb_parent + 去重前置条件）
2. AST映射规则: ✅ 存在（输出节点类型 + break 检测 + 角色处理 + 通用重建）
3. 子区域处理: ✅ 存在（单块声明 + 去重 + _loop_depth）
4. 字节码一致性约束: ✅ 存在（指令完整映射/自赋值/break 语义/原则/R11 修复）

**建议补充内容**：无，4 节齐全。

---

### 17. _generate_stmts_from_instrs (line 31603) — 额外发现

**现有 docstring 摘要**：
```
从指令列表中提取多条语句，用于回边块等多语句场景。

区域归约算法符合度:
  本方法服务于 LoopRegion 回边块等多语句块场景...
  按语句边界逐条归约...

字节码模式:
  - STORE_ATTR: ... → obj.attr = value
  - STORE_SUBSCR: ... → container[index] = value
  - STORE_FAST/NAME/GLOBAL/DEREF: ... → name = value
  - POP_TOP: <expr instrs>, POP_TOP → expr 语句

参数:
  instrs: 回边块过滤后的指令列表
  block: 指令所属的基本块

返回:
  AST 语句字典列表

典型应用场景:
  get_str_data 外层 for 循环回边块含两条兄弟赋值...
```

**4 节模板对照**：
1. 输入契约: ❌ 缺失（"参数" 节描述了入参，但未按"输入契约"标题组织，且缺少前置不变量）
2. AST映射规则: ❌ 缺失（"字节码模式" 节描述了映射，但未按标准节标题组织）
3. 子区域处理: ❌ 缺失（"区域归约算法符合度" 提及回边块归属，但未按标准节标题组织）
4. 字节码一致性约束: ❌ 缺失（"区域归约算法符合度" 涉及原则，但未按标准节标题组织）

**判定说明**：本方法有较详尽的 docstring 内容，且内容实质上覆盖了 4 节模板的部分语义（参数 ≈ 输入契约；字节码模式 ≈ AST映射规则；区域归约算法符合度 ≈ 子区域处理/字节码一致性），但**完全未使用 4 节模板的标准节标题**，因此判定为部分合规。

**建议补充内容**：将现有内容重组为 4 节标准标题：
- 输入契约：instrs（已过滤指令列表）+ block；前置条件（已去除 RESUME/NOP/CACHE/PUSH_NULL/JUMP_*/for_target 消费指令）
- AST映射规则：Assign(Subscript/Attribute/Name) + Expr；按 STORE 边界切分
- 子区域处理：回边块作为 LoopRegion body 末尾抽象节点；逐条归约不泄漏
- 字节码一致性约束：栈效应切分（TOS2/TOS1/TOS0）；STORE_ATTR 不被 STORE_SUBSCR 吞并（R22）

---

### 18. _generate_return_ast (line 32870) — 额外发现

**现有 docstring 摘要**：
无 docstring。方法体直接以 `if return_instr is not None:` 开头。

**4 节模板对照**：
1. 输入契约: ❌ 缺失
2. AST映射规则: ❌ 缺失
3. 子区域处理: ❌ 缺失
4. 字节码一致性约束: ❌ 缺失

**建议补充内容**：应补充：
- 输入契约：BasicBlock + 可选 return_instr（Instruction）；前置条件（块含 RETURN_VALUE/RETURN_CONST）
- AST映射规则：返回 {'type':'Return', 'value': ...}；RETURN_CONST → Constant；RETURN_VALUE + LOAD_CONST None → Constant(None)；SWAP+POP_TOP 模式检测
- 子区域处理：不递归子区域；value_instrs 交由 expr_reconstructor.reconstruct
- 字节码一致性约束：skip_ops 过滤集（RESUME/NOP/CACHE/POP_TOP/PUSH_NULL/COPY/POP_EXCEPT/PUSH_EXC_INFO/PRECALL/CALL）；generator 函数 SWAP 保留（is_in_gen_loop）

---

## 审计结论

### 任务指定的 9 个方法
全部合规（9/9）。这些方法是区域归约算法的核心结构化区域生成器，docstring 已严格按 4 节模板编写，内容详实，包含字段映射、子区域递归规则、字节码不变量及测试匹配状态。

### 额外发现的 9 个方法
- 合规：1 个（_generate_block_statements）
- 部分合规：3 个（_generate_value_context_chain_compare_assign / _generate_class_body_from_code / _generate_stmts_from_instrs）—— 有 docstring 但未按 4 节模板组织
- 不合规：5 个（_generate_region / _generate_elif_else_chain / _generate_try_body / _generate_handler_body_statements / _generate_return_ast）—— 完全无 docstring

### 全量统计（18 个真实方法）

| 合规状态 | 方法数 | 占比 |
|----------|--------|------|
| 合规 | 10 | 55.6% |
| 部分合规 | 3 | 16.7% |
| 不合规 | 5 | 27.8% |
| **合计** | **18** | **100%** |

### 优先级建议
1. **高优先级（不合规，无 docstring）**：_generate_region（分派入口，影响全局理解）/ _generate_try_body / _generate_handler_body_statements / _generate_return_ast / _generate_elif_else_chain
2. **中优先级（部分合规，需重组节标题）**：_generate_value_context_chain_compare_assign / _generate_stmts_from_instrs（内容已较完整，仅需重组为 4 节标准标题）
3. **低优先级（部分合规，需扩写）**：_generate_class_body_from_code（仅 1 行摘要，需扩写为完整 4 节）

### 备注
- `_generate_match_case_body` @ 18723 经核查为 `_generate_match` 方法 docstring 内的示例代码（位于 ```python 代码块中），并非真实方法定义，已排除在审计范围外。
- 所有合规方法的 docstring 末尾均声明遵循"区域归约算法 4 核心原则"（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口），并标注字节码匹配状态（如 "100% 完全匹配"），可作为后续补充 docstring 的参考范式。

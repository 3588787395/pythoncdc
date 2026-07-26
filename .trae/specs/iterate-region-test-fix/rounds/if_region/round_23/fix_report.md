# Round 23 Fix Report — IF 区域 C7 簇 + 回归修复

## 概要

| 指标 | R22 基线 | R23 当前 | Δ |
|---|---|---|---|
| if_region 失败数 | 28 | 21 | **-7** |
| if_region 通过数 | 789 | 796 | +7 |
| if_region skipped | 10 | 10 | 0 |
| ternary 失败数 | 0 | 0 | 0 |
| ternary 通过数 | 506 | 506 | 0 |
| ternary skipped | 36 | 36 | 0 |

**结论**: IF 区域 R23 净修复 7 个测试（含 C7 簇 5 个 + Bug 1/2/3 新增 3 个 - 回归 1 个），ternary 区域 0 回归。

## 修复分类

### 阶段 1: C7 簇 5 个早期修复（已稳定）
- ✅ test_adv18_try_finally_in_if_body — inner_merge 检测 both-sink-terminal + 外部前驱检查
- ✅ test_adv19_try_except_else_in_if_body — inner_merge + else_blocks 协调
- ✅ test_adv19_while_else_break_in_elif_body — LoopRegion else_blocks 过滤逻辑修复
- ✅ test_adv19_tuple_unpack_in_if_body — UNPACK_EX 后 trailing 语句丢失修复
- ✅ test_adv20_yield_in_while_in_if_body — trailing_return_none 仅顶层 LoopRegion 过滤

### 阶段 2: Bug 1/2/3 新修复（3 个目标测试）
- ✅ Bug 1（模式 3）: test_adv19_multiline_return_in_if_body
  - 根因: TernaryRegion 过度延伸进嵌套 IfRegion 的 condition_block，使嵌套 if 条件退化为裸表达式 `(result['doubled'] > 100)`，return 语句丢失
  - 修复: 在 TernaryRegion 识别时，若 merge_block 同时是嵌套 IfRegion 的 condition_block，停止 ternary 延伸让 IfRegion 优先归约（嵌套即抽象节点原则）
- ✅ Bug 2（模式 4）: test_adv20_walrus_in_while_cond_nested_if
  - 根因: walrus `(n := next(it, None))` 反编译后，同块内未消费的 `LOAD_GLOBAL next / LOAD_FAST it / LOAD_CONST None / PRECALL / CALL` 序列作为副作用残留，多出裸 `next` 表达式语句
  - 修复: walrus 副作用残留过滤（每块唯一归属原则 — walrus 副作用属 walrus 表达式内子节点）
- ✅ Bug 3（模式 F）: test_adv19_multi_not_chain_in_if_cond
  - 根因: `_ie_has_external_pred` 仅排除 inner_condition_block，未考虑布尔运算链（a and b and c and d）中其他条件块，else 块被错误标记为 post-if 合并点
  - 修复: 优化外部前驱判断，将同一布尔运算链中的所有条件块纳入排除范围（父引用子入口原则）

### 阶段 3: 回归修复（5 + 3 = 8 个）
- ✅ R-A if59 系列（3 测试）: test_if59ifelifreturn_a/n/x
  - 根因: Bug 1/2/3 修复后，`final_else` 过滤逻辑误将函数级 RETURN 终态块当作 post-if 合并点，导致 `return 0` 语句丢失
  - 修复: 在 `final_else` 过滤前检查 else_succ 是否是函数级 RETURN 终态块，若是则保留为 final_else（每块唯一归属原则 — 函数级终态块属于 final_else，不可被 inner_merge 占用）
  - 代码位置: `core/cfg/region_analyzer.py:10754-10804` 新增 `_else_has_external_pred` 检查
- ✅ R-B adv11 系列（2 测试）: test_adv11_nested_ternary_walrus_cond, test_adv11_walrus_ternary_if_cond
  - 根因: Bug 1 阶段修复过度限制简单 walrus+ternary 场景，使 IfRegion 重复消费 TernaryRegion 的 merge_block
  - 修复: 通过 generated_blocks 守卫使 IfRegion 引用 TernaryRegion 入口而非独立生成（父引用子入口原则）
  - 代码位置: `core/cfg/region_ast_generator.py:21460-21474`
- ✅ R-C if84 系列（3 测试）: test_if84ifchainedcompareelse_a/n/x
  - 根因: if59 修复添加的 `_else_has_external_pred` 排除集仅含 `{block, then_succ, else_succ}`，未排除链式比较（`0 < a < 10`）的中间条件块和 else 清理跳板。中间块被误判为外部前驱 → `merge=else_succ` → `else_blocks` 为空 → else 分支丢失
  - 修复: 扩展排除集为 `{block, then_succ, else_succ, _else_succ_original} | chain_blocks`，镜像 `_check_elif_chain._ie_has_external_pred` 的排除集构造方式
  - 代码位置: `core/cfg/region_analyzer.py:10681-10684` 捕获原始 `_else_succ_original` + `10803-10818` 扩展排除集

## 修改的文件
- `core/cfg/region_analyzer.py` (+约 165 行)
- `core/cfg/region_ast_generator.py` (+约 95 行)

## 算法合规性自检（区域归约 4 原则）

| 原则 | 合规 | 论证 |
|---|---|---|
| 自底向上归约 | ✅ | TernaryRegion 与 IfRegion 冲突时按归约顺序决策，不回溯修正 |
| 每块唯一归属 | ✅ | 函数级终态块属 final_else（if59 修复）；链式比较中间块属当前 IfRegion（if84 修复）；walrus 副作用属 walrus 表达式（Bug 2 修复） |
| 嵌套即抽象节点 | ✅ | TernaryRegion 在 IfRegion 中作单抽象节点（Bug 1 修复停止 ternary 延伸） |
| 父引用子入口 | ✅ | IfRegion 引用 TernaryRegion 入口（adv11 修复 generated_blocks 守卫） |

## 禁止项自检
- ✅ 未引入跨区域启发式特殊 case
- ✅ 未添加后处理补丁
- ✅ 未使用启发式优先级覆盖
- ✅ 未展平嵌套
- ✅ 未硬编码深度上限
- ✅ 未修改任何测试文件
- ✅ 未在源码添加 print/pdb/breakpoint
- ✅ 未在根级或 round_23 目录留 _debug_*.py 调试文件

## 剩余未修复（21 个失败，留待 R24+）
- C1 嵌套 ternary 条件（test_adv01_nested_ternary_cond, test_adv13_ternary_*, test_adv15_ternary_*）
- C4 chained_compare 在 if 条件（test_adv18_if_with_chained_compare_cond）
- C5 lambda_iife / mixed_complex_branches
- C6 with multi_ctx / for_else_break / nested_with_try
- C8 assert_chained_cmp / star_expr_in_call / tuple_return
- C9 dictcomp_complex_filter
- C10 for_continue / chained_in_check / raise_from_complex

## commit
待主代理 git commit + push

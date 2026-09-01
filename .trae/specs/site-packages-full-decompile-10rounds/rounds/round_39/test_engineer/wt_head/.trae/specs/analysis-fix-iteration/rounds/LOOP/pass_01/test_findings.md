# 架构工程师分析报告 — Pass 1 / LOOP 区域

## 方法定位
- `_identify_loop_regions`: region_analyzer.py L2717-L3253
- `_generate_loop`: region_ast_generator.py L2682-L2919
- 关键后处理补丁: `_cleanup_try_else_in_loop_body` (L3320), `_detect_and_filter_conditional_recheck_fake_loops` (L3371), `_rebuild_block_roles_after_fake_loop_removal` (L3255)

## 4 原则合规性
- 原则 1（自底向上归约）：部分违反 — 末尾重扫 condition_recheck/chain_blocks、跨 LoopRegion 去重
- 原则 2（每块唯一归属）：违反 — FOR 子集过滤豁免、yield_from LoopRegion 与 TernaryRegion 块重叠
- 原则 3（嵌套即抽象节点）：部分违反 — `_cleanup_try_else_in_loop_body` 事后修复登记错误
- 原则 4（入口引用语义）：基本合规，但 `_loop_generate_while` 反向抓前驱 IfRegion 违反

## 反模式检查
- 无禁止前缀方法名（_fix_/_patch_ 等）
- 无硬编码深度上限
- **8 处后处理补丁**（含 3 处 LOOP 直接相关）：
  - `_cleanup_try_else_in_loop_body` (L3320, analyze L1599 调用)
  - `_detect_and_filter_conditional_recheck_fake_loops` (L3371, analyze L1609 调用)
  - `_rebuild_block_roles_after_fake_loop_removal` (L3255, analyze L1611 调用)
  - 跨 LoopRegion 去重 (L3212-3251)
  - yield_from LoopRegion 事后移除 (analyze L1295-1314)
- 跨区域启发式: `_is_fused_ternary_false_value_block` (LOOP 阶段感知 TERNARY)
- 硬编码判据: `_is_fake_loop` 中 `len(body) != 2`

## 本轮建议修复（3 项，聚焦消除反模式，不触碰失败用例）
### 修复 1 — 删除 `_loop_generate_while` 死代码
位置: region_ast_generator.py L3431-3436（与 L3424-3429 完全重复）
理由: 零风险死代码移除

### 修复 2 — `_find_loop_else` 加 block_to_region 守卫，消除 `_cleanup_try_else_in_loop_body`
位置: region_analyzer.py `_find_loop_else` L3720-3735 / L3802-3808 / L3842-3848
策略: 新增 `_is_owned_by_other_region` 守卫，每个 else_blocks 收集点调用；删除 `_cleanup_try_else_in_loop_body` 方法体 + analyze() L1599 调用
理由: 消除 1 个跨区域后处理补丁（~50 行），统一为识别期 block_to_region 检查

### 修复 3 — 扩展 `_is_fake_loop` 识别 continue 假循环，消除两个后处理补丁
位置: region_analyzer.py `_is_fake_loop` L4308-4364
策略: 新增 `_is_continue_recheck_fake_loop` 结构判据方法（基于 block_to_region 外层 LOOP 占用 + body 块 JUMP_BACKWARD 跳外层 header）；删除 `_detect_and_filter_conditional_recheck_fake_loops` + `_rebuild_block_roles_after_fake_loop_removal` + analyze() L1609-1616 调用
理由: 消除 2 个后处理补丁（~110 行），消除 `len(body) != 2` 硬编码

## 其他问题（后续迭代）
- 复合 and 条件链计数配额启发式（L2948-3043, ~95 行）
- `_loop_generate_while` 中 `_preceding_if_cond` 拼装 BoolOp
- `is_yield_from_loop` 与 TernaryRegion 块重叠事后移除

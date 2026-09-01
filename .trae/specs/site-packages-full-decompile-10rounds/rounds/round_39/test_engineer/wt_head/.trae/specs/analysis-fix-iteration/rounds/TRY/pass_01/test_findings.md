# 架构工程师分析报告 — Pass 1 / TRY 区域

## 方法定位
- `_identify_try_except_regions`: region_analyzer.py L4681-L5498
- `_generate_try`: region_ast_generator.py L12614-L13188
- 后处理补丁密集: Pattern A/B/C/E fix, R4-09 系列, R18 Bug 25-27, te046

## 4 原则合规性
- 原则 1（自底向上归约）：部分违反 — TRY 优先级最高(TOP-DOWN) + 生成器 try_try 嵌套补偿(L12933) + _skipped_outer_try 包装(L12994)
- 原则 2（每块唯一归属）：基本合规但脆弱 — generated_blocks 反复 add/discard
- 原则 3（嵌套即抽象节点）：部分违反 — _generate_try_body 4 并列启发式条件(L11952)
- 原则 4（入口引用语义）：部分违反 — entry_block 识别阶段二次改写(L4973, L5386)

## 反模式检查
- 无禁止前缀方法名（_merge_block_is_loop_back_edge 在 L18304 非TRY专属）
- **硬编码深度上限**: `_find_return_through_cleanup_chain(max_depth=6)` (L13190, L13245)
- **后处理补丁密集**: try_try 嵌套补偿 / _skipped_outer_try 包装 / R4-09 系列 7 处 / Pattern A/B/C/E fix
- **文档-代码矛盾**: L4688 docstring `TRY > WITH > LOOP` vs L1226/L1231 实现 `TRY > LOOP > WITH`
- **复制粘贴**: pre_handler_blocks 双分支(L4922 vs L4955) `if pre_handler_blocks:` 内 3 行完全相同

## 本轮建议修复（3 项，零/低风险，聚焦反模式消除）
### 修复 A — 统一 L4688 docstring 与实现顺序
位置: region_analyzer.py L4688
策略: 改为 `TRY > LOOP > WITH > MATCH > ASSERT`，与 L1226/L1231 一致
理由: 消除文档-代码矛盾，零行为变更

### 修复 B — 移除 `_find_return_through_cleanup_chain` 的 max_depth=6 硬编码
位置: region_ast_generator.py L13190(签名) + L13245(`if len(path) > max_depth: continue`)
策略: 删除 max_depth 参数与 L13245 检查，依赖 visited 集合(L13238 已防环)保证终止性
理由: 消除硬编码深度上限，解锁长 cleanup 链场景

### 修复 C — 提取 pre_handler_blocks 应用逻辑为单一共享块
位置: region_analyzer.py L4922-L4929 与 L4955-L4962
策略: 将两处 `if pre_handler_blocks:` 内 3 行复制粘贴提取到 if/else 之后共享代码段
理由: 消除复制粘贴后处理，单一机制易扩展，行为等价

## 其他问题（后续迭代）
- try_try 嵌套补偿移除（高风险，需先在分析器完整识别外层 handler）
- _generate_try_body 嵌套检测统一为区间包含（中风险）
- 指令名判据（_classify_handler_type 5 opname, cleanup_blocks 20+ opname 白名单）

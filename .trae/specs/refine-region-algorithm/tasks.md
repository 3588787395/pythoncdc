# Tasks

> 目标：在保持 99.95% 基线（2067/2068 + match_region 198/198）的前提下，
> 消除 2 个 WARN、移除硬编码嵌套上限、减少 isinstance 分支至 < 20，
> 使程序完全符合区域归约算法并支持无限嵌套。
>
> **当前基线（2026-07-14）**:
> - 测试矩阵：2067/2068（99.95%，仅 te046 暂缓）
> - match_region：198/198（2 skipped）
> - 算法符合度：PARTIALLY COMPLIANT（WARN-1: try_except depth 特例，WARN-2: with 后处理补丁）
> - isinstance.*Region 出现次数：50+（待精确统计）
> - 硬编码嵌套上限：`depth > 3`（L3404, L3454）
> - Git：11 个 fix-* spec 目录删除 + 7 个核心文件修改 + 调试产物待提交

## Phase 1: 提交仓库更新（基线固化）

- [ ] Task 1.1: 归档调试产物
  - [ ] 确认 `region-decompile-perfection/` 下的 `_diag_*.txt`、`diag_while_loop/`、`failures_baseline.md`、`*_analysis.md` 是需保留的归档还是应删除
  - [ ] 删除根目录临时文件 `baseline_loop.txt`、`baseline_match.txt`、`baseline_try.txt`、`_diag_bytecode_diff.py`（若为一次性脚本）
  - [ ] 保留 `.quality_baseline.json`（若为基线指标文件）
- [ ] Task 1.2: 暂存并提交
  - [ ] `git add` 删除的 11 个 fix-* spec 目录
  - [ ] `git add` 修改的 7 个核心文件（region_analyzer.py / region_ast_generator.py / ast_generator_v2.py / code_generator.py / comprehension_generator.py / pattern_parser.py / run_test_matrix.py）
  - [ ] `git add` 修改的 region-decompile-perfection spec 文档
  - [ ] `git commit -m "..."` 提交（消息描述：完成 region-decompile-perfection，99.95% 基线，清理冗余 spec）
- [ ] Task 1.3: 推送至远程
  - [ ] `git push` 推送当前分支
  - [ ] 验证推送成功
- [ ] Task 1.4: 基线验证
  - [ ] `python tests/exhaustive/run_test_matrix.py` 全量运行确认 2067/2068
  - [ ] `python -m unittest discover -s tests/exhaustive/match_region` 确认 198/198（2 skipped）

## Phase 2: 复杂度审计与精确测量

- [ ] Task 2.1: 精确统计 isinstance.*Region 分布
  - [ ] 在 `region_analyzer.py` 中统计 `isinstance\([^,]+,\s*\w*Region\)` 总数与各类型分布
  - [ ] 按方法归类（哪些方法最依赖 isinstance 分派）
  - [ ] 标记可改为多态/分派表的位点（如 `process_regions` L500-600、`process_try_except` L1000-1100）
- [ ] Task 2.2: 精确定位 2 个 WARN 的代码范围
  - [ ] WARN-1: `_identify_try_except_regions` 中基于 `depth` 字段的特例判断（确认行号 L3689-3700 及周边）
  - [ ] WARN-2: `_merge_consecutive_with_regions` 后处理补丁（确认行号 L5986-6005 及调用点）
- [ ] Task 2.3: 精确定位硬编码嵌套上限
  - [ ] `_is_with_exit_leading_to_break` 的 `depth > 3`（L3404）
  - [ ] `_is_with_exit_leading_to_continue` 的 `depth > 3`（L3454）
  - [ ] 确认这两个方法的递归调用模式与终止条件

## Phase 3: 移除硬编码嵌套上限（支持无限嵌套）

- [ ] Task 3.1: 改写 `_is_with_exit_leading_to_break`
  - [ ] 移除 `depth > 3` 上限，改用 `visited: Set[int]` 集合记录已访问块
  - [ ] 递归终止条件改为：块已在 visited 中 / 块超出当前 loop 范围 / 块为 RETURN
  - [ ] 更新方法 docstring 说明无限嵌套支持
- [ ] Task 3.2: 改写 `_is_with_exit_leading_to_continue`
  - [ ] 同 Task 3.1 方案
- [ ] Task 3.3: 构造深层嵌套测试用例验证
  - [ ] 生成 5 层嵌套 with + break 的测试（当前 depth>3 会截断）
  - [ ] 生成 5 层嵌套 with + continue 的测试
  - [ ] 运行 L2 nested（285）+ L3 triple_nested（120）确认无回归
  - [ ] 运行 with_region（191）确认无回归
- [ ] Task 3.4: 全量回归
  - [ ] `python tests/exhaustive/run_test_matrix.py` 确认 ≥ 2067/2068
  - [ ] 提交本阶段改动

## Phase 4: 消除 WARN-1（try_except depth 跨区域特例）

- [ ] Task 4.1: 分析异常表 depth 字段的语义
  - [ ] 读取 `_identify_try_except_regions` 中 depth 比较逻辑（L3689-3700 及周边 L3606-3765）
  - [ ] 确认 depth 字段反映异常表嵌套层级（CPython 异常表结构）
  - [ ] 设计基于 `(start, end, target)` 区间包含关系的替代判定
- [ ] Task 4.2: 重写 depth 比较为结构包含判定
  - [ ] 嵌套关系判定：handler A 嵌套于 handler B 内 ⟺ A.start ∈ [B.start, B.end) 且 A.target == B.target 或 A.target ∈ B 的 handler 块
  - [ ] 移除所有 `other.get('depth', 0) < info.get('depth', 0)` 等数值比较特例
  - [ ] 更新 docstring 说明结构包含判定算法
- [ ] Task 4.3: 回归测试 try_except
  - [ ] 运行 L1 try_except（230）确认无回归
  - [ ] 运行 L2 nested（285）确认无回归（含 n13try_for_if_break 等）
  - [ ] 全量 `run_test_matrix.py` 确认 ≥ 2067/2068
  - [ ] 提交本阶段改动

## Phase 5: 消除 WARN-2（with 后处理补丁）

- [ ] Task 5.1: 分析 `_merge_consecutive_with_regions` 调用点
  - [ ] 读取 L5986-6005 实现与 `analyze()` 中的调用点
  - [ ] 确认合并条件：相邻 WithRegion 的 entry 连续 + 共享同一 scope
- [ ] Task 5.2: 将合并逻辑前移至 `_identify_with_regions`
  - [ ] 在 `_identify_with_regions` 识别出 WithRegion 后，检查前一个区域是否为相邻 WithRegion
  - [ ] 若相邻则合并（扩展前一个 WithRegion 的 body 包含后一个），不创建新 WithRegion
  - [ ] 移除 `_merge_consecutive_with_regions` 方法及其在 `analyze()` 的调用
- [ ] Task 5.3: 回归测试 with_region
  - [ ] 运行 L1 with_region（191）确认无回归
  - [ ] 运行 L2 nested（285）确认无回归
  - [ ] 全量 `run_test_matrix.py` 确认 ≥ 2067/2068
  - [ ] 提交本阶段改动

## Phase 6: 减少 isinstance 分支（目标 < 20 处）

- [ ] Task 6.1: 识别可多态化的分派模式
  - [ ] 统计 `process_regions` (L500-600) 中的 isinstance 链
  - [ ] 统计 `process_try_except` (L1000-1100) 中的 isinstance 链
  - [ ] 识别「按类型执行不同合并/归属逻辑」的模式（如 L1085-1161 的 LoopRegion/IfRegion/TryExceptRegion 分派）
- [ ] Task 6.2: 引入多态方法或分派表
  - [ ] 为高频分派类型（LoopRegion / IfRegion / TryExceptRegion / WithRegion / BoolOpRegion）添加多态方法（如 `merge_into_parent(parent_region) -> bool`）
  - [ ] 或构造分派表 `_REGION_DISPATCH = {LoopRegion: _handle_loop_in_parent, ...}`
  - [ ] 替换 isinstance 链为多态调用或分派表查找
- [ ] Task 6.3: 验证 isinstance 数量下降
  - [ ] 重新统计 `isinstance.*Region` 出现次数，确认 < 20
  - [ ] 全量 `run_test_matrix.py` 确认 ≥ 2067/2068
  - [ ] 提交本阶段改动

## Phase 7: 算法符合度最终验证

- [ ] Task 7.1: 重新执行算法符合度审计
  - [ ] 反模式1 跨区域特例：PASS（WARN-1 已消除）
  - [ ] 反模式2 后处理补丁：PASS（WARN-2 已消除）
  - [ ] 反模式3 启发式优先级覆盖：PASS
  - [ ] 反模式4 破坏嵌套的扁平化：PASS
  - [ ] 整体：FULLY COMPLIANT
- [ ] Task 7.2: 无限嵌套验证
  - [ ] 构造 10 层嵌套 with+break/continue 测试，验证正确识别
  - [ ] 构造 10 层嵌套 try/except 测试，验证正确识别
  - [ ] 确认无任何硬编码深度上限残留（grep `depth > \d` 无结果）
- [ ] Task 7.3: 最终基线确认
  - [ ] `python tests/exhaustive/run_test_matrix.py` 全量 ≥ 99.95%
  - [ ] `python -m unittest discover -s tests/exhaustive/match_region` 198/198
  - [ ] `isinstance.*Region` 计数 < 20
- [ ] Task 7.4: 提交并推送最终版本
  - [ ] `git commit` 最终改动
  - [ ] `git push` 推送
  - [ ] 更新 spec 文档状态为已完成

# Task Dependencies

- Task 1（提交基线）→ 必须先完成，作为后续改动的起点
- Task 2（审计）→ 依赖 Task 1，为 Task 3-6 提供精确数据
- Task 3（移除嵌套上限）、Task 4（WARN-1）、Task 5（WARN-2）→ 依赖 Task 2，三者相互独立可并行
- Task 6（减少 isinstance）→ 依赖 Task 3-5 完成（避免合并冲突），但审计部分可与 Task 3-5 并行
- Task 7（最终验证）→ 依赖 Task 3-6 全部完成

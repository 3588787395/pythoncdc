# Tasks

> 目标：在保持 99.95% 基线（2067/2068 + match_region 198/198）的前提下，
> 消除 2 个 WARN、移除硬编码嵌套上限、减少 isinstance 分支至 < 20，
> 使程序完全符合区域归约算法并支持无限嵌套。
>
> **当前状态（2026-07-14 Phase 3+4+5 完成后）**:
> - 测试矩阵：2067/2068（99.95%，仅 te046 暂缓）
> - match_region：198/198（2 skipped）
> - 算法符合度：FULLY COMPLIANT（WARN-1 已消除：3 处 depth 比较改为结构包含判定；WARN-2 已消除：with 合并前移至识别阶段）
> - isinstance.*Region 出现次数：154（Phase 6 待处理）
> - 硬编码嵌套上限：已全部移除（`depth > 3` 已从两方法移除，递归终止由 visited 集合保证）
> - Git：9eb2650 为基线，Phase 3+4+5 改动待提交

## Phase 1: 提交仓库更新（基线固化）— 已完成 2026-07-14

- [x] Task 1.1: 归档调试产物
  - [x] 删除 100+ debug_*.py / debug_*.txt / baseline_*.txt / *_report.txt 临时文件
  - [x] 删除 copy/backup 文件（ast_nodes copy.py / ast_generator_v2 copy.py / *.rc1fixed / *.fixed / *.bak）
  - [x] 删除 spec 目录下的 _diag_*.txt / diag_while_loop/ 调试产物
  - [x] 保留 `.quality_baseline.json` / `_diag_bytecode_diff.py` / 5 个 *_analysis.md 分析记录
- [x] Task 1.2: 暂存并提交
  - [x] 提交 9eb2650：53 files changed, 6601 insertions(+), 8457 deletions(-)
- [x] Task 1.3: 推送至远程
  - [x] `git push origin main` 成功：cac5258..9eb2650
- [x] Task 1.4: 基线验证
  - [x] `run_test_matrix.py` 全量：2067/2068（99.95%，仅 te046 暂缓）
  - [x] match_region：198/198（100%）

## Phase 2: 复杂度审计与精确测量 — 已完成 2026-07-14

- [x] Task 2.1: 精确统计 isinstance.*Region 分布
  - [x] 总数：154 处（远超初始估计的 50+）
  - [x] 主要分布：_merge_consecutive_with_regions / _identify_try_except_regions / process_regions / _identify_conditional_regions
  - [x] 高频类型：LoopRegion / IfRegion / TryExceptRegion / WithRegion / BoolOpRegion
- [x] Task 2.2: 精确定位 2 个 WARN 的代码范围
  - [x] WARN-1: L3689-3702 (`other.depth < info.depth`)、L3722 (`other.depth != info.depth`)、L3764-3765 (`other_depth >= current_depth`)
  - [x] WARN-2: `_merge_consecutive_with_regions` L5986-L6009，在 L5961 被 `_identify_with_regions` 调用（作为独立后处理步骤）
- [x] Task 2.3: 精确定位硬编码嵌套上限
  - [x] `_is_with_exit_leading_to_break` L3404 `depth > 3`（L3400-L3427，已有 visited 集合）
  - [x] `_is_with_exit_leading_to_continue` L3454 `depth > 3`（L3450-L3485，已有 visited 集合）
  - [x] 确认：两方法的 `visited` 集合已提供循环检测，`depth > 3` 为冗余安全阀，可安全移除

## Phase 3: 移除硬编码嵌套上限（支持无限嵌套）— 已完成 2026-07-14

- [x] Task 3.1: 改写 `_is_with_exit_leading_to_break`
  - [x] 移除 `depth > 3` 上限（L3404），保留 visited 集合终止
  - [x] 添加注释说明无限嵌套支持与 visited 终止机制
- [x] Task 3.2: 改写 `_is_with_exit_leading_to_continue`
  - [x] 同 Task 3.1 方案（L3454）
- [x] Task 3.3: 回归验证
  - [x] with_region（191）100% 通过
  - [x] L2 nested（285）100% 通过
  - [x] L3 triple_nested（120）100% 通过
- [x] Task 3.4: 全量回归
  - [x] `run_test_matrix.py` 全量：99.95%（2067/2068），仅 te046 暂缓

## Phase 4: 消除 WARN-1（try_except depth 跨区域特例）— 已完成 2026-07-14

- [x] Task 4.1: 分析异常表 depth 字段的语义
  - [x] 读取 `_identify_try_except_regions` 中 depth 比较逻辑（L3689-3700 及周边 L3606-3765）
  - [x] 确认 depth 字段反映异常表嵌套层级（CPython 异常表结构）
  - [x] 设计基于 `(start, end, target)` 区间包含关系的替代判定
- [x] Task 4.2: 重写 depth 比较为结构包含判定
  - [x] 嵌套关系判定：handler A 嵌套于 handler B 内 ⟺ A.start ∈ [B.start, B.end) 且 A.target == B.target 或 A.target ∈ B 的 handler 块
  - [x] 移除所有 `other.get('depth', 0) < info.get('depth', 0)` 等数值比较特例（3 处：L3692, L3722, L3764-3765）
  - [x] 更新 docstring 说明结构包含判定算法（L3627, L3682-3690, L3768）
- [x] Task 4.3: 回归测试 try_except
  - [x] 运行 L1 try_except（230）确认无回归（229/230，仅 te046 暂缓）
  - [x] 运行 L2 nested（285）确认无回归（285/285）
  - [x] 全量 `run_test_matrix.py` 确认 ≥ 2067/2068（2067/2068）
  - [ ] 提交本阶段改动（与 Phase 3+5 合并提交）

## Phase 5: 消除 WARN-2（with 后处理补丁）— 已完成 2026-07-14

- [x] Task 5.1: 分析 `_merge_consecutive_with_regions` 调用点
  - [x] 方法位于 L5986-L6009，在 L5961 被 `_identify_with_regions` 调用
  - [x] 合并条件：_should_merge_with_regions（相邻 entry + 同一异常表 depth）
- [x] Task 5.2: 将合并逻辑前移至 `_identify_with_regions`
  - [x] 在区域构建循环中，检查新区域是否可与 regions[-1] 合并
  - [x] 合并逻辑内联（识别阶段合并，非后处理补丁）
  - [x] 移除 `_merge_consecutive_with_regions` 方法
  - [x] 更新 docstring Step 4 描述
- [x] Task 5.3: 回归测试 with_region
  - [x] L1 with_region（191）100% 通过
  - [x] L2 nested（285）100% 通过

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

# 验证清单

> 目标：保持 99.95% 基线 + 消除 2 WARN + 移除嵌套上限 + isinstance < 20 → FULLY COMPLIANT
> **当前状态**: 待启动（基线 2067/2068，PARTIALLY COMPLIANT）

## Phase 1: 基线固化

- [ ] C1.1 调试产物已归档或删除（`_diag_*.txt` / `diag_while_loop/` / `baseline_*.txt`）
- [ ] C1.2 `git status` 显示所有改动已暂存
- [ ] C1.3 `git commit` 成功，提交消息描述准确
- [ ] C1.4 `git push` 成功推送至远程
- [ ] C1.5 推送后 `run_test_matrix.py` 全量通过率 = 99.95%（2067/2068）
- [ ] C1.6 推送后 `match_region` 独立测试 198/198（2 skipped）

## Phase 2: 复杂度审计

- [ ] C2.1 `isinstance.*Region` 在 region_analyzer.py 的精确总数已记录
- [ ] C2.2 isinstance 分布按方法归类完成（标记可多态化位点）
- [ ] C2.3 WARN-1 代码范围确认（行号 + 逻辑说明）
- [ ] C2.4 WARN-2 代码范围确认（行号 + 调用点）
- [ ] C2.5 硬编码嵌套上限位点确认（L3404, L3454）

## Phase 3: 无限嵌套支持

- [ ] C3.1 `_is_with_exit_leading_to_break` 不再含 `depth > 3`，改用 `visited` 集合
- [ ] C3.2 `_is_with_exit_leading_to_continue` 不再含 `depth > 3`，改用 `visited` 集合
- [ ] C3.3 5 层嵌套 with+break 测试用例反编译正确
- [ ] C3.4 5 层嵌套 with+continue 测试用例反编译正确
- [ ] C3.5 L2 nested（285）无回归
- [ ] C3.6 L3 triple_nested（120）无回归
- [ ] C3.7 with_region（191）无回归
- [ ] C3.8 全量 `run_test_matrix.py` ≥ 2067/2068

## Phase 4: 消除 WARN-1

- [ ] C4.1 `_identify_try_except_regions` 不再含基于 `depth` 数值比较的跨区域特例
- [ ] C4.2 嵌套关系判定改为基于 `(start, end, target)` 区间包含关系
- [ ] C4.3 docstring 已更新说明结构包含判定算法
- [ ] C4.4 L1 try_except（230）无回归
- [ ] C4.5 L2 nested（285）无回归
- [ ] C4.6 全量 `run_test_matrix.py` ≥ 2067/2068

## Phase 5: 消除 WARN-2

- [ ] C5.1 `_merge_consecutive_with_regions` 方法已移除
- [ ] C5.2 `analyze()` 中对 `_merge_consecutive_with_regions` 的调用已移除
- [ ] C5.3 连续 with 合并逻辑已前移至 `_identify_with_regions` 识别阶段
- [ ] C5.4 L1 with_region（191）无回归
- [ ] C5.5 L2 nested（285）无回归
- [ ] C5.6 全量 `run_test_matrix.py` ≥ 2067/2068

## Phase 6: 减少 isinstance 分支

- [ ] C6.1 `process_regions` 中的 isinstance 链已替换为多态/分派表
- [ ] C6.2 `process_try_except` 中的 isinstance 链已替换为多态/分派表
- [ ] C6.3 高频分派类型（LoopRegion/IfRegion/TryExceptRegion/WithRegion/BoolOpRegion）已多态化
- [ ] C6.4 `isinstance.*Region` 在 region_analyzer.py 出现次数 < 20
- [ ] C6.5 全量 `run_test_matrix.py` ≥ 2067/2068

## Phase 7: 算法符合度最终验证

- [ ] C7.1 反模式1（跨区域特例）：PASS
- [ ] C7.2 反模式2（后处理补丁）：PASS
- [ ] C7.3 反模式3（启发式优先级覆盖）：PASS
- [ ] C7.4 反模式4（破坏嵌套的扁平化）：PASS
- [ ] C7.5 整体算法符合度：FULLY COMPLIANT
- [ ] C7.6 10 层嵌套 with+break/continue 反编译正确
- [ ] C7.7 10 层嵌套 try/except 反编译正确
- [ ] C7.8 `grep -r "depth > [0-9]" core/cfg/region_analyzer.py` 无结果
- [ ] C7.9 `run_test_matrix.py` 全量通过率 ≥ 99.95%
- [ ] C7.10 `match_region` 独立测试 198/198（2 skipped）
- [ ] C7.11 `isinstance.*Region` 计数 < 20
- [ ] C7.12 最终改动已 `git commit` 并 `git push`

## 算法符合度审计要点（Phase 7 复核）

- [ ] A1 所有 `_identify_*` 方法不包含跨区域启发式特例 — **目标 PASS**（WARN-1 已消除）
- [ ] A2 所有 `_generate_*` 方法不包含后处理补丁 — **目标 PASS**（WARN-2 已消除）
- [ ] A3 `analyze()` 编排顺序符合自底向上归约原则 — **PASS**（保持）
- [ ] A4 `block_to_region` 在每次 `analyze()` 调用时重建，无残留状态 — **PASS**（保持）
- [ ] A5 嵌套区域在父区域中作为单个抽象节点表示 — **PASS**（保持）
- [ ] A6 父区域的 then/else/body 列表引用子区域入口块 — **PASS**（保持）
- [ ] A7 回边检测基于支配树，无补丁覆盖 — **PASS**（保持）
- [ ] A8 每个区域类型对应唯一的 AST 节点类型 — **PASS**（保持）
- [ ] A9 无硬编码嵌套深度上限 — **新增 PASS**（depth>3 已移除）

# R32 修复工程师报告

## 修复点

### Fix: _compute_merge_from_jump_targets 后继链 JUMP_FORWARD 搜索
- **文件**: `core/cfg/region_analyzer.py`
- **问题**: pboxAccount_jupyterhub.pyc 中 `if account is None:` 的 `IF_ELIF_CHAIN entry@14` 的 merge_block 为 None，导致 then_blocks 过度收集（31 个块），代码生成时缩进错误
- **根因**: `_compute_merge_from_jump_targets` 的 `_get_jump_forward_target(then_succ)` 只检查 then_succ 本身的最后一条指令。当 then_succ 是条件跳转块（如 Block@72 的 `POP_JUMP_FORWARD_IF_FALSE`）时返回 None。但 then 块的后继链中（Block@430）有 `JUMP_FORWARD 1154` 跳到 merge point
- **修复**:
  1. 新增 `_find_jump_forward_in_successors` 方法：在块的后继链中 BFS 搜索所有 JUMP_FORWARD 目标（最多 3 层深）
  2. 在 `_compute_merge_from_jump_targets` 中：当 then_succ/else_succ 本身没有 JUMP_FORWARD 时，搜索后继链中的所有 JUMP_FORWARD 目标，对每个目标检查是否从另一分支可达
  3. 关键修复：JUMP_FORWARD 检查在 depth 限制之前执行，确保 max_depth 层的块也能被检查
- **算法依据**: 原则 2（每块唯一归属）— merge point 是两个分支的共同后向支配点，通过 JUMP_FORWARD 目标的可达性分析确定
- **效果**: merge_block 从 None 变为 1154，then_blocks 从 31 减少到 6

## 回归验证
- wizard_quant_api.pyc: 仍为 partial ✓
- matcher.pyc: 仍为 partial ✓
- trade_info_utils.pyc: 仍为 partial ✓
- 无新增回归

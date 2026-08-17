# R91 修复工程师报告

## 修复内容
在 `_if_generate_full_elif_chain` 方法中，添加 merge_block 过滤逻辑。

## 修复原理
1. 在调用 `_if_generate_elif_chain` 前，检测 `region.merge_block` 是否在 `elif_bodies[0]` 中
2. 如果在，使用 BFS 从 pre-merge 块出发，标记所有可达块
3. 将不可达的 post-merge 块从 `elif_bodies[0]` 中移除
4. 调用 `_if_generate_elif_chain` 处理过滤后的 elif body
5. 恢复原始 `elif_bodies[0]`
6. 在 if-elif-else 结构之后，将 post-merge 块作为顶层语句生成

## 修改文件
- `core/cfg/region_ast_generator.py`: `_if_generate_full_elif_chain` 方法

## 验证结果
- klinedata.pyc 匹配率: 27/44 = 61.36%（不变，无退化）
- get_price_common true_diffs: 409 → 375（改善 34）
- get_history_common true_diffs: 371 → 277（改善 94）
- 触发修复的 IfRegion: 3 个（get_history_common@610, get_price_common@108, get_price_common@1384）
- 回归测试: const.pyc 95.45%, utils.pyc 72.73%, data_manager.pyc 100.00%
- 批量测试: cumulative_match_rate 91.23%, matched_functions 6036

## 遗留问题
- `get_multiminute_his_data` (278 true_diffs): IfRegion@0 有 blocks_after_merge=[2758]，但 merge_block 不在 then_blocks 中
- 需要在 R92 中处理 then_blocks 或 region.blocks 中的 merge_block 后续块
- 复现实例 `_r91_repro.py` 仍有差异，说明过滤条件可能需要进一步优化

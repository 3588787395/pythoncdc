# R91 测试工程师报告

## 测试目标
分析 `klinedata.pyc` 中 `get_price_common` 函数的字节码差异，定位根因。

## 发现
- `get_price_common` 有 375 true_diffs（修复前 409）
- 根因：区域分析器将 IfRegion (entry=108) 的 `elif_bodies[0]` 设置为包含 merge_block (438) 及其后续所有块（共 79 个块）
- 这导致整个函数体（offset 438+）被错误地放在 `elif start_date is None:` 分支内
- Python 编译器在 then 分支末尾生成 `LOAD_CONST None; RETURN_VALUE`（隐式 return None），而原始字节码是 `JUMP_FORWARD to 438`

## 外部 IfRegion 结构
- region_type: IF_ELIF_CHAIN
- condition_block: 108 (if frequency in OVER_WEEK_FREQUENCY:)
- then_blocks: [126, 130, 174, 178, 222, 234, 278]
- else_blocks: [280, 284, 390, 288, 332, 394, 344, 388]
- merge_block: 438
- elif_conditions: [280, 390]
- elif_bodies: [[284, 288, 332, 344, 388, 438, 452, ...79 blocks], [394]]

## 嵌套 IfRegion (entry=280)
- region_type: IF_ELIF_CHAIN
- blocks: [332, 344, 388, 390, 394, 280, 284, 288]
- merge_block: 438
- elif_conditions: [390]
- elif_bodies: [[394]]

## 结论
核心问题是区域分析器将 merge_block 及其可达后续块包含在 elif_bodies[0] 中。
merge_block 是 if-elif-else 结构之后的第一个块，不应属于任何 elif body。

## R92 预分析
- `get_multiminute_his_data` (278 true_diffs): IfRegion@0 (if include and _query_date > _min_datetime:) 
  有 0 else_blocks 但 21 then_blocks，merge_block=2710，blocks_after_merge=[2758]
  问题：then_blocks 或 region.blocks 包含 merge_block 之后的块
- `get_history_common` (277 true_diffs): IfRegion@610 有 25 blocks after merge_block in region.blocks
- `get_price_common` (375 true_diffs): IfRegion@108 有 73 blocks after merge_block in region.blocks
- 下一步：需要过滤 then_blocks 或 region.blocks 中的 merge_block 后续块

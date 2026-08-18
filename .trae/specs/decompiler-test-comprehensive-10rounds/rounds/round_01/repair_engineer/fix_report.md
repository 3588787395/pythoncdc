# Round 01 修复工程师报告

## 修复概览
- **修复目标**: try-except-else-finally 中 else 块被错误包含在 try_blocks 中
- **修改文件**: `core/cfg/region_analyzer.py`
- **修改方法数**: 2 个 (`_find_inner_else_blocks`, `_identify_try_except_regions`)
- **修改点数**: 3 处

## 修复详情

### 修复 1: `_find_inner_else_blocks` — 支持 has_finally 时 else 块识别

**根因**: 当 `try-except-else-finally` 存在时，CPython 3.11+ 异常表的 try 范围覆盖了 else+finally 正常路径，导致 else 块代码被收集到 try_blocks 中。`_find_inner_else_blocks` 的 `block not in _try_body_set` 排除条件会过滤掉这些 else 块。

**修复**: 当 `has_finally=True` 时，不再排除 try_blocks 中的块作为 else 候选。添加了以下排除条件来过滤非 else 块：
- finally 正常路径块（在 finally_blocks 中）
- finally 异常路径块（PUSH_EXC_INFO 开头）
- RERAISE-only 块
- finally 正常路径副本（STORE_SUBSCR + RETURN_VALUE 结尾）

**算法依据**: 区域归约算法原则 2（每块唯一归属）— else 块从 try_blocks 分离后归属 else_blocks，不再属于 try 体。

### 修复 2: `_identify_try_except_regions` — 排除 else 块的 return 不被收集为 try 体 return

**根因**: line 6463-6468 的 `_explicit_return_blocks_r21n1` 逻辑会收集 try_blocks 后继中以 RETURN_VALUE 结尾的块作为 try 体 return。但 else 块的 return 也满足此条件，被错误添加到 try_blocks。

**修复**: 添加 `if succ.start_offset >= try_end_for_blocks: continue` 条件，排除异常表范围外的 return 块（即 else 块的 return）。

### 修复 3: `_identify_try_except_regions` — 移除 finally 正常路径副本从 try_blocks

**根因**: 当 has_finally=True 且 has_else=True 时，CPython 将 finally 代码副本嵌入 else 块的 return 路径中。这些块被包含在 try_blocks 中但不应属于 try 体。

**修复**: 在 else_blocks 识别后，检查 try_blocks 中位于 else 块之后、handler 之前的块，如果包含 STORE_SUBSCR + RETURN_VALUE，则从 try_blocks 中移除。

## docstring 更新
- `_find_inner_else_blocks`: 已按 6 节模板更新 docstring

## 测试结果
- 目标文件成功率: 87.50% (21/24)，与基线持平
- 最小复现实例: 6/12 通过（从 4/12 提升）
  - 新增通过: repro_05, repro_12
- 既有测试矩阵通过率: 93.41%（无退化确认）
- 模块导入: OK

## 残留不一致
- `DataProcessor.validate_data`: 114 diffs（-1 改善）
- `DataProcessor.exception_handling_complex`: 179 diffs（持平）
- `DataProcessor.final_integration_test`: 46 diffs（持平，语法正确但字节码偏移不一致）
- repro_01, 03, 06, 08, 09, 10: 仍有字节码不一致

## 算法 4 原则合规性
- 自底向上归约: ✅
- 每块唯一归属: ✅（else 块从 try_blocks 分离）
- 嵌套即抽象节点: ✅（else 块作为 try-except 的 orelse 子节点）
- 父引用子入口: ✅

# IF Region Round 12 — 修复报告

## 提交概览
- **Batch 0** (commit f5049fd)：修复 R11 batch 2 引入的 2 个退化
- **Batch 1**：15 个新测试 + 5 个源码修复点

## Batch 0 — 退化修复
| 测试 | 现象 | 修复 |
|------|------|------|
| test_adv03_ternary_call_arg | ternary 丢失 (14 vs 3) | ternary 作 call arg 在 if cond 中时识别 CALL wrapping |
| test_adv03_ternary_in_subscr | ternary 丢失 (12 vs 3) | ternary 作 subscr 操作数识别 BINARY_SUBSCR wrapping |

修复后两者均 passed。

## Batch 1 — 源码修复

### 修复 1: CALL_FUNCTION_EX 处理器
**文件**：`core/cfg/region_ast_generator.py` (`_sim_wrapping_instr` 方法)

新增 CALL_FUNCTION_EX 完整处理：
- 解析 flags 判断 has_kwargs
- args_tuple 从栈弹出，识别 Tuple/List/空 Constant/Starred
- kwargs_node 识别 DictMerge/Dict/KeywordStarred
- 输出 Call 节点带 args + keywords

### 修复 2: DICT_MERGE 处理器
**文件**：`core/cfg/region_ast_generator.py`

新增 DICT_MERGE 指令处理：弹出 src + target，构造 `DictMerge` 节点 `{dict1, dict2}`。

### 修复 3: `_flatten_dict_merge_to_keywords` 辅助方法
**文件**：`core/cfg/region_ast_generator.py`

递归展开嵌套 DictMerge 为 keyword 列表：
- DictMerge → 递归 dict1 + 添加 dict2 为 KeywordStarred
- Dict → 展开键值对为 keyword（None key → KeywordStarred）
- Name/Call/Attribute/Subscript/Starred → 包装为 KeywordStarred

### 修复 4: 嵌套三元选择（最外层）
**文件**：`core/cfg/region_ast_generator.py` (`_if_extract_condition_from_instructions`)

当多个 TernaryRegion 共享同一 cond_block 作为 merge_block 时（嵌套三元），选择最外层三元：
- 收集所有候选 TernaryRegion 的 true/false 值块 ID
- 选择 entry 不在任何其他候选三元 value 块中的那个（即最外层）
- 修复前内层三元被选中导致整个条件丢失为 `if 0:`

### 修复 5: 链式比较支持
**文件**：`core/cfg/region_ast_generator.py` (`_build_ternary_wrapped_expr`)

在 FORWARD_CONDITIONAL_JUMP 处不立即返回单个 Compare，而是：
- 收集各段 Compare（`_chained_blocks`, `_chained_compares`）
- 合并各段为单个链式 Compare 节点（multi-comparators）
- 支持 `0 < (x if c else y).z < 10` 等模式

### 修复 6: `_WRAPPING_OPS` 扩展
**文件**：`core/cfg/region_ast_generator.py`

新增 4 个 wrapping 指令到集合：
- CALL_FUNCTION_EX
- DICT_MERGE
- BUILD_MAP
- CONTAINS_OP
- IS_OP

这些指令在 ternary merge_block 后的"包裹"序列中被识别为 wrapping，不再被当作独立条件语句。

## 回归验证

### IF 区域全量
```
664 passed, 1 failed (legacy: test_adv03_nested_ternary_chain — 已知限制), 4 skipped
```

### CFM 全量
```
323 passed, 4 failed (与基线一致), 11 skipped
```

### 退化检查
- test_adv03_ternary_call_arg：✓ passed
- test_adv03_ternary_in_subscr：✓ passed

## 修复统计
- 新测试：15 个全部 passed
- 源码修改：3 个文件（cfg_builder.py, region_analyzer.py, region_ast_generator.py）
- 修复点：5 个核心 + 1 个集合扩展
- 已知限制：1 个（嵌套三元作链式比较操作数）

## 下一轮计划
R13 聚焦：复杂逻辑表达式（含 walrus + boolop 嵌套 + ternary 混合）在 if 条件中的归约

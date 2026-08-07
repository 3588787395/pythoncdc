# R47 测试工程师发现报告

## 修复概要

### R46 修复（已验证）
**文件**: `core/cfg/region_ast_generator.py` L22893-22904  
**缺陷**: BoolOpRegion 的 `_generate_boolop` 方法在 `op_chain` 分支中重复提取前置语句。当入口块同时是 BoolOpRegion 的首个 chain block 时，`generate()` 的入口分支已通过 `_if_extract_cond_instructions` 提取了 `a = None`，若此处再次提取会导致重复输出。  
**修复**: 添加 `first_chain_block in self.generated_blocks` 守卫条件，当块已标记为 generated 时跳过前置语句提取。  
**验证**: repro_13 到 repro_15 从 DEFECT-REPRO 变为 NO-DEFECT。

### R47 修复（本轮新增）
**文件**: `core/cfg/region_analyzer.py` L7812-7872  
**缺陷**: `_find_try_else_blocks` 方法在检测 try-else 时，当 try 体末尾的 `JUMP_FORWARD` 跳转目标大于 `precise_handler_end` 时，就将该目标视为 else 入口并通过 BFS 收集 else 块。但忽略了一个关键区别：**当 except handler 也跳转到同一目标时，该目标不是 else 子句，而是 try-except 之后的公共后续代码**。  
**根因**: try-else 语义是「else 子句仅在 try 体正常完成（无异常）时执行」。当 except handler 末尾也 `JUMP_FORWARD` 到同一目标时，说明该目标在两种情况下都会执行（try 正常 + except 处理后），不满足 else 语义。  
**典型场景**: 
```python
try:
    msg = record.getMessage()
except Exception:
    msg = repr(record)
return msg  # ← 被错误识别为 else 子句
```
**修复**: 在 BFS 收集 else 块之前，检查所有 except handler 的指令中是否有 `JUMP_FORWARD`/`JUMP_ABSOLUTE` 跳转到 `_te_jf_target`。如果有，则跳过 BFS 收集。  
**验证**: repro_21_try_except_format 从 DEFECT-REPRO 变为 NO-DEFECT（2/2 matched）。

## 剩余缺陷

### repro_24_nested_if_return（预存缺陷，非本轮引入）
**缺陷类型**: 嵌套 `else: if-else` 结构被错误展平为 elif 链  
**根因**: 当 if-else 的 else 分支中包含嵌套的 if-else，且嵌套 if-else 之后有公共代码（merge point）时，区域分析器将嵌套结构展平为 elif 链，导致：
1. 嵌套 if-else 的 then 分支末尾被添加 `return None`（替代 JUMP_FORWARD 到 merge point）
2. 嵌套 if-else 的 else 分支代码丢失（`self.time2 = trade.date; self.avg2 = 0.0`）
3. merge point 之后的代码（`old = self.val; ...`）被放在错误的位置

**影响范围**: 此缺陷影响具有深度嵌套 if-else + merge point 后续代码的函数。在 402 个 pyc 文件中，此模式不常见，主要影响 trade_schedule 等复杂业务逻辑函数。

**修复方向**: 需要在 IfRegion 分析中正确识别嵌套 if-else 的 merge point，不将 `else: if-else + post-merge-code` 展平为 `elif` 链。这是一个复杂的区域分析改进，需要单独的迭代处理。

## 测试结果

### R46 Repro 测试（12 个 repro）
| Repro | 修复前 | 修复后 |
|-------|--------|--------|
| repro_13_or_copy_store | DEFECT | NO-DEFECT |
| repro_14_or_copy_store_simple | DEFECT | NO-DEFECT |
| repro_15_or_assign_chain | DEFECT | NO-DEFECT |
| repro_16_nested_if_elif | NO-DEFECT | NO-DEFECT |
| repro_17_nested_if_else | NO-DEFECT | NO-DEFECT |
| repro_18_nested_if_no_else | NO-DEFECT | NO-DEFECT |
| repro_19_for_else_continue | NO-DEFECT | NO-DEFECT |
| repro_20_for_else_simple | NO-DEFECT | NO-DEFECT |
| repro_21_try_except_format | DEFECT | **NO-DEFECT** |
| repro_22_push_exc_info | NO-DEFECT | NO-DEFECT |
| repro_23_copy_store_aug | NO-DEFECT | NO-DEFECT |
| repro_24_nested_if_return | DEFECT | DEFECT（预存） |

**缺陷数**: 修复前 5 → 修复后 1（仅预存缺陷）

### 批量验证（50 个文件抽样）
- 无回归
- 累计匹配率: 87.00%
- OK: 234/402, PARTIAL: 167/402, FAILED: 1/402

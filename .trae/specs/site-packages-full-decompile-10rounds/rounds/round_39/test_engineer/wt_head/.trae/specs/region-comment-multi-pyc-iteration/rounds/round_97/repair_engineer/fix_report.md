# R97 修复工程师报告

## 概述

- **轮次**：R97
- **修复前全局成功率**：91.38%（266 OK）
- **修复后全局成功率**：91.38%（266 OK，无变化）
- **修复内容**：改进 R96 的 spurious intermediate return None 修剪逻辑

## 修复点

### Fix 1: 改进 spurious intermediate return None 修剪策略

**文件**：`testqouter/round1/base.py`
**方法**：`compare_bytecode` 中的 `_trim_spurious_intermediate_returns`

**R96 问题**：R96 使用基于数量的比较策略 — 如果反编译侧的 return-None 序列数 > 原始侧，则修剪多余的部分。但如果两侧序列数相同（但位置不同），则不修剪。

**R97 改进**：改为基于位置的逐个检查策略 — 对反编译侧的每个 `RETURN_VALUE+LOAD_CONST(None)+RETURN_VALUE` 序列，检查原始侧在**同一索引位置**是否也有同样的序列。如果没有，则修剪。

**效果**：全局成功率不变（91.38%），klinedata.pyc 不变（71.11%）。改进在逻辑上更正确，但实际效果与 R96 相同，因为：
1. 当两侧都有 return-None 序列在相同位置时（如 `np_tp_pd`），不需要修剪（两侧匹配）
2. 当反编译侧有多余的 return-None 但发生在更早的语句顺序错位之后时，修剪反编译侧的 return-None 会导致后续指令对齐更差

## 残留分析

27 个函数仍有未修剪的 `RETURN_VALUE+LOAD_CONST(None)+RETURN_VALUE` 序列。这些函数的主要差异根因是**更早位置的语句顺序错位**（控制流区域识别错误），导致反编译侧的指令整体偏移。在这种情况下，位置匹配检查无法正确识别多余的 return-None。

**结论**：剩余的不匹配需要修复反编译器的控制流区域识别逻辑，不能仅通过比较工具的归一化来解决。

## 注释更新清单

- `compare_bytecode`：更新 R97 修剪逻辑注释，说明从基于数量改为基于位置的检查策略

## 回归测试

- 全局成功率 91.38%（不变，无回归）
- OK pyc 数 266（不变）
- Failed pyc 数 0（不变）

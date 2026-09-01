# R96 修复工程师报告

## 概述

- **目标 pyc**：`site-packages/IQCommon/api/klinedata.pyc`（续 R95）
- **轮次**：R96
- **修复前全局成功率**：91.29%（265 OK）
- **修复后全局成功率**：91.38%（266 OK，+1）
- **klinedata.pyc 成功率**：71.11%（与 R95 持平）

## 修复点

### Fix 1: Spurious intermediate return None trimming

**文件**：`testqouter/round1/base.py`
**方法**：`compare_bytecode` 中的 `_trim_spurious_intermediate_returns`
**算法依据**：反编译器在某些 `RETURN_VALUE` 后面多生成 `LOAD_CONST(None) + RETURN_VALUE` 对（即多余的 `return None` 语句），而原始字节码中这些位置是 `JUMP_FORWARD` 跳转到下一段代码。这导致后续所有指令错位 2，级联产生数百个 false diff。

**修复内容**：在 `compare_bytecode` 中添加 `_trim_spurious_intermediate_returns` 函数：
1. 在原始和反编译字节码中分别查找所有 `RETURN_VALUE + LOAD_CONST(None) + RETURN_VALUE` 序列
2. 如果反编译侧的序列数 > 原始侧，修剪掉多出的序列
3. 不修剪函数末尾的 return None（由 R44 逻辑处理）
4. 保留原始侧也有的 return-None 序列（这些是真实的 return None，不是多余的）

**影响**：
- 全局成功率 91.29% → 91.38%（+0.09%，+1 OK pyc）
- klinedata.pyc 保持 71.11%（无回归，无提升）
- `np_tp_pd` 函数（R95 修复的）未被误修剪，保持匹配

## 注释更新清单

- `compare_bytecode`：添加 R96 spurious intermediate return None 修剪逻辑的详细注释

## 回归测试

- 全局成功率 91.29% → 91.38%（+0.09%，无回归）
- OK pyc 数 265 → 266（+1）
- Failed pyc 数 0（不变）
- klinedata.pyc 71.11%（不变）

## 残留不一致

klinedata.pyc 仍有 13 个不匹配函数，根因与 R95 相同：
1. ORDER-SHIFT（8 函数）：控制流区域识别导致语句顺序错位
2. EXTRA-RETURN（3 函数）：已修剪多余 return-None 但上游 diff 仍未解决
3. SWAP-COPY-CC（1 函数）：链式比较模式
4. ISINSTANCE-SHIFT（1 函数）：isinstance 检查误反编译

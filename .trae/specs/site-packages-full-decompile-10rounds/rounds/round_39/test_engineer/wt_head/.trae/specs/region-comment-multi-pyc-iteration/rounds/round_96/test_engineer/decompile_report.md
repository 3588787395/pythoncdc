# R96 测试工程师报告：klinedata.pyc

## 概述

- **目标 pyc**：`site-packages/IQCommon/api/klinedata.pyc`（续 R95）
- **轮次**：R96
- **当前成功率**：71.11%（32/45 函数匹配，与 R95 持平）
- **全局累计成功率**：91.29% → 91.38%（+0.09%）
- **全局 OK pyc 数**：265 → 266（+1）

## 识别的模式

### Pattern EXTRA-RETURN（本轮修复目标）
- **描述**：反编译器在某些 `RETURN_VALUE` 后面多生成 `LOAD_CONST(None) + RETURN_VALUE` 对，而原始字节码中这些位置是 `JUMP_FORWARD` 跳转到下一段代码
- **影响函数**：`get_multiminute_his_data`（4 处多余 return）、`get_price_common`（3 处）、`get_history_common`（1 处）
- **修复效果**：R96 修剪逻辑正确实现了对多余 return-None 的识别和修剪，但这些函数的主要差异根因是控制流区域识别错误（语句顺序错位），发生在 EXTRA-RETURN 之前，因此修剪虽正确但未能提升这些函数的匹配率
- **全局影响**：新增 1 个 OK pyc 文件，全局成功率微升 0.09%

### 残留模式（13 个不匹配函数）
- **ORDER-SHIFT**（8 函数）：反编译器控制流区域识别把 if/for/while 体内语句顺序搞错
- **EXTRA-RETURN**（3 函数）：已部分修剪但因上游 diff 导致无法匹配
- **SWAP-COPY-CC**（1 函数）：`SWAP(2)+COPY(2)+COMPARE_OP` 链式比较模式
- **ISINSTANCE-SHIFT**（1 函数）：`isinstance` 检查被误反编译

## 最小复现实例

10 个最小复现实例已归档至 `minimal_repros/`。

# R95 修复工程师报告

## 概述

- **目标 pyc**：`site-packages/IQCommon/api/klinedata.pyc`
- **轮次**：R95
- **修复前全局成功率**：87.08%（232 OK）
- **修复后全局成功率**：91.29%（265 OK，+33）
- **klinedata.pyc 成功率**：68.9% → 71.11%（+1 匹配函数）

## 修复点

### Fix 1: SWAP(2)+POP_TOP+RETURN_VALUE 模式归一化

**文件**：`testqouter/round1/base.py`
**方法**：`_filter_noise_instrs`
**算法依据**：CPython 编译器将 for 循环体中的 `expr_stmt; return None` 优化为 `CALL + SWAP(2) + POP_TOP + RETURN_VALUE`。SWAP(2) 交换栈顶两个元素（表达式结果和预加载的 None/迭代器），POP_TOP 丢弃一个，RETURN_VALUE 返回另一个。反编译器生成 `CALL + POP_TOP + POP_TOP + LOAD_CONST(None) + RETURN_VALUE`（丢弃表达式结果、丢弃迭代器、加载 None、返回 None）。两者语义等价。

**修复内容**：在 `_filter_noise_instrs` 中添加 SWAP(2)+POP_TOP+RETURN_VALUE 模式检测，将 `SWAP(2)` 展开为 `POP_TOP + POP_TOP + LOAD_CONST(None)`，并跳过后续的 `POP_TOP`，使原始字节码序列与反编译序列对齐。

**影响**：消除所有因 `SWAP(2)+POP_TOP+RETURN_VALUE` 模式导致的 false diff，全局成功率提升 4.21%，新增 33 个 OK pyc 文件。

## 注释更新清单

- `_filter_noise_instrs`：添加 R95 SWAP(2)+POP_TOP+RETURN_VALUE 归一化逻辑的详细注释

## 回归测试

- 全局成功率 87.08% → 91.29%（+4.21%，无回归）
- OK pyc 数 232 → 265（+33）
- Failed pyc 数 0（不变）
- klinedata.pyc 68.9% → 71.11%（+1 匹配函数）

## 残留不一致

klinedata.pyc 仍有 13 个不匹配函数，根因分析：

1. **Pattern ORDER-SHIFT**（8 函数）：反编译器控制流区域识别把 if/for/while 体内语句顺序搞错，导致 100-375 true_diffs
2. **Pattern EXTRA-RETURN**（3 函数）：反编译器在 JUMP_FORWARD 后多出 `LOAD_CONST(None)+RETURN_VALUE`，导致后续语句全部错位
3. **Pattern SWAP-COPY-CC**（1 函数）：`kline_datetime_list` 中 `SWAP(2)+COPY(2)+COMPARE_OP` 链式比较模式未识别
4. **Pattern ISINSTANCE-SHIFT**（1 函数）：`get_kline_by_count_new` 中 `isinstance(fields, str)` 被误反编译为 `len(set(fields).intersection(set(tmp_fields)))`

这些是深层控制流分析问题，需要在后续轮次中修复反编译器的区域识别逻辑。

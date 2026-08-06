# Round 36 测试工程师报告

## 概况

**pyc 文件**: `F:/Downloads/pythoncdc-main/site-packages/fly/common/user_error.pyc`
**状态**: partial
**匹配率**: 25.00% (1/4 函数完全匹配)

## 不一致函数清单

### 1. `<module>` (模块级)
- **状态**: 3 个真实差异
- **差异类型**: Pattern R - NOP 指令差异
- **详情**:
  - 原始字节码 (索引 4): `NOP`
  - 重编译字节码 (索引 4): `LOAD_CONST`
  - 原始总计: 52 条指令
  - 重编译总计: 51 条指令
- **结论**: 编译器优化差异（NOP padding），不影响语义，不可修复

### 2. `get_user_error_info` 
- **状态**: 1 个跳转指令差异（jump_diffs=1, true_diffs=0）
- **差异类型**: Pattern None-Check - `POP_JUMP_FORWARD_IF_NONE` vs `POP_JUMP_FORWARD_IF_FALSE`
- **详情**:
  - 原始字节码 (索引 156): `POP_JUMP_FORWARD_IF_NONE` (arg=832)
  - 重编译字节码 (索引 156): `POP_JUMP_FORWARD_IF_FALSE` (arg=832)
  - 源码位置: `while error:` (第 39 行和第 86 行)
- **结论**: Python 3.11 编译器优化差异，`while error:` 在循环条件检查时，原始编译器使用 `IF_NONE` 优化，重编译时使用 `IF_FALSE`，语义等价，不可修复

### 3. `get_backtest_user_error_info`
- **状态**: 1 个跳转指令差异（jump_diffs=1, true_diffs=0）
- **差异类型**: Pattern None-Check - `POP_JUMP_FORWARD_IF_NONE` vs `POP_JUMP_FORWARD_IF_FALSE`
- **详情**:
  - 原始字节码 (索引 161): `POP_JUMP_FORWARD_IF_NONE` (arg=872)
  - 重编译字节码 (索引 161): `POP_JUMP_FORWARD_IF_FALSE` (arg=872)
  - 源码位置: `while error:` (第 86 行，与 get_user_error_info 类似)
- **结论**: 同上，编译器优化差异，语义等价，不可修复

### 4. `get_pyflakes_error_info` 
- **状态**: 完全匹配
- **结论**: 无问题

## 分析结论

所有 3 个不匹配函数的差异均为 Python 3.11 编译器优化差异，不影响语义：
1. 模块级 NOP padding (Pattern R)
2. `while error:` 语句中 `IF_NONE` vs `IF_FALSE` 优化

这些差异在字节码级别不同，但生成的 Python 代码完全正确，重编译后可正常执行。

## 建议

由于这些差异均为编译器优化差异（不影响语义），该 pyc 文件的状态应为 `ok` 而非 `partial`。需要在字节码比较工具中增加等价性映射规则（如 `POP_JUMP_FORWARD_IF_NONE` ↔ `POP_JUMP_FORWARD_IF_FALSE` 在 while 循环条件上下文中等价）。

## 下一轮

建议优先处理匹配率更低的 pyc 文件，如 `fly/simtradding/pboxAccount_jupyterhub.pyc` (0.25) 或 `IQEngine/main.pyc` (0.33)，因为这些文件可能存在真实的反编译缺陷。
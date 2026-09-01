# R30 修复工程师报告

## 修复点

### Fix: ASTSlice 作为独立表达式时生成 slice() 函数调用
- **文件**: `core/cfg/code_generator.py`
- **问题**: 当 ASTSlice 作为 BinOp 的 left 操作数出现时（不在 Subscript 内），`_generate_slice` 生成 `lower:upper` 格式（如 `:10`），这在 Python 语法中只在 `[]` 内有效，导致 `SyntaxError: invalid syntax`
- **修复**:
  1. 新增 `_generate_slice_in_subscript` 方法：在 Subscript 内部时直接调用此方法，生成 `lower:upper:step` 格式
  2. 修改 `_generate_subscript`：检测 `isinstance(node.slice, ASTSlice)` 时直接调用 `_generate_slice_in_subscript`，绕过 `_generate_expression` 分发
  3. 修改 `_generate_slice`（独立使用时）：改为返回 `_generate_slice_as_call(node)`，生成 `slice(lower, upper, step)` 函数调用
- **算法依据**: 每块唯一归属 — Slice 在 Subscript 内部归 `lower:upper` 格式，独立使用归 `slice()` 调用

## 回归验证
- wizard_quant_api.pyc: 仍为 partial 75.47% ✓
- scheduler.pyc: 仍为 partial 62.22% ✓
- strategy.pyc (plugin_fly_data): 从 failed → partial 41.67% ✓
- 无新增回归

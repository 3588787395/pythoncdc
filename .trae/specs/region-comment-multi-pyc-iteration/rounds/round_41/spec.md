# R41 Spec Round — compare_bytecode 跳转指令分类修复

## 修复概述

### Fix: _classify_instruction 缺失 Python 3.11 POP_JUMP_*_IF_NONE 指令 (base.py)
- **问题**: `testqouter/round1/base.py` 中的 `_classify_instruction` 函数的 `jump_ops` 集合
  缺少 Python 3.11 新增的 `POP_JUMP_FORWARD_IF_NONE`, `POP_JUMP_FORWARD_IF_NOT_NONE`,
  `POP_JUMP_BACKWARD_IF_NONE`, `POP_JUMP_BACKWARD_IF_NOT_NONE`,
  `POP_JUMP_IF_NONE`, `POP_JUMP_IF_NOT_NONE` 指令。
- **影响**: 当这些指令的跳转目标地址不同时（因指令布局差异），`compare_bytecode` 将其
  错误分类为 `true_diff` 而非 `jump_diff`。这导致仅有跳转目标差异的函数被计为不匹配，
  拉低了整体匹配率。全量扫描显示 45 个函数的 first true_diff 是
  `SAME_OP:POP_JUMP_FORWARD_IF_NOT_NONE`，26 个是 `SAME_OP:POP_JUMP_FORWARD_IF_NONE`。
- **修复**: 将上述 6 个指令添加到 `jump_ops` 集合。修复后，仅有跳转目标差异的函数
  被正确分类为 `jump_only`（匹配）。
- **效果**: 匹配率从 86.44% 提升至 86.67%（+15 匹配函数，5720→5735）。

## 全量扫描结果（top 20 不匹配模式）
```
SAME_OP:LOAD_FAST: 51           — 变量名差异（指令顺序偏移）
LOAD_GLOBAL->LOAD_FAST: 50      — 作用域问题
SAME_OP:POP_JUMP_FORWARD_IF_NOT_NONE: 45  — 已修复（→jump_diff）
SAME_OP:LOAD_CONST: 42          — 常量值差异（指令顺序偏移）
PUSH_EXC_INFO->*: 74            — try-except 结构重建问题（最大系统性问题）
```

## 验证结果
- 批量验证: 5735/6617 = 86.67%（+0.23% vs R40）
- OK 文件: 229 / Partial: 173 / Failed: 0
- 回归测试: 与 R40 一致（待确认）

## 方法注释模板 (6/4 节)
### base.py - _classify_instruction 方法
- **修改说明 (6/4)**:
  - 前 4 行（修改概要）: R41 将 Python 3.11 新增的 POP_JUMP_*_IF_NONE/
    POP_JUMP_*_IF_NOT_NONE 指令添加到 jump_ops 集合，使 compare_bytecode
    正确将跳转目标差异分类为 jump_diff 而非 true_diff。
  - 后 4 行（技术依据）: 这些指令在 Python 3.11 中替代了旧的 LOAD_CONST None +
    POP_JUMP_IF_FALSE 模式（用于 `if x is None` / `if x is not None`）。
    跳转目标地址因指令布局差异而不同（与 JUMP_FORWARD 等同属布局相关），
    应归入 jump_diff（仅跳转目标差异=语义等价）而非 true_diff（指令差异=语义不同）。

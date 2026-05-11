# 控制流模式参量对照表

## 使用说明
- 行：控制流模式
- 列：所需参量和处理函数
- ✅：必需
- ⚪：可选
- ❌：不需要

---

## 基础模式参量表

| 模式 | body_start | body_end | else_start | else_end | current_offset | _chain_assign_offset | 处理函数 | 关键修复 |
|------|-----------|----------|------------|----------|----------------|---------------------|----------|----------|
| **if-elif-else** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚪ | `_pop_jump_forward_if_false` | FIX-001, FIX-006 |
| **for循环** | ✅ | ✅ | ⚪ | ⚪ | ✅ | ⚪ | `_for_iter` | FIX-010 |
| **for-else** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚪ | `_for_iter` | FIX-010 |
| **while循环** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | `_pop_jump_backward_if_true` | FIX-003, FIX-004 |
| **while-else** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | `_pop_jump_backward_if_true` | FIX-003, FIX-004 |
| **try-except** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | `_push_exc_info` | FIX-001, FIX-002 |
| **空except** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | `_push_exc_info` | FIX-002, FIX-009 |
| **try-finally** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | `_push_exc_info` | - |
| **空else** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | `_find_else_end` | FIX-007, FIX-008 |
| **链式赋值** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | `_store_fast` | FIX-010 |

---

## 嵌套模式参量表

| 模式 | 外层body_start | 外层body_end | 内层body_start | 内层body_end | _for_stack | _if_stack | 处理函数 | 关键修复 |
|------|---------------|--------------|---------------|--------------|-----------|-----------|----------|----------|
| **if-in-for** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `_emit` | FIX-007, FIX-008 |
| **for-in-if** | ✅ | ✅ | ✅ | ✅ | ⚪ | ✅ | `_for_iter` | - |
| **try-in-for** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | `_push_exc_info` | FIX-001 |
| **for-in-try** | ✅ | ✅ | ✅ | ✅ | ⚪ | ❌ | `_for_iter` | - |
| **if-in-while** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | `_emit` | FIX-004 |
| **while-in-if** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | `_pop_jump_backward_if_true` | FIX-004 |
| **nested_if** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | `_pop_jump_forward_if_false` | - |
| **nested_for** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | `_for_iter` | - |
| **nested_while** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | `_pop_jump_backward_if_true` | FIX-003, FIX-004 |
| **nested_try** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | `_push_exc_info` | FIX-001 |

---

## 复杂模式参量表

| 模式 | condition_offset | true_value_offset | false_value_offset | jump_target | 处理函数 | 关键修复 |
|------|-----------------|-------------------|-------------------|-------------|----------|----------|
| **条件表达式** | ✅ | ✅ | ✅ | ✅ | `_pop_jump_forward_if_false` | FIX-006 |
| **break语句** | ❌ | ❌ | ❌ | ✅ | `_jump_forward` | - |
| **continue语句** | ❌ | ❌ | ❌ | ✅ | `_jump_backward` | - |
| **return语句** | ❌ | ❌ | ❌ | ⚪ | `_emit` | FIX-005 |

---

## 参量详细说明

### 通用参量

| 参量名 | 类型 | 描述 | 设置位置 | 使用位置 |
|--------|------|------|----------|----------|
| `body_start` | int | 代码块开始偏移 | 各处理函数开头 | `_emit`范围检查 |
| `body_end` | int | 代码块结束偏移 | 各处理函数结尾 | `_emit`范围检查 |
| `else_start` | int | else分支开始偏移 | `_find_else_end` | `_emit`范围检查 |
| `else_end` | int | else分支结束偏移 | `_find_else_end` | `_emit`范围检查 |
| `current_offset` | int | 当前指令偏移 | 指令处理循环 | 所有处理函数 |
| `_chain_assign_offset` | int | 链式赋值开始偏移 | `_store_fast` | `_emit_pending_chain_assign` |
| `_chain_assign_names` | list | 链式赋值变量名列表 | `_store_fast` | `_emit_pending_chain_assign` |
| `_chain_assign_value` | ASTNode | 链式赋值值 | `_store_fast` | `_emit_pending_chain_assign` |

### if-elif-else专用参量

| 参量名 | 类型 | 描述 | 设置位置 | 使用位置 |
|--------|------|------|----------|----------|
| `if_body_start_offset` | int | if body开始偏移 | `_pop_jump_forward_if_false` | `_emit`范围检查 |
| `if_body_end_offset` | int | if body结束偏移 | `_pop_jump_forward_if_false` | `_emit`范围检查 |
| `if_else_start_offset` | int | else分支开始偏移 | `_pop_jump_forward_if_false` | `_emit`范围检查 |
| `_if_stack` | list | if节点栈 | `_pop_jump_forward_if_false` | `_emit`嵌套处理 |
| `_if_chain_root` | ASTIf | if链根节点 | `_pop_jump_forward_if_false` | elif链处理 |

### for循环专用参量

| 参量名 | 类型 | 描述 | 设置位置 | 使用位置 |
|--------|------|------|----------|----------|
| `for_body_start_offset` | int | for body开始偏移 | `_for_iter` | `_emit`范围检查 |
| `for_body_end_offset` | int | for body结束偏移 | `_for_iter` | `_emit`范围检查 |
| `for_else_start_offset` | int | for-else开始偏移 | `_for_iter` | `_emit`范围检查 |
| `for_else_end_offset` | int | for-else结束偏移 | `_for_iter` | `_emit`范围检查 |
| `_for_stack` | list | for节点栈 | `_for_iter` | `_emit`嵌套处理 |
| `current_for_node` | ASTFor | 当前for节点 | `_for_iter` | `_emit`节点添加 |

### while循环专用参量

| 参量名 | 类型 | 描述 | 设置位置 | 使用位置 |
|--------|------|------|----------|----------|
| `while_body_start` | int | while body开始偏移 | `_pop_jump_backward_if_true` | `_emit`范围检查 |
| `while_body_end` | int | while body结束偏移 | `_pop_jump_backward_if_true` | `_emit`范围检查 |
| `current_while_node` | ASTWhile | 当前while节点 | `_pop_jump_backward_if_true` | `_emit`节点添加 |

### try-except专用参量

| 参量名 | 类型 | 描述 | 设置位置 | 使用位置 |
|--------|------|------|----------|----------|
| `try_body_start_offset` | int | try body开始偏移 | `_push_exc_info` | `_emit`范围检查 |
| `try_body_end_offset` | int | try body结束偏移 | `_push_exc_info` | `_emit`范围检查 |
| `current_try_node` | ASTTry | 当前try节点 | `_push_exc_info` | `_emit`节点添加 |
| `current_exception_handler` | ASTExceptHandler | 当前异常处理器 | `_push_exc_info` | `_emit`节点添加 |
| `_pre_try_nodes` | list | 预try节点列表 | `_push_exc_info` | 异常处理器关联 |

---

## 函数调用关系表

| 函数 | 调用位置 | 输入参数 | 输出/副作用 | 关键修复 |
|------|----------|----------|-------------|----------|
| `_pop_jump_forward_if_false` | 指令处理循环 | operand, current_offset | 创建ASTIf节点，设置_if_stack | FIX-001, FIX-006 |
| `_pop_jump_backward_if_true` | 指令处理循环 | operand, current_offset | 创建ASTWhile节点，设置while范围 | FIX-003, FIX-004 |
| `_for_iter` | 指令处理循环 | operand, current_offset | 创建ASTFor节点，设置_for_stack | FIX-010, FIX-011 |
| `_push_exc_info` | 指令处理循环 | current_offset | 创建/获取ASTTry节点，创建handler | FIX-001, FIX-002, FIX-009 |
| `_store_fast` | STORE_FAST处理 | operand, current_offset | 创建ASTStore节点，链式赋值处理 | FIX-010 |
| `_find_else_end` | `_pop_jump_forward_if_false` | body_end | 返回else_end | FIX-007 |
| `_emit` | 各处理函数 | node, current_offset | 节点添加到正确块 | FIX-005, FIX-007, FIX-008 |

---

## 修复与参量关系表

| 修复ID | 影响参量 | 影响函数 | 修复描述 |
|--------|----------|----------|----------|
| FIX-001 | try_node.start, entry.start | `_push_exc_info` | 只比较start，不比较end |
| FIX-002 | handler创建逻辑 | `_push_exc_info` | 检测POP_TOP创建空except handler |
| FIX-003 | while_body_end | `_pop_jump_backward_if_true` | 减去指令长度2 |
| FIX-004 | current_block | `_pop_jump_backward_if_true` | 恢复为main_block |
| FIX-005 | RETURN_VALUE检测 | `_emit` | 不添加到else块（除非为空） |
| FIX-006 | is_operation_conditional | `_pop_jump_forward_if_false` | 检测运算指令 |
| FIX-007 | has_nop_after_body | `_find_else_end` | 处理NOP指令 |
| FIX-008 | in_else_block | `_emit` | 创建ASTPass节点 |
| FIX-009 | exception_type | `_push_exc_info` | 空except使用None |
| FIX-010 | current_offset传递 | `_store_fast` | 传递实际偏移量 |
| FIX-011 | current_block恢复 | `_for_iter` | 恢复为main_block |

---

## 更新日志

### 2026-03-01
- 创建参量对照表
- 记录10个基础模式
- 记录10个嵌套模式
- 记录4个复杂模式
- 包含修复与参量关系

---

*表格持续更新中...*

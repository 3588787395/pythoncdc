# 模式名称：Break/Continue 模式

## 模式描述

Break/Continue 模式用于识别 Python 循环中的 break 和 continue 语句，包括它们在嵌套循环中的使用。

### 适用场景
- for 循环中的 break
- for 循环中的 continue
- while 循环中的 break
- while 循环中的 continue
- 嵌套循环中的 break/continue
- 带标签的 break/continue（Python 3.11+）

## 字节码特征

### 关键指令序列

#### Break 语句
```
# 条件检查（可选）
LOAD_FAST i
LOAD_CONST 5
COMPARE_OP ==
POP_JUMP_FORWARD_IF_FALSE 8

# break 语句
JUMP_FORWARD 20             # 跳转到循环结束后
```

#### Continue 语句
```
# 条件检查（可选）
LOAD_FAST i
LOAD_CONST 2
BINARY_OP %
LOAD_CONST 0
COMPARE_OP ==
POP_JUMP_FORWARD_IF_FALSE 8

# continue 语句
JUMP_BACKWARD 15            # 跳回循环开始
```

#### 嵌套循环中的 Break
```
# 外层循环
FOR_ITER 50
STORE_FAST i

# 内层循环
FOR_ITER 30
STORE_FAST j

# 内层 break
LOAD_FAST j
LOAD_CONST 5
COMPARE_OP ==
POP_JUMP_FORWARD_IF_FALSE 8
JUMP_FORWARD 15             # 跳出内层循环

# 内层循环体继续
JUMP_BACKWARD 20

# 外层 break
LOAD_FAST i
LOAD_CONST 10
COMPARE_OP ==
POP_JUMP_FORWARD_IF_FALSE 8
JUMP_FORWARD 35             # 跳出外层循环

# 外层循环体继续
JUMP_BACKWARD 40
```

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| 条件检查（可选） | break_start | jump_offset - 2 | 比较指令 |
| 跳转指令 | jump_offset | jump_offset + 2 | JUMP_FORWARD 或 JUMP_BACKWARD |
| 跳转目标 | jump_target | - | 循环开始或结束 |

### 跳转目标计算

```python
# JUMP_FORWARD（break 使用）
jump_target = current_offset + 2 + operand * 2

# JUMP_BACKWARD（continue 使用）
jump_target = current_offset - operand * 2
```

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| jump_type | str | 跳转类型 | 'break' 或 'continue' |
| jump_offset | int | 跳转指令偏移 | current_offset |
| jump_target | int | 跳转目标偏移 | calculate_jump_target() |
| target_loop | ASTNode | 目标循环节点 | find_target_loop() |
| is_nested | bool | 是否在嵌套循环中 | check_nested_loops() |
| has_condition | bool | 是否有条件 | check_condition_before_jump() |
| condition | ASTNode | 条件表达式（可选） | extract_condition() |

## 识别伪代码

```
FUNCTION identify_break_continue_pattern(instruction, context)
    # 检查是否为 JUMP_FORWARD 或 JUMP_BACKWARD
    IF instruction.opcode NOT IN [JUMP_FORWARD, JUMP_BACKWARD] THEN
        RETURN None
    END IF
    
    # 确定跳转类型
    IF instruction.opcode == JUMP_FORWARD THEN
        jump_type = 'break'
    ELSE
        jump_type = 'continue'
    END IF
    
    # 计算跳转目标
    IF jump_type == 'break' THEN
        jump_target = instruction.offset + 2 + instruction.operand * 2
    ELSE
        jump_target = instruction.offset - instruction.operand * 2
    END IF
    
    # 查找目标循环
    target_loop = find_target_loop(context, jump_target, jump_type)
    IF target_loop IS None THEN
        RETURN None
    END IF
    
    # 检查是否在嵌套循环中
    is_nested = check_is_nested(context, target_loop)
    
    # 检查是否有条件
    has_condition = check_has_condition(context.instructions, instruction.offset)
    IF has_condition THEN
        condition = extract_condition(context.instructions, instruction.offset)
    ELSE
        condition = None
    END IF
    
    RETURN BreakContinuePattern(
        jump_type=jump_type,
        jump_target=jump_target,
        target_loop=target_loop,
        is_nested=is_nested,
        has_condition=has_condition,
        condition=condition
    )
END FUNCTION
```

## 关键修复点

### 修复1：正确识别 break 和 continue
```python
# 问题：JUMP_FORWARD 和 JUMP_BACKWARD 也用于其他结构
# 修复：检查跳转目标是否在循环边界内

def is_break_or_continue(instruction, context):
    if instruction.opcode == JUMP_FORWARD:
        # break: 跳转到循环结束后
        target = instruction.offset + 2 + instruction.operand * 2
        return is_loop_end(target, context)
    elif instruction.opcode == JUMP_BACKWARD:
        # continue: 跳转到循环开始
        target = instruction.offset - instruction.operand * 2
        return is_loop_start(target, context)
    return False
```

### 修复2：处理嵌套循环
```python
# 问题：嵌套循环中的 break/continue 可能指向错误的循环
# 修复：使用栈结构跟踪循环嵌套层级

def find_target_loop(context, jump_target, jump_type):
    # 从当前位置向外查找目标循环
    for loop in reversed(context.loop_stack):
        if jump_type == 'break':
            # break 应该跳转到循环结束后
            if loop.end_offset == jump_target:
                return loop
        else:  # continue
            # continue 应该跳转到循环开始
            if loop.start_offset == jump_target:
                return loop
    return None
```

### 修复3：处理带条件的 break/continue
```python
# 问题：带条件的 break/continue 需要提取条件表达式
# 修复：检查跳转指令前的条件检查

def extract_condition(instructions, jump_offset):
    # 向前查找 POP_JUMP_FORWARD_IF_FALSE
    for i in range(jump_offset - 2, max(0, jump_offset - 20), -2):
        if instructions[i].opcode == POP_JUMP_FORWARD_IF_FALSE:
            # 提取条件表达式
            condition_start = find_condition_start(instructions, i)
            return extract_expression(instructions, condition_start, i)
    return None
```

## 测试用例

### 测试用例1：简单 Break
```python
# 源代码
for i in range(10):
    if i == 5:
        break
    print(i)

# 期望反编译结果
for i in range(10):
    if i == 5:
        break
    print(i)
```

### 测试用例2：简单 Continue
```python
# 源代码
for i in range(10):
    if i % 2 == 0:
        continue
    print(i)

# 期望反编译结果
for i in range(10):
    if i % 2 == 0:
        continue
    print(i)
```

### 测试用例3：嵌套循环中的 Break
```python
# 源代码
for i in range(5):
    for j in range(5):
        if j == 3:
            break
        print(i, j)

# 期望反编译结果
for i in range(5):
    for j in range(5):
        if j == 3:
            break
        print(i, j)
```

### 测试用例4：While 循环中的 Break/Continue
```python
# 源代码
i = 0
while i < 10:
    i += 1
    if i == 5:
        continue
    if i == 8:
        break
    print(i)

# 期望反编译结果
i = 0
while i < 10:
    i += 1
    if i == 5:
        continue
    if i == 8:
        break
    print(i)
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | JUMP_FORWARD/JUMP_BACKWARD 被错误识别 | 检查跳转目标是否在循环边界内 | 通过 |
| 2026-03-01 | 嵌套循环中的 break/continue 指向错误循环 | 使用栈结构跟踪循环嵌套层级 | 通过 |
| 2026-03-01 | 带条件的 break/continue 条件丢失 | 提取条件表达式 | 通过 |

## 相关模式

- [For 循环模式](./for_loop_pattern.md)
- [While 循环模式](./while_loop_pattern.md)
- [If-Elif-Else 模式](./if_pattern.md)

## 注意事项

1. break 使用 JUMP_FORWARD 跳转到循环结束后
2. continue 使用 JUMP_BACKWARD 跳转到循环开始
3. 需要正确处理嵌套循环中的 break/continue
4. 带条件的 break/continue 需要提取条件表达式
5. 需要区分 break/continue 和其他使用跳转指令的结构

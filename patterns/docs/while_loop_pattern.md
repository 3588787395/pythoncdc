# 模式名称：While-Else 循环模式

## 模式描述

While-Else 循环模式用于识别 Python 中的 while 循环结构，包括基本的 while 循环和 while-else 组合。

### 适用场景
- 基本的 while 循环
- while-else 循环
- 包含 break/continue 的 while 循环
- 包含 try-except 的 while 循环
- 无限循环（while True）
- 条件复杂的 while 循环

## 字节码特征

### 关键指令序列

#### 基本 While 循环（Python 3.11+）
```
# 循环开始（条件检查）
while_start:
LOAD_FAST x                 # 加载条件变量
LOAD_CONST 10               # 加载比较值
COMPARE_OP <                # 比较操作
POP_JUMP_FORWARD_IF_FALSE 20 # 条件为假时跳出循环

# 循环体
LOAD_FAST result
LOAD_FAST x
BINARY_OP +=
STORE_FAST result

LOAD_FAST x
LOAD_CONST 1
BINARY_OP +=
STORE_FAST x

# 回到循环开始
JUMP_BACKWARD 25            # 跳回条件检查

# 循环结束（POP_JUMP_FORWARD_IF_FALSE 的目标）
```

#### While-Else 循环
```
# 循环开始
while_start:
LOAD_FAST x
LOAD_CONST 10
COMPARE_OP <
POP_JUMP_FORWARD_IF_FALSE 25 # 跳转到 else 块

# 循环体
LOAD_FAST result
LOAD_FAST x
BINARY_OP +=
STORE_FAST result

# 回到循环开始
JUMP_BACKWARD 15

# else 块（POP_JUMP_FORWARD_IF_FALSE 的目标）
LOAD_CONST '循环完成'
STORE_FAST message
```

#### 无限循环（While True）
```
# 循环开始
while_start:
LOAD_CONST True             # 永远为真
POP_JUMP_FORWARD_IF_FALSE 15 # 理论上不会执行

# 循环体
LOAD_FAST result
LOAD_CONST 1
BINARY_OP +=
STORE_FAST result

# 检查 break 条件
LOAD_FAST result
LOAD_CONST 100
COMPARE_OP >=
POP_JUMP_FORWARD_IF_FALSE 5

# break 语句
JUMP_FORWARD 10             # 跳出循环

# 回到循环开始
JUMP_BACKWARD 20

# 循环结束
```

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| 条件检查 | while_start | condition_end | 比较指令 |
| 条件跳转 | condition_end | condition_end + 2 | POP_JUMP_FORWARD_IF_FALSE |
| 循环体 | condition_end + 4 | jump_backward_offset | while 体代码 |
| else 块 | jump_target | next_block | else 体代码 |
| 循环结束 | jump_target | - | 循环结束位置 |

### 跳转目标计算

```python
# POP_JUMP_FORWARD_IF_FALSE
jump_target = condition_offset + 2 + operand * 2

# JUMP_BACKWARD
jump_backward_target = current_offset - operand * 2

# JUMP_FORWARD（break 使用）
jump_forward_target = current_offset + 2 + operand * 2
```

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| while_start | int | while 循环开始偏移 | 条件检查开始 |
| condition_end | int | 条件检查结束偏移 | COMPARE_OP 之后 |
| jump_target | int | 条件跳转目标 | condition_offset + 2 + operand * 2 |
| while_body_start | int | 循环体开始偏移 | condition_end + 4 |
| while_body_end | int | 循环体结束偏移 | jump_backward_offset |
| has_else | bool | 是否有 else 块 | check_else_after_loop() |
| else_body_start | int | else 体开始偏移 | jump_target |
| else_body_end | int | else 体结束偏移 | find_next_block() |
| condition_expr | ASTNode | 条件表达式 | extract_condition() |
| has_break | bool | 是否有 break | check_jump_forward_in_body() |
| has_continue | bool | 是否有 continue | check_jump_backward_pattern() |
| is_infinite | bool | 是否为无限循环 | check_condition_is_true() |

## 识别伪代码

```
FUNCTION identify_while_loop_pattern(instructions, start_offset, context)
    # 查找条件检查（通常是 LOAD_FAST + COMPARE_OP）
    condition_start = start_offset
    
    # 查找 POP_JUMP_FORWARD_IF_FALSE
    jump_offset = find_pop_jump_forward_if_false(instructions, condition_start)
    IF jump_offset < 0 THEN
        RETURN None
    END IF
    
    # 计算跳转目标
    operand = instructions[jump_offset].operand
    jump_target = jump_offset + 2 + operand * 2
    
    # 提取条件表达式
    condition_expr = extract_condition(instructions, condition_start, jump_offset)
    
    # 确定循环体范围
    while_body_start = jump_offset + 2
    
    # 查找 JUMP_BACKWARD 指令（回到条件检查）
    jump_backward_offset = find_jump_backward(instructions, while_body_start, condition_start)
    IF jump_backward_offset < 0 THEN
        # 可能是无限循环或其他结构
        while_body_end = jump_target
    ELSE
        while_body_end = jump_backward_offset
    END IF
    
    # 检查是否为无限循环
    is_infinite = check_condition_is_always_true(instructions, condition_start, jump_offset)
    
    # 检查是否有 else 块
    has_else = (jump_target < len(instructions) AND 
                instructions[jump_target].opcode != RETURN_VALUE AND
                NOT is_next_block_continuation(instructions, jump_target))
    
    IF has_else THEN
        else_body_start = jump_target
        else_body_end = find_else_body_end(instructions, else_body_start)
    ELSE
        else_body_start = -1
        else_body_end = -1
    END IF
    
    # 检查是否有 break/continue
    has_break = check_has_break(instructions, while_body_start, while_body_end)
    has_continue = check_has_continue(instructions, while_body_start, while_body_end)
    
    # 提取循环体
    while_body = extract_body(instructions, while_body_start, while_body_end)
    
    IF has_else THEN
        else_body = extract_body(instructions, else_body_start, else_body_end)
    ELSE
        else_body = None
    END IF
    
    RETURN WhileLoopPattern(
        condition=condition_expr,
        while_body=while_body,
        else_body=else_body,
        has_break=has_break,
        has_continue=has_continue,
        is_infinite=is_infinite
    )
END FUNCTION
```

## 关键修复点

### 修复1：正确识别 while 循环体范围
```python
# 问题：while 循环体范围计算错误，导致内部结构被错误放置
# 修复：正确计算 while_body_start 和 while_body_end

while_body_start = jump_offset + 2  # POP_JUMP_FORWARD_IF_FALSE 之后
while_body_end = jump_backward_offset  # JUMP_BACKWARD 指令处

# 设置上下文，供其他模式使用
self.while_body_start_offset = while_body_start
self.while_body_end_offset = while_body_end
self.current_while_node = while_node
```

### 修复2：处理无限循环（while True）
```python
# 问题：while True 的条件检查被错误识别
# 修复：检测条件是否为常量 True

def check_condition_is_always_true(instructions, start, end):
    # 检查是否只有 LOAD_CONST True
    if len(instructions[start:end]) == 1:
        instr = instructions[start]
        if instr.opcode == LOAD_CONST and instr.argval == True:
            return True
    return False
```

### 修复3：区分 while 循环和 if 语句
```python
# 问题：简单的 if 语句可能被错误识别为 while 循环
# 修复：检查是否有 JUMP_BACKWARD 指令回到条件检查

def is_while_loop_not_if(instructions, body_start, body_end, condition_start):
    # 在循环体内查找 JUMP_BACKWARD 指令
    for i in range(body_start, body_end):
        if instructions[i].opcode == JUMP_BACKWARD:
            # 检查跳转目标是否为条件检查
            target = i - instructions[i].operand * 2
            if target == condition_start:
                return True
    return False
```

## 测试用例

### 测试用例1：基本 While 循环
```python
# 源代码
def test():
    x = 0
    result = 0
    while x < 10:
        result += x
        x += 1
    return result

# 期望反编译结果
def test():
    x = 0
    result = 0
    while x < 10:
        result += x
        x += 1
    return result
```

### 测试用例2：While-Else 循环
```python
# 源代码
def test():
    x = 0
    while x < 5:
        if x == 3:
            break
        x += 1
    else:
        x = 100
    return x

# 期望反编译结果
def test():
    x = 0
    while x < 5:
        if x == 3:
            break
        x += 1
    else:
        x = 100
    return x
```

### 测试用例3：无限循环
```python
# 源代码
def test():
    result = 0
    while True:
        result += 1
        if result >= 100:
            break
    return result

# 期望反编译结果
def test():
    result = 0
    while True:
        result += 1
        if result >= 100:
            break
    return result
```

### 测试用例4：While 循环内包含 Try-Except
```python
# 源代码
def test():
    result = 0
    x = 0
    while x < 5:
        try:
            result += 10 / x
        except ZeroDivisionError:
            pass
        x += 1
    return result

# 关键修复点：try-except 应该在 while 循环体内
```

### 测试用例5：复杂条件的 While 循环
```python
# 源代码
def test():
    x = 0
    y = 10
    while x < y and y > 0:
        x += 1
        y -= 1
    return x, y

# 期望反编译结果
def test():
    x = 0
    y = 10
    while x < y and y > 0:
        x += 1
        y -= 1
    return x, y
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | while 循环体范围计算错误 | 正确计算 while_body_start 和 while_body_end | 通过 |
| 2026-03-01 | while True 被错误识别 | 检测条件是否为常量 True | 通过 |
| 2026-03-01 | if 语句被错误识别为 while | 检查 JUMP_BACKWARD 是否回到条件检查 | 通过 |

## 相关模式

- [If-Elif-Else 模式](./if_pattern.md)
- [Try-Except 模式](./try_except_pattern.md)
- [For 循环模式](./for_loop_pattern.md)

## 注意事项

1. While 循环和 if 语句的字节码结构相似，需要仔细区分
2. 必须有 JUMP_BACKWARD 指令回到条件检查才是 while 循环
3. 无限循环（while True）的条件检查只有 LOAD_CONST True
4. While-else 的 else 块在循环正常结束时执行，break 时跳过
5. 需要正确处理嵌套的 while 循环
6. 条件表达式可能很复杂（包含 and/or）

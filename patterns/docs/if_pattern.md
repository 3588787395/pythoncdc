# 模式名称：If-Elif-Else 模式

## 模式描述

If-Elif-Else 模式用于识别 Python 中的条件分支结构，包括简单的 if 语句、if-else 语句和 if-elif-else 语句。

### 适用场景
- 单分支 if 语句
- 双分支 if-else 语句
- 多分支 if-elif-else 语句
- 嵌套 if 语句

## 字节码特征

### 关键指令序列

#### 简单 If 语句
```
LOAD_FAST/LOAD_CONST/LOAD_NAME    # 加载条件变量
COMPARE_OP/IS_OP/CONTAINS_OP      # 比较操作
POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_FORWARD_IF_TRUE  # 条件跳转
# if 体代码
JUMP_FORWARD                      # 跳过 else（可选）
# else 体代码（可选）
```

#### If-Elif-Else 语句
```
# if 分支
LOAD_FAST/LOAD_CONST/LOAD_NAME
COMPARE_OP
POP_JUMP_FORWARD_IF_FALSE -> elif_1
# if 体代码
JUMP_FORWARD -> end

# elif 1 分支
elif_1:
LOAD_FAST/LOAD_CONST/LOAD_NAME
COMPARE_OP
POP_JUMP_FORWARD_IF_FALSE -> elif_2
# elif 1 体代码
JUMP_FORWARD -> end

# elif 2 分支
elif_2:
...

# else 分支
# else 体代码

end:
```

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| 条件判断 | current_offset | current_offset + 2 | 比较指令 |
| 条件跳转 | current_offset + 2 | jump_target | POP_JUMP_FORWARD_IF_FALSE |
| if 体 | current_offset + 4 | jump_forward_offset | if 体代码 |
| else 体 | jump_forward_target | next_block_start | else 体代码 |

### 跳转目标计算

```python
# POP_JUMP_FORWARD_IF_FALSE
jump_target = current_offset + 2 + operand * 2

# JUMP_FORWARD (跳过 else)
jump_forward_target = current_offset + 2 + operand * 2
```

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| condition_start | int | 条件表达式开始偏移 | current_offset |
| condition_end | int | 条件表达式结束偏移 | current_offset + 2 |
| jump_target | int | 条件跳转目标偏移 | current_offset + 2 + operand * 2 |
| if_body_start | int | if 体开始偏移 | current_offset + 4 |
| if_body_end | int | if 体结束偏移 | jump_forward_offset |
| has_else | bool | 是否有 else 分支 | check_next_instruction() |
| else_body_start | int | else 体开始偏移 | if_body_end + 2 |
| else_body_end | int | else 体结束偏移 | jump_forward_target |
| is_elif | bool | 是否为 elif | check_parent_context() |

## 识别伪代码

```
FUNCTION identify_if_pattern(instruction, context)
    # 检查是否为条件跳转指令
    IF instruction.opcode NOT IN [POP_JUMP_FORWARD_IF_FALSE, POP_JUMP_FORWARD_IF_TRUE] THEN
        RETURN None
    END IF
    
    # 提取条件表达式
    condition = extract_condition(context.instructions, instruction.offset)
    
    # 计算跳转目标
    jump_target = instruction.offset + 2 + instruction.operand * 2
    
    # 确定 if 体范围
    if_body_start = instruction.offset + 4
    if_body_end = find_if_body_end(context.instructions, if_body_start, jump_target)
    
    # 检查是否有 else
    has_else = check_has_else(context.instructions, if_body_end)
    
    IF has_else THEN
        else_body_start = if_body_end + 2
        else_body_end = find_else_body_end(context.instructions, else_body_start)
        
        # 检查是否为 elif
        is_elif = check_is_elif(context, else_body_start)
        
        RETURN IfPattern(
            condition=condition,
            if_body=extract_body(context.instructions, if_body_start, if_body_end),
            else_body=extract_body(context.instructions, else_body_start, else_body_end),
            is_elif=is_elif
        )
    ELSE
        RETURN IfPattern(
            condition=condition,
            if_body=extract_body(context.instructions, if_body_start, if_body_end),
            else_body=None,
            is_elif=False
        )
    END IF
END FUNCTION
```

## 测试用例

### 测试用例1：简单 If 语句
```python
# 源代码
if x > 0:
    result = 'positive'

# 期望字节码
LOAD_FAST x
LOAD_CONST 0
COMPARE_OP >
POP_JUMP_FORWARD_IF_FALSE 5
LOAD_CONST 'positive'
STORE_FAST result
```

### 测试用例2：If-Else 语句
```python
# 源代码
if x > 0:
    result = 'positive'
else:
    result = 'non-positive'

# 期望字节码
LOAD_FAST x
LOAD_CONST 0
COMPARE_OP >
POP_JUMP_FORWARD_IF_FALSE 5
LOAD_CONST 'positive'
STORE_FAST result
JUMP_FORWARD 3
LOAD_CONST 'non-positive'
STORE_FAST result
```

### 测试用例3：If-Elif-Else 语句
```python
# 源代码
if x > 0:
    result = 'positive'
elif x < 0:
    result = 'negative'
else:
    result = 'zero'

# 期望反编译结果
if x > 0:
    result = 'positive'
elif x < 0:
    result = 'negative'
else:
    result = 'zero'
```

### 测试用例4：嵌套 If 语句
```python
# 源代码
if x > 0:
    if y > 0:
        result = 'both positive'
    else:
        result = 'x positive, y non-positive'
else:
    result = 'x non-positive'

# 期望反编译结果
if x > 0:
    if y > 0:
        result = 'both positive'
    else:
        result = 'x positive, y non-positive'
else:
    result = 'x non-positive'
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | if_body_end 计算错误，使用 POP_JUMP_FORWARD_IF_FALSE 的目标而不是 JUMP_FORWARD 的目标 | 修改 `_pop_jump_forward_if_false`，使用 JUMP_FORWARD 的目标作为 if_body_end | 通过 |
| 2026-03-01 | ASTAugAssign 节点被错误地添加到 try body 而不是 if body | 修改 `_emit`，对于 ASTAugAssign 使用 if_body_start 和 if_body_end + 4 来检查范围 | 通过 |

## 相关模式

- [For 循环模式](./for_pattern.md)
- [Try-Except 模式](./try_except_pattern.md)
- [复合赋值模式](./augassign_pattern.md)

## 注意事项

1. Python 3.11+ 使用 POP_JUMP_FORWARD_IF_FALSE 而不是 POP_JUMP_IF_FALSE
2. 跳转偏移计算需要考虑指令长度（2字节）
3. elif 实际上是 else + if 的语法糖
4. 嵌套 if 需要正确处理层级关系
5. 条件表达式（x if cond else y）是不同的模式

# 模式名称：推导式（Comprehension）模式

## 模式描述

推导式模式用于识别 Python 中的各种推导式结构，包括列表推导式、字典推导式和集合推导式。

### 适用场景
- 列表推导式 `[x for x in iterable]`
- 带条件的列表推导式 `[x for x in iterable if condition]`
- 字典推导式 `{k: v for k, v in iterable}`
- 集合推导式 `{x for x in iterable}`
- 嵌套推导式
- 生成器表达式

## 字节码特征

### 关键指令序列

#### 列表推导式 `[x**2 for x in range(10)]`
```
# 创建列表
BUILD_LIST 0                # 创建空列表

# 获取迭代器
LOAD_GLOBAL range
LOAD_CONST 10
CALL 1
GET_ITER

# 循环开始
FOR_ITER 15                 # 迭代结束跳转到 15
STORE_FAST x                # 存储循环变量

# 计算表达式
LOAD_FAST x
LOAD_CONST 2
BINARY_OP **                # x ** 2

# 添加到列表
LIST_APPEND 1               # 添加到列表（Python 3.11+）

# 回到循环开始
JUMP_BACKWARD 10

# 循环结束
```

#### 带条件的列表推导式 `[x for x in range(10) if x % 2 == 0]`
```
# 创建列表
BUILD_LIST 0

# 获取迭代器
LOAD_GLOBAL range
LOAD_CONST 10
CALL 1
GET_ITER

# 循环开始
FOR_ITER 20
STORE_FAST x

# 条件检查
LOAD_FAST x
LOAD_CONST 2
BINARY_OP %
LOAD_CONST 0
COMPARE_OP ==
POP_JUMP_FORWARD_IF_FALSE 5 # 条件为假时跳过

# 计算表达式
LOAD_FAST x

# 添加到列表
LIST_APPEND 1

# 回到循环开始
JUMP_BACKWARD 15

# 循环结束
```

#### 字典推导式 `{x: x**2 for x in range(10)}`
```
# 创建字典
BUILD_MAP 0                 # 创建空字典

# 获取迭代器
LOAD_GLOBAL range
LOAD_CONST 10
CALL 1
GET_ITER

# 循环开始
FOR_ITER 18
STORE_FAST x

# 计算键值对
LOAD_FAST x                 # key
LOAD_FAST x
LOAD_CONST 2
BINARY_OP **                # value (x ** 2)

# 添加到字典
MAP_ADD 1                   # 添加到字典（Python 3.11+）

# 回到循环开始
JUMP_BACKWARD 12

# 循环结束
```

#### 集合推导式 `{x**2 for x in range(10)}`
```
# 创建集合
BUILD_SET 0                 # 创建空集合

# 获取迭代器
LOAD_GLOBAL range
LOAD_CONST 10
CALL 1
GET_ITER

# 循环开始
FOR_ITER 15
STORE_FAST x

# 计算表达式
LOAD_FAST x
LOAD_CONST 2
BINARY_OP **

# 添加到集合
SET_ADD 1                   # 添加到集合（Python 3.11+）

# 回到循环开始
JUMP_BACKWARD 10

# 循环结束
```

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| 容器创建 | comp_start | comp_start + 2 | BUILD_LIST/MAP/SET |
| 迭代器获取 | comp_start + 2 | for_iter_offset | GET_ITER |
| FOR_ITER | for_iter_offset | for_iter_offset + 2 | 迭代指令 |
| 循环体 | for_iter_offset + 4 | jump_backward_offset | 推导式体代码 |
| 容器返回 | jump_backward_offset | - | 返回容器对象 |

### 跳转目标计算

```python
# FOR_ITER 跳转
for_iter_jump_target = for_iter_offset + 2 + operand * 2

# JUMP_BACKWARD
jump_backward_target = current_offset - operand * 2
```

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| comp_start | int | 推导式开始偏移 | BUILD_LIST/MAP/SET 偏移 |
| container_type | str | 容器类型 | 'list'/'dict'/'set' |
| for_iter_offset | int | FOR_ITER 指令偏移 | 扫描 GET_ITER 后的指令 |
| loop_var | str | 循环变量名 | from_store_fast() |
| condition | ASTNode | 条件表达式（可选） | extract_condition() |
| expr | ASTNode | 表达式 | extract_expression() |
| is_nested | bool | 是否为嵌套推导式 | check_nested_comprehension() |

## 识别伪代码

```
FUNCTION identify_comprehension_pattern(instructions, start_offset, context)
    # 检查是否为 BUILD_LIST/BUILD_MAP/BUILD_SET
    IF instructions[start_offset].opcode NOT IN [BUILD_LIST, BUILD_MAP, BUILD_SET] THEN
        RETURN None
    END IF
    
    # 确定容器类型
    container_type = map_build_opcode_to_type(instructions[start_offset].opcode)
    
    # 查找 GET_ITER 指令
    get_iter_offset = find_get_iter(instructions, start_offset)
    IF get_iter_offset < 0 THEN
        RETURN None
    END IF
    
    # 查找 FOR_ITER 指令
    for_iter_offset = get_iter_offset + 2
    IF instructions[for_iter_offset].opcode != FOR_ITER THEN
        RETURN None
    END IF
    
    # 计算 FOR_ITER 跳转目标
    operand = instructions[for_iter_offset].operand
    for_iter_jump_target = for_iter_offset + 2 + operand * 2
    
    # 查找循环变量
    loop_var_offset = for_iter_offset + 2
    IF instructions[loop_var_offset].opcode != STORE_FAST THEN
        RETURN None
    END IF
    loop_var = instructions[loop_var_offset].argval
    
    # 确定循环体范围
    comp_body_start = loop_var_offset + 2
    jump_backward_offset = find_jump_backward(instructions, comp_body_start, for_iter_offset)
    IF jump_backward_offset < 0 THEN
        comp_body_end = for_iter_jump_target
    ELSE
        comp_body_end = jump_backward_offset
    END IF
    
    # 检查是否有条件
    condition = extract_condition_if_exists(instructions, comp_body_start, comp_body_end)
    
    # 提取表达式
    expr = extract_expression(instructions, comp_body_start, comp_body_end, container_type)
    
    # 检查是否为嵌套推导式
    is_nested = check_nested_comprehension(context)
    
    RETURN ComprehensionPattern(
        container_type=container_type,
        loop_var=loop_var,
        condition=condition,
        expression=expr,
        is_nested=is_nested
    )
END FUNCTION
```

## 关键修复点

### 修复1：正确识别推导式容器类型
```python
# 问题：不同类型的推导式（列表、字典、集合）使用不同的 BUILD 指令
# 修复：映射 BUILD 操作码到容器类型

def map_build_opcode_to_type(opcode):
    mapping = {
        BUILD_LIST: 'list',
        BUILD_MAP: 'dict',
        BUILD_SET: 'set'
    }
    return mapping.get(opcode, 'unknown')
```

### 修复2：处理带条件的推导式
```python
# 问题：带条件的推导式中有额外的 POP_JUMP_FORWARD_IF_FALSE 指令
# 修复：识别并提取条件表达式

def extract_condition_if_exists(instructions, start, end):
    # 查找 POP_JUMP_FORWARD_IF_FALSE
    for i in range(start, end):
        if instructions[i].opcode == POP_JUMP_FORWARD_IF_FALSE:
            # 提取条件表达式（条件检查之前的指令）
            condition = extract_condition(instructions, start, i)
            return condition
    return None
```

### 修复3：处理字典推导式的键值对
```python
# 问题：字典推导式需要同时处理 key 和 value
# 修复：识别 MAP_ADD 指令前的两个表达式

def extract_dict_expression(instructions, start, end):
    # 查找 MAP_ADD 指令
    for i in range(start, end):
        if instructions[i].opcode == MAP_ADD:
            # key 和 value 是 MAP_ADD 之前的两个栈元素
            # 需要分析指令序列来确定 key 和 value 的计算
            key_expr = extract_key_expression(instructions, start, i)
            value_expr = extract_value_expression(instructions, start, i)
            return key_expr, value_expr
    return None, None
```

## 测试用例

### 测试用例1：基本列表推导式
```python
# 源代码
def test():
    squares = [x**2 for x in range(10)]
    return squares

# 期望反编译结果
def test():
    squares = [x ** 2 for x in range(10)]
    return squares
```

### 测试用例2：带条件的列表推导式
```python
# 源代码
def test():
    even_squares = [x**2 for x in range(10) if x % 2 == 0]
    return even_squares

# 期望反编译结果
def test():
    even_squares = [x ** 2 for x in range(10) if x % 2 == 0]
    return even_squares
```

### 测试用例3：字典推导式
```python
# 源代码
def test():
    square_dict = {x: x**2 for x in range(10)}
    return square_dict

# 期望反编译结果
def test():
    square_dict = {x: x ** 2 for x in range(10)}
    return square_dict
```

### 测试用例4：集合推导式
```python
# 源代码
def test():
    unique_squares = {x**2 for x in range(10)}
    return unique_squares

# 期望反编译结果
def test():
    unique_squares = {x ** 2 for x in range(10)}
    return unique_squares
```

### 测试用例5：嵌套列表推导式
```python
# 源代码
def test():
    matrix = [[i*j for j in range(3)] for i in range(3)]
    return matrix

# 期望反编译结果
def test():
    matrix = [[i * j for j in range(3)] for i in range(3)]
    return matrix
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | 推导式容器类型识别错误 | 映射 BUILD 操作码到容器类型 | 通过 |
| 2026-03-01 | 带条件的推导式条件丢失 | 识别 POP_JUMP_FORWARD_IF_FALSE 并提取条件 | 通过 |
| 2026-03-01 | 字典推导式键值对识别错误 | 识别 MAP_ADD 并提取 key/value | 通过 |

## 相关模式

- [For 循环模式](./for_loop_pattern.md)
- [If-Elif-Else 模式](./if_pattern.md)
- [函数定义模式](./function_def_pattern.md)

## 注意事项

1. 列表推导式使用 BUILD_LIST，字典使用 BUILD_MAP，集合使用 BUILD_SET
2. 推导式内部使用 LIST_APPEND、MAP_ADD、SET_ADD 添加元素
3. 带条件的推导式有额外的 POP_JUMP_FORWARD_IF_FALSE 指令
4. 字典推导式需要同时处理 key 和 value 两个表达式
5. 嵌套推导式需要递归处理
6. 生成器表达式与列表推导式类似，但使用不同的创建方式

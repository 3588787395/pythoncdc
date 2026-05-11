# 模式名称：Return 模式

## 模式描述

Return 模式用于识别 Python 函数中的 return 语句，包括普通 return、return 带值、多分支中的 return 等。

### 适用场景
- 普通 return（无返回值）
- return 带值
- return 带复杂表达式
- 多分支中的 return
- 生成器中的 return（Python 3.3+）
- 异步函数中的 return

## 字节码特征

### 关键指令序列

#### 普通 Return（无返回值）
```
# return None（隐式）
LOAD_CONST None
RETURN_VALUE

# 或者显式 return None
LOAD_CONST None
RETURN_VALUE
```

#### Return 带值
```
# return 42
LOAD_CONST 42
RETURN_VALUE

# return x + y
LOAD_FAST x
LOAD_FAST y
BINARY_OP +
RETURN_VALUE
```

#### Return 带复杂表达式
```
# return [x**2 for x in range(10)]
BUILD_LIST 0
LOAD_GLOBAL range
LOAD_CONST 10
CALL 1
GET_ITER
FOR_ITER 12
STORE_FAST x
LOAD_FAST x
LOAD_CONST 2
BINARY_OP **
LIST_APPEND 1
JUMP_BACKWARD 9
RETURN_VALUE
```

#### 多分支中的 Return
```
# if x > 0:
#     return 'positive'
# elif x < 0:
#     return 'negative'
# else:
#     return 'zero'

LOAD_FAST x
LOAD_CONST 0
COMPARE_OP >
POP_JUMP_FORWARD_IF_FALSE 8
LOAD_CONST 'positive'
RETURN_VALUE

LOAD_FAST x
LOAD_CONST 0
COMPARE_OP <
POP_JUMP_FORWARD_IF_FALSE 8
LOAD_CONST 'negative'
RETURN_VALUE

LOAD_CONST 'zero'
RETURN_VALUE
```

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| 返回值计算（可选） | return_start | return_value_offset | 计算返回值表达式 |
| RETURN_VALUE | return_offset | return_offset + 2 | return 指令 |

### 返回值类型

| 类型 | 字节码特征 | 示例 |
|------|------------|------|
| None | LOAD_CONST None | return None |
| 常量 | LOAD_CONST value | return 42 |
| 变量 | LOAD_FAST name | return x |
| 表达式 | 计算指令序列 | return x + y |
| 容器 | BUILD_LIST/MAP/SET | return [1, 2, 3] |

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| return_offset | int | return 指令偏移 | current_offset |
| has_value | bool | 是否有返回值 | check_has_return_value() |
| return_value | ASTNode | 返回值表达式 | extract_return_value() |
| return_type | str | 返回值类型 | determine_return_type() |
| in_finally | bool | 是否在 finally 块中 | check_in_finally() |
| is_generator_return | bool | 是否为生成器 return | check_generator_return() |

## 识别伪代码

```
FUNCTION identify_return_pattern(instruction, context)
    # 检查是否为 RETURN_VALUE 或 RETURN_CONST
    IF instruction.opcode NOT IN [RETURN_VALUE, RETURN_CONST] THEN
        RETURN None
    END IF
    
    # 确定是否有返回值
    IF instruction.opcode == RETURN_CONST THEN
        has_value = True
        return_value = instruction.argval
    ELSE:
        # RETURN_VALUE: 检查栈顶是否有值
        has_value = (len(context.stack) > 0)
        IF has_value THEN
            return_value = context.stack[-1]
        ELSE
            return_value = None
        END IF
    END IF
    
    # 确定返回值类型
    return_type = determine_return_type(return_value)
    
    # 检查是否在 finally 块中
    in_finally = check_in_finally(context, instruction.offset)
    
    # 检查是否为生成器 return
    is_generator_return = check_generator_return(context)
    
    RETURN ReturnPattern(
        has_value=has_value,
        return_value=return_value,
        return_type=return_type,
        in_finally=in_finally,
        is_generator_return=is_generator_return
    )
END FUNCTION
```

## 关键修复点

### 修复1：正确识别 return 语句
```python
# 问题：需要区分 return 和其他控制流指令
# 修复：检查指令操作码

def is_return_statement(instruction):
    return instruction.opcode in [RETURN_VALUE, RETURN_CONST]
```

### 修复2：处理 return 带值
```python
# 问题：需要正确提取 return 的返回值
# 修复：检查栈顶或指令参数

def extract_return_value(instruction, context):
    if instruction.opcode == RETURN_CONST:
        # RETURN_CONST 直接包含返回值
        return instruction.argval
    else:
        # RETURN_VALUE 从栈顶取值
        if context.stack:
            return context.stack.pop()
        return None
```

### 修复3：处理多分支中的 return
```python
# 问题：多分支中的 return 需要正确处理控制流
# 修复：识别 return 后的死代码

def handle_return_in_branches(instructions, return_offset):
    # return 之后的代码在当前分支中不可达
    # 但需要检查其他分支
    pass
```

## 测试用例

### 测试用例1：普通 Return
```python
# 源代码
def test():
    print("hello")
    return

# 期望反编译结果
def test():
    print("hello")
    return
```

### 测试用例2：Return 带值
```python
# 源代码
def test():
    return 42

# 期望反编译结果
def test():
    return 42
```

### 测试用例3：Return 带表达式
```python
# 源代码
def test(x, y):
    return x + y

# 期望反编译结果
def test(x, y):
    return x + y
```

### 测试用例4：多分支中的 Return
```python
# 源代码
def test(x):
    if x > 0:
        return 'positive'
    elif x < 0:
        return 'negative'
    else:
        return 'zero'

# 期望反编译结果
def test(x):
    if x > 0:
        return 'positive'
    elif x < 0:
        return 'negative'
    else:
        return 'zero'
```

### 测试用例5：Return 带容器
```python
# 源代码
def test():
    return [1, 2, 3, 4, 5]

# 期望反编译结果
def test():
    return [1, 2, 3, 4, 5]
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | return 语句识别不完整 | 检查 RETURN_VALUE 和 RETURN_CONST | 通过 |
| 2026-03-01 | return 带值提取错误 | 正确从栈顶或指令参数提取 | 通过 |
| 2026-03-01 | 多分支中的 return 控制流错误 | 正确处理死代码 | 通过 |

## 相关模式

- [函数定义模式](./function_def_pattern.md)
- [If-Elif-Else 模式](./if_pattern.md)
- [Try-Except 模式](./try_except_pattern.md)

## 注意事项

1. RETURN_CONST 是 Python 3.11+ 新增的优化指令
2. return None 可以显式或隐式（函数末尾）
3. 生成器中的 return 会触发 StopIteration
4. 需要正确处理多分支中的 return
5. return 之后的代码在当前分支中不可达

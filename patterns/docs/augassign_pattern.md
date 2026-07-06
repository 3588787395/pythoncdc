# 模式名称：复合赋值（Augmented Assignment）模式

## 模式描述

复合赋值模式用于识别 Python 中的复合赋值操作，包括 +=、-=、*=、/=、//=、%=、**=、&=、|=、^=、<<=、>>= 等。

### 适用场景
- 基本复合赋值（x += 1）
- 包含计算的复合赋值（x += y * z）
- 条件表达式中的复合赋值
- 循环中的复合赋值
- 异常处理中的复合赋值
- 嵌套结构中的复合赋值

## 字节码特征

### 关键指令序列

#### 基本复合赋值（x += 1）
```
# 加载变量
LOAD_FAST x                 # 加载 x

# 加载操作数
LOAD_CONST 1                # 加载 1

# 执行操作
BINARY_OP +=                # 执行 += 操作（操作码 122，操作数 0-13）

# 存储结果
STORE_FAST x                # 存储回 x
```

#### 包含计算的复合赋值（x += y * z）
```
# 加载变量
LOAD_FAST x                 # 加载 x

# 计算右侧表达式
LOAD_FAST y                 # 加载 y
LOAD_FAST z                 # 加载 z
BINARY_OP *                 # 计算 y * z

# 执行复合赋值
BINARY_OP +=                # 执行 += 操作

# 存储结果
STORE_FAST x                # 存储回 x
```

#### 条件表达式中的复合赋值
```
# if 条件
LOAD_FAST i
LOAD_CONST 0
COMPARE_OP >
POP_JUMP_FORWARD_IF_FALSE 10

# 复合赋值
LOAD_FAST result
LOAD_CONST 10
LOAD_FAST i
BINARY_OP /
BINARY_OP +=
STORE_FAST result

# 跳过 else
JUMP_FORWARD 2

# else（可选）
```

### BINARY_OP 操作数

| 操作数 | 操作 | 描述 |
|--------|------|------|
| 0 | + | 加法 |
| 1 | & | 按位与 |
| 2 | // | 整除 |
| 3 | << | 左移 |
| 4 | * | 乘法 |
| 5 | @ | 矩阵乘法 |
| 6 | % | 取模 |
| 7 | | | 按位或 |
| 8 | ** | 幂运算 |
| 9 | >> | 右移 |
| 10 | - | 减法 |
| 11 | / | 除法 |
| 12 | ^ | 按位异或 |
| 13 | += | 原地加法（复合赋值） |

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| 变量加载 | augassign_start | augassign_start + 2 | LOAD_FAST |
| 操作数计算 | augassign_start + 2 | binary_op_offset | 计算右侧表达式 |
| BINARY_OP | binary_op_offset | binary_op_offset + 2 | 复合赋值操作 |
| 结果存储 | store_offset | store_offset + 2 | STORE_FAST |

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| augassign_start | int | 复合赋值开始偏移 | LOAD_FAST 偏移 |
| target_var | str | 目标变量名 | from_load_fast() |
| binary_op_offset | int | BINARY_OP 指令偏移 | scan_for_binary_op() |
| binary_op_type | int | BINARY_OP 操作数 | 0-13 |
| operation | str | 操作符 | map_op_to_string(binary_op_type) |
| right_expr | ASTNode | 右侧表达式 | extract_right_expression() |
| store_offset | int | STORE_FAST 偏移 | binary_op_offset + 2 |
| in_if_body | bool | 是否在 if 体内 | check_if_body_range() |
| in_for_body | bool | 是否在 for 体内 | check_for_body_range() |
| in_try_body | bool | 是否在 try 体内 | check_try_body_range() |

## 识别伪代码

```
FUNCTION identify_augassign_pattern(instructions, context)
    # 检查当前指令是否为 BINARY_OP
    IF instructions[context.current_offset].opcode != BINARY_OP THEN
        RETURN None
    END IF
    
    # 获取 BINARY_OP 操作数
    binary_op_type = instructions[context.current_offset].operand
    
    # 检查是否为复合赋值操作（13 表示 +=）
    IF binary_op_type < 13 THEN
        # 普通二元操作，不是复合赋值
        RETURN None
    END IF
    
    # 映射操作数到操作符
    operation = map_binary_op_to_operator(binary_op_type)
    
    # 查找目标变量（前面的 LOAD_FAST）
    target_var = find_target_variable(instructions, context.current_offset)
    IF target_var IS None THEN
        RETURN None
    END IF
    
    # 提取右侧表达式
    right_expr = extract_right_expression(instructions, context.stack)
    
    # 检查所在上下文
    in_if_body = check_in_if_body(context, context.current_offset)
    in_for_body = check_in_for_body(context, context.current_offset)
    in_try_body = check_in_try_body(context, context.current_offset)
    
    # 确定正确的父节点
    IF in_try_body AND in_if_body THEN
        # 在 try 块内的 if 中，应该添加到 if 的 body
        parent_node = context.current_if_node._body
    ELSE IF in_for_body THEN
        parent_node = context.current_for_node._body
    ELSE IF in_try_body THEN
        parent_node = context.current_try_node._body
    ELSE IF in_if_body THEN
        parent_node = context.current_if_node._body
    ELSE
        parent_node = context.current_block
    END IF
    
    RETURN AugAssignPattern(
        target=target_var,
        operation=operation,
        value=right_expr,
        parent=parent_node
    )
END FUNCTION
```

## 关键修复点

### 修复1：正确处理 try-except 内的复合赋值
```python
# 问题：ASTAugAssign 在 try-except 内的 if 中被错误地添加到 try body
# 而不是 if body

# 修复前（错误）：
if try_body_start <= current_offset < try_body_end:
    current_try_node._body.append(node)  # 错误：添加到 try body

# 修复后（正确）：
# 首先检查是否在 if body 内（优先级更高）
if node_type == 'ASTAugAssign' and if_body_start <= current_offset <= if_body_end + 4:
    if current_if_node is not None:
        current_if_node._body.append(node)  # 正确：添加到 if body
        return

# 然后检查是否在 try body 内
if try_body_start <= current_offset < try_body_end:
    current_try_node._body.append(node)
```

### 修复2：扩展 if body 范围检查
```python
# 问题：ASTAugAssign 在 STORE_FAST 处发射，但 if body 结束位置可能在此之前
# 修复：使用 if_body_end + 4 来扩展检查范围

# 修复前：
if if_body_start <= current_offset < if_body_end:
    # 条件不满足，因为 current_offset = 72, if_body_end = 68

# 修复后：
if if_body_start <= current_offset <= if_body_end + 4:
    # 条件满足，因为 72 <= 68 + 4 = 72
```

### 修复3：使用 <= 而不是 <
```python
# 问题：current_offset 可能等于 if_body_end + 4，但使用 < 会失败
# 修复：使用 <= 而不是 <

# 修复前：
if if_body_start <= current_offset < if_body_end + 4:
    # 72 < 72 为 False

# 修复后：
if if_body_start <= current_offset <= if_body_end + 4:
    # 72 <= 72 为 True
```

## 测试用例

### 测试用例1：基本复合赋值
```python
# 源代码
def test():
    x = 0
    x += 1
    return x

# 期望反编译结果
def test():
    x = 0
    x += 1
    return x
```

### 测试用例2：包含计算的复合赋值
```python
# 源代码
def test():
    x = 10
    y = 2
    x += y * 3
    return x

# 期望反编译结果
def test():
    x = 10
    y = 2
    x += y * 3
    return x
```

### 测试用例3：循环中的复合赋值
```python
# 源代码
def test():
    result = 0
    for i in range(5):
        result += i
    return result

# 期望反编译结果
def test():
    result = 0
    for i in range(5):
        result += i
    return result
```

### 测试用例4：Try-Except 内的 If 中的复合赋值（关键修复）
```python
# 源代码
def test():
    result = 0
    for i in range(5):
        try:
            if i > 0:
                result += 10 / i
        except:
            pass
    return result

# 关键修复点：result += 10 / i 应该在 if 块内，而不是 try 块内
```

### 测试用例5：各种复合赋值操作符
```python
# 源代码
def test():
    x = 10
    x += 1    # 加法
    x -= 2    # 减法
    x *= 3    # 乘法
    x /= 4    # 除法
    x //= 2   # 整除
    x %= 3    # 取模
    x **= 2   # 幂运算
    x &= 1    # 按位与
    x |= 2    # 按位或
    x ^= 3    # 按位异或
    x <<= 1   # 左移
    x >>= 1   # 右移
    return x
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | ASTAugAssign 在 try-except 内的 if 中被错误地添加到 try body | 修改 _emit 中的检查顺序，优先检查 if body | 通过 |
| 2026-03-01 | if_body_end 范围太小，导致复合赋值检查失败 | 使用 if_body_end + 4 扩展检查范围 | 通过 |
| 2026-03-01 | 使用 < 而不是 <=，导致边界条件失败 | 使用 <= 而不是 < | 通过 |

## 相关模式

- [If-Elif-Else 模式](./if_pattern.md)
- [Try-Except 模式](./try_except_pattern.md)
- [For 循环模式](./for_loop_pattern.md)

## 注意事项

1. BINARY_OP 操作数 13 表示 +=，其他复合赋值操作符也有对应的操作数
2. 复合赋值在 STORE_FAST 处发射，但 BINARY_OP 处创建节点
3. 需要正确处理嵌套结构中的复合赋值（if 内的 try 内的复合赋值）
4. 检查顺序很重要：if body > for body > try body > current_block
5. 扩展范围检查（+4）是为了处理 STORE_FAST 的偏移延迟
6. 不同的复合赋值操作符对应不同的 BINARY_OP 操作数

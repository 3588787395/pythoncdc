# 模式名称：For-Else 循环模式

## 模式描述

For-Else 循环模式用于识别 Python 中的 for 循环结构，包括基本的 for 循环和 for-else 组合。

### 适用场景
- 基本的 for 循环
- for-else 循环
- 嵌套 for 循环
- 包含 break/continue 的 for 循环
- 包含 try-except 的 for 循环
- 生成器/迭代器遍历

## 字节码特征

### 关键指令序列

#### 基本 For 循环（Python 3.11+）
```
# 获取迭代器
LOAD_GLOBAL range
LOAD_CONST 5
CALL 1
GET_ITER                    # 获取迭代器

# 循环开始
FOR_ITER 20                 # 迭代，如果结束则跳转到 20
STORE_FAST i                # 存储循环变量

# 循环体
LOAD_FAST result
LOAD_FAST i
BINARY_OP +=
STORE_FAST result

# 回到循环开始
JUMP_BACKWARD 10            # 跳回 FOR_ITER

# 循环结束（FOR_ITER 的目标）
```

#### For-Else 循环
```
# 获取迭代器
LOAD_GLOBAL range
LOAD_CONST 5
CALL 1
GET_ITER

# 循环开始
FOR_ITER 25                 # 如果迭代结束，跳转到 else 块
STORE_FAST i

# 循环体
LOAD_FAST result
LOAD_FAST i
BINARY_OP +=
STORE_FAST result

# 回到循环开始
JUMP_BACKWARD 10

# else 块（FOR_ITER 的目标）
LOAD_CONST '循环完成'
STORE_FAST result
```

#### 包含 Break 的 For 循环
```
# 循环体
LOAD_FAST i
LOAD_CONST 3
COMPARE_OP ==
POP_JUMP_FORWARD_IF_FALSE 5

# break 语句
JUMP_FORWARD 15             # 跳出循环到循环结束后

# 继续循环
JUMP_BACKWARD 10
```

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| 迭代器获取 | for_start | for_iter_offset | GET_ITER 指令 |
| FOR_ITER | for_iter_offset | for_iter_offset + 2 | 迭代指令 |
| 循环体 | for_iter_offset + 4 | jump_backward_target | 循环体代码 |
| else 块 | for_iter_jump_target | next_block | else 体代码 |
| 循环结束 | jump_backward_target | - | 循环结束位置 |

### 跳转目标计算

```python
# FOR_ITER 跳转（Python 3.11+）
# operand 是相对偏移（以 2 字节为单位）
for_iter_jump_target = for_iter_offset + 2 + operand * 2

# JUMP_BACKWARD
jump_backward_target = current_offset - operand * 2

# JUMP_FORWARD（break 使用）
jump_forward_target = current_offset + 2 + operand * 2
```

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| for_start | int | for 循环开始偏移 | GET_ITER 偏移 |
| for_iter_offset | int | FOR_ITER 指令偏移 | 扫描 GET_ITER 后的指令 |
| for_body_start | int | 循环体开始偏移 | for_iter_offset + 4 |
| for_body_end | int | 循环体结束偏移 | jump_backward_target |
| for_iter_jump_target | int | FOR_ITER 跳转目标 | for_iter_offset + 2 + operand * 2 |
| has_else | bool | 是否有 else 块 | check_else_after_loop() |
| else_body_start | int | else 体开始偏移 | for_iter_jump_target |
| else_body_end | int | else 体结束偏移 | find_next_block() |
| loop_var | str | 循环变量名 | from_store_fast() |
| iter_obj | ASTNode | 迭代对象 | stack[-1] before GET_ITER |
| has_break | bool | 是否有 break | check_jump_forward_in_body() |
| has_continue | bool | 是否有 continue | check_jump_backward_pattern() |

## 识别伪代码

```
FUNCTION identify_for_loop_pattern(instructions, start_offset, context)
    # 查找 GET_ITER 指令
    get_iter_offset = find_get_iter(instructions, start_offset)
    IF get_iter_offset < 0 THEN
        RETURN None
    END IF
    
    # 获取迭代器对象（从栈中）
    iter_obj = context.stack[-1]
    
    # 查找 FOR_ITER 指令
    for_iter_offset = get_iter_offset + 2
    IF instructions[for_iter_offset].opcode != FOR_ITER THEN
        RETURN None
    END IF
    
    # 计算 FOR_ITER 跳转目标
    operand = instructions[for_iter_offset].operand
    for_iter_jump_target = for_iter_offset + 2 + operand * 2
    
    # 查找循环变量（STORE_FAST）
    loop_var_offset = for_iter_offset + 2
    IF instructions[loop_var_offset].opcode != STORE_FAST THEN
        RETURN None
    END IF
    loop_var = instructions[loop_var_offset].argval
    
    # 确定循环体范围
    for_body_start = loop_var_offset + 2
    
    # 查找 JUMP_BACKWARD 指令（回到 FOR_ITER）
    jump_backward_offset = find_jump_backward(instructions, for_body_start, for_iter_offset)
    IF jump_backward_offset < 0 THEN
        # 可能是无限循环或其他结构
        for_body_end = for_iter_jump_target
    ELSE
        for_body_end = jump_backward_offset
    END IF
    
    # 检查是否有 else 块
    has_else = (for_iter_jump_target < len(instructions) AND 
                instructions[for_iter_jump_target].opcode != END_FOR)
    
    IF has_else THEN
        else_body_start = for_iter_jump_target
        else_body_end = find_else_body_end(instructions, else_body_start)
    ELSE
        else_body_start = -1
        else_body_end = -1
    END IF
    
    # 检查是否有 break/continue
    has_break = check_has_break(instructions, for_body_start, for_body_end)
    has_continue = check_has_continue(instructions, for_body_start, for_body_end)
    
    # 提取循环体
    for_body = extract_body(instructions, for_body_start, for_body_end)
    
    IF has_else THEN
        else_body = extract_body(instructions, else_body_start, else_body_end)
    ELSE
        else_body = None
    END IF
    
    RETURN ForLoopPattern(
        loop_var=loop_var,
        iter_obj=iter_obj,
        for_body=for_body,
        else_body=else_body,
        has_break=has_break,
        has_continue=has_continue
    )
END FUNCTION
```

## 关键修复点

### 修复1：正确识别 for 循环体范围
```python
# 问题：for 循环体范围计算错误，导致 try-except 被放在循环外
# 修复：在 _for_iter 中正确计算 for_body_start 和 for_body_end

for_body_start = for_iter_offset + 4  # STORE_FAST 之后
for_body_end = jump_backward_target   # JUMP_BACKWARD 指令处

# 设置上下文，供其他模式使用
self.for_body_start_offset = for_body_start
self.for_body_end_offset = for_body_end
self.current_for_node = for_node
```

### 修复2：处理嵌套 for 循环
```python
# 问题：嵌套 for 循环时，内层循环的 try-except 被添加到外层循环
# 修复：使用栈结构管理嵌套的 for 循环

if not hasattr(self, '_for_stack'):
    self._for_stack = []

# 进入 for 循环
self._for_stack.append({
    'start': for_body_start,
    'end': for_body_end,
    'node': for_node
})

# 退出 for 循环
if self._for_stack:
    self._for_stack.pop()
```

### 修复3：处理 for-else 结构
```python
# 问题：else 块被错误地识别为循环体的一部分
# 修复：正确识别 FOR_ITER 的跳转目标

# FOR_ITER 跳转目标是 else 块的开始
else_body_start = for_iter_jump_target

# 检查是否有 else
if instructions[else_body_start].opcode not in [END_FOR, RETURN_VALUE]:
    has_else = True
    else_body_end = find_next_block_end(instructions, else_body_start)
```

## 测试用例

### 测试用例1：基本 For 循环
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

### 测试用例2：For-Else 循环
```python
# 源代码
def test():
    result = []
    for i in range(5):
        if i == 3:
            break
        result.append(i)
    else:
        result.append('完成')
    return result

# 期望反编译结果
def test():
    result = []
    for i in range(5):
        if i == 3:
            break
        result.append(i)
    else:
        result.append('完成')
    return result
```

### 测试用例3：嵌套 For 循环
```python
# 源代码
def test():
    result = []
    for i in range(3):
        for j in range(3):
            result.append((i, j))
    return result

# 期望反编译结果
def test():
    result = []
    for i in range(3):
        for j in range(3):
            result.append((i, j))
    return result
```

### 测试用例4：For 循环内包含 Try-Except
```python
# 源代码
def test():
    result = 0
    for i in range(5):
        try:
            result += 10 / i
        except ZeroDivisionError:
            pass
    return result

# 关键修复点：try-except 应该在 for 循环体内
```

### 测试用例5：For 循环遍历列表
```python
# 源代码
def test():
    items = [1, 2, 3, 4, 5]
    result = 0
    for item in items:
        result += item
    return result

# 期望反编译结果
def test():
    items = [1, 2, 3, 4, 5]
    result = 0
    for item in items:
        result += item
    return result
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | for 循环体范围计算错误，导致 try-except 被放在循环外 | 正确计算 for_body_start 和 for_body_end，设置上下文供其他模式使用 | 通过 |
| 2026-03-01 | 嵌套 for 循环时，内层循环的 try-except 被添加到外层循环 | 使用栈结构管理嵌套的 for 循环 | 通过 |
| 2026-03-01 | for-else 结构的 else 块被错误识别 | 正确识别 FOR_ITER 的跳转目标 | 通过 |

## 相关模式

- [If-Elif-Else 模式](./if_pattern.md)
- [Try-Except 模式](./try_except_pattern.md)
- [While 循环模式](./while_loop_pattern.md)

## 注意事项

1. Python 3.11+ 中 FOR_ITER 的行为有所变化，需要注意跳转计算
2. GET_ITER 和 FOR_ITER 之间可能有其他指令（如 STORE_FAST）
3. 嵌套 for 循环需要正确处理层级关系
4. for-else 的 else 块在循环正常结束时执行，break 时跳过
5. break 和 continue 使用 JUMP_FORWARD 和 JUMP_BACKWARD
6. 迭代器对象可能在栈中，需要正确处理

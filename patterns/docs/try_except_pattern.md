# 模式名称：Try-Except-Else-Finally 模式

## 模式描述

Try-Except-Else-Finally 模式用于识别 Python 中的异常处理结构，包括 try-except、try-except-else、try-finally 和 try-except-else-finally 组合。

### 适用场景
- 基本的 try-except 语句
- 多 except 分支
- try-except-else 语句
- try-finally 语句
- try-except-else-finally 完整结构
- for/while 循环内的 try-except
- 嵌套 try-except

## 字节码特征

### 关键指令序列

#### Python 3.11+ 异常表机制
Python 3.11+ 使用异常表（Exception Table）而不是 SETUP_FINALLY 指令：

```
ExceptionTable:
  start to end -> target [depth]
  42 to 74 -> 76 [1]  # try 块范围 42-74，异常处理从 76 开始
```

#### Try-Except 基本结构
```
# try 块（受保护的代码）
LOAD_FAST result
LOAD_FAST i
LOAD_CONST 0
COMPARE_OP >
POP_JUMP_FORWARD_IF_FALSE 5
LOAD_CONST 10
LOAD_FAST i
BINARY_OP /
BINARY_OP +=
STORE_FAST result

# PUSH_EXC_INFO - 异常处理入口
PUSH_EXC_INFO
# except 块代码
POP_TOP
POP_EXCEPT
JUMP_BACKWARD

# 异常表
ExceptionTable:
  42 to 74 -> 76 [1]
```

#### Try-Except-Else 结构
```
# try 块
try_body:
    # try 体代码
    JUMP_FORWARD else_end  # 如果无异常，跳过 except

# except 块
PUSH_EXC_INFO
# except 体代码
POP_TOP
POP_EXCEPT
JUMP_FORWARD else_end

# else 块
else_start:
    # else 体代码

else_end:
```

#### Try-Finally 结构
```
# try 块
try_body:
    # try 体代码
    JUMP_FORWARD finally_start

# finally 块（无论是否异常都执行）
finally_start:
    # finally 体代码
    RERAISE  # 如果有异常，重新抛出
```

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| try 块 | exception_table.start | exception_table.end | 受保护的代码范围 |
| PUSH_EXC_INFO | exception_table.target | - | 异常处理入口 |
| except 块 | PUSH_EXC_INFO + 2 | POP_EXCEPT | 异常处理代码 |
| else 块 | except_end + 2 | JUMP_FORWARD目标 | 无异常时执行 |
| finally 块 | finally_start | RERAISE/END_FINALLY | 清理代码 |

### 异常表解析

```python
class ExceptionTableEntry:
    start: int      # try 块开始偏移
    end: int        # try 块结束偏移
    target: int     # 异常处理入口（PUSH_EXC_INFO）
    depth: int      # 异常处理深度
    lasti: bool     # 是否是 lasti
    type: int       # 异常类型
```

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| try_body_start | int | try 体开始偏移 | exception_table_entry.start |
| try_body_end | int | try 体结束偏移 | exception_table_entry.end |
| push_exc_info_offset | int | PUSH_EXC_INFO 偏移 | exception_table_entry.target |
| except_body_start | int | except 体开始偏移 | push_exc_info_offset + 2 |
| except_body_end | int | except 体结束偏移 | pop_except_offset |
| has_else | bool | 是否有 else | check_jump_forward_after_except() |
| else_body_start | int | else 体开始偏移 | except_body_end + 2 |
| else_body_end | int | else 体结束偏移 | jump_forward_target |
| has_finally | bool | 是否有 finally | check_finally_block() |
| finally_body_start | int | finally 体开始偏移 | else_body_end + 2 或 except_body_end + 2 |
| finally_body_end | int | finally 体结束偏移 | reraise_offset |
| exception_type | str | 异常类型 | from_compare_op_in_except() |
| in_for_body | bool | 是否在 for 循环内 | check_for_body_range() |
| in_if_body | bool | 是否在 if 体内 | check_if_body_range() |

## 识别伪代码

```
FUNCTION identify_try_except_pattern(instructions, exception_table, context)
    # 解析异常表
    exc_entries = parse_exception_table(exception_table)
    
    FOR each entry IN exc_entries
        # 提取 try 块范围
        try_body_start = entry.start
        try_body_end = entry.end
        push_exc_info_offset = entry.target
        
        # 确定 except 块范围
        except_body_start = push_exc_info_offset + 2
        except_body_end = find_pop_except(instructions, except_body_start)
        
        # 检查是否有 else
        has_else = check_has_else(instructions, except_body_end)
        
        IF has_else THEN
            else_body_start = except_body_end + 2
            else_body_end = find_jump_forward_target(instructions, else_body_start)
        ELSE
            else_body_start = -1
            else_body_end = -1
        END IF
        
        # 检查是否有 finally
        has_finally = check_has_finally(instructions, else_body_end, except_body_end)
        
        IF has_finally THEN
            IF has_else THEN
                finally_body_start = else_body_end + 2
            ELSE
                finally_body_start = except_body_end + 2
            END IF
            finally_body_end = find_reraise_or_end(instructions, finally_body_start)
        ELSE
            finally_body_start = -1
            finally_body_end = -1
        END IF
        
        # 提取异常类型
        exception_type = extract_exception_type(instructions, except_body_start)
        
        # 检查是否在 for/if 体内
        in_for_body = check_in_for_body(context, try_body_start, try_body_end)
        in_if_body = check_in_if_body(context, try_body_start, try_body_end)
        
        RETURN TryExceptPattern(
            try_body=extract_body(instructions, try_body_start, try_body_end),
            except_body=extract_body(instructions, except_body_start, except_body_end),
            else_body=extract_body(instructions, else_body_start, else_body_end) IF has_else ELSE None,
            finally_body=extract_body(instructions, finally_body_start, finally_body_end) IF has_finally ELSE None,
            exception_type=exception_type,
            in_for_body=in_for_body,
            in_if_body=in_if_body
        )
    END FOR
END FUNCTION
```

## 关键修复点

### 修复1：从异常表获取 try 块范围
```python
# 在 _emit 中
if try_body_start == -1 or try_body_end == -1:
    # 从异常表获取 try 块范围
    exc_entries = parse_exception_table(except_table_data)
    for entry in exc_entries:
        if entry.start <= current_offset < entry.end:
            try_body_start = entry.start
            try_body_end = entry.end
            break
```

### 修复2：在 for 循环内正确处理 try 节点
```python
# 在 _push_exc_info 中
for_body_start = getattr(self, 'for_body_start_offset', -1)
for_body_end = getattr(self, 'for_body_end_offset', -1)
current_for_node = getattr(self, 'current_for_node', None)

if for_body_start <= current_offset < for_body_end and current_for_node is not None:
    # 在 for 循环的 body 范围内，添加到 for 循环的 body
    current_for_node._body.append(try_node)
else:
    # 添加到主块
    self.current_block.append(try_node)
```

### 修复3：使用预创建的 try 节点
```python
# 在 _push_exc_info 中
pre_created_try_node = getattr(self, 'current_try_node', None)
if pre_created_try_node is not None and hasattr(pre_created_try_node, '_body'):
    # 使用预创建的 try 节点
    try_node = pre_created_try_node
else:
    # 创建新的 try 节点
    try_node = ASTTry(ASTBlock(), [], ASTBlock(), ASTBlock())
```

## 测试用例

### 测试用例1：基本 Try-Except
```python
# 源代码
def test():
    try:
        result = 10 / 0
    except ZeroDivisionError:
        result = '除零错误'
    return result

# 期望反编译结果
def test():
    try:
        result = 10 / 0
    except ZeroDivisionError:
        result = '除零错误'
    return result
```

### 测试用例2：Try-Except 在 For 循环内
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

# 关键修复点：try 节点应该在 for 循环体内
```

### 测试用例3：嵌套 Try-Except
```python
# 源代码
def test():
    try:
        try:
            result = 10 / 0
        except ZeroDivisionError:
            result = '内层除零错误'
    except Exception:
        result = '外层错误'
    return result
```

### 测试用例4：Try-Except-Else-Finally
```python
# 源代码
def test():
    try:
        result = 10 / 2
    except ZeroDivisionError:
        result = '除零错误'
    else:
        result = '成功'
    finally:
        print('清理')
    return result
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | try_body_start 和 try_body_end 为 -1，无法识别 try 块范围 | 在 _emit 中从异常表获取 try 块范围 | 通过 |
| 2026-03-01 | try 节点被添加到 main_block 而不是 for 循环的 body | 在 _push_exc_info 中检查 for 循环范围 | 通过 |
| 2026-03-01 | _push_exc_info 创建新的 try 节点，而不是使用 _emit 中创建的 | 检查并使用 self.current_try_node | 通过 |
| 2026-03-01 | ASTAugAssign 在 try-except 内的 if 中被错误放置 | 修改 _emit 中的范围检查逻辑 | 通过 |

## 相关模式

- [If-Elif-Else 模式](./if_pattern.md)
- [For 循环模式](./for_pattern.md)
- [复合赋值模式](./augassign_pattern.md)

## 注意事项

1. Python 3.11+ 使用异常表机制，SETUP_FINALLY 指令已被移除
2. PUSH_EXC_INFO 是异常处理的入口点
3. POP_EXCEPT 标记 except 块的结束
4. 需要正确处理嵌套的 try-except
5. for/if 体内的 try-except 需要特殊处理
6. 异常表可能包含多个条目，需要遍历处理

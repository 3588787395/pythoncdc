# 模式名称：函数定义（Function Definition）模式

## 模式描述

函数定义模式用于识别 Python 中的函数定义结构，包括普通函数、嵌套函数、带装饰器的函数、异步函数等。

### 适用场景
- 普通函数定义
- 带参数的函数定义
- 带默认参数的函数定义
- 带 *args 和 **kwargs 的函数定义
- 嵌套函数定义
- 带装饰器的函数定义
- 异步函数定义（async def）
- Lambda 表达式

## 字节码特征

### 关键指令序列

#### 普通函数定义
```
# 加载函数体代码对象
LOAD_CONST <code object test>
LOAD_CONST 'test'

# 创建函数
MAKE_FUNCTION 0             # 创建函数对象

# 存储函数
STORE_FAST test             # 存储到局部变量
```

#### 带参数的函数定义
```
# 加载默认参数（如果有）
LOAD_CONST 10               # 默认值
LOAD_CONST (10,)            # 默认参数元组

# 加载函数体代码对象
LOAD_CONST <code object test>
LOAD_CONST 'test'

# 创建函数（带默认参数）
MAKE_FUNCTION 1             # 创建函数对象（操作数 1 表示有默认参数）

# 存储函数
STORE_FAST test
```

#### 嵌套函数定义
```
# 外层函数
LOAD_CONST <code object outer>
LOAD_CONST 'outer'
MAKE_FUNCTION 0
STORE_FAST outer

# 内层函数（在外层函数体内）
# 加载闭包变量
LOAD_FAST x                 # 加载外层变量
LOAD_CLOSURE x              # 创建闭包

# 加载内层函数代码对象
LOAD_CONST <code object inner>
LOAD_CONST 'inner'

# 创建闭包函数
MAKE_FUNCTION 8             # 操作数 8 表示闭包函数

# 存储内层函数
STORE_FAST inner
```

#### 带装饰器的函数定义
```
# 加载装饰器
LOAD_GLOBAL decorator

# 创建函数（同上）
LOAD_CONST <code object test>
LOAD_CONST 'test'
MAKE_FUNCTION 0

# 应用装饰器
CALL_FUNCTION 1             # 调用装饰器

# 存储装饰后的函数
STORE_FAST test
```

### MAKE_FUNCTION 操作数

| 操作数 | 标志 | 描述 |
|--------|------|------|
| 0 | 0x00 | 普通函数 |
| 1 | 0x01 | 有默认参数 |
| 2 | 0x02 | 有 *args |
| 4 | 0x04 | 有 **kwargs |
| 8 | 0x08 | 有闭包 |
| 组合 | - | 可以组合使用（如 9 = 1 + 8 表示有默认参数和闭包）|

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| 默认参数 | func_start | code_obj_offset | 加载默认参数 |
| 代码对象 | code_obj_offset | code_obj_offset + 4 | LOAD_CONST code + name |
| MAKE_FUNCTION | make_func_offset | make_func_offset + 2 | 创建函数 |
| 装饰器应用 | decorator_offset | decorator_offset + 2 | CALL_FUNCTION（可选） |
| 函数存储 | store_offset | store_offset + 2 | STORE_FAST |

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| func_name | str | 函数名 | from_load_const() |
| code_obj | CodeObject | 函数体代码对象 | from_load_const() |
| make_func_flags | int | MAKE_FUNCTION 标志 | from_make_function() |
| has_defaults | bool | 是否有默认参数 | check_flag(0x01) |
| has_varargs | bool | 是否有 *args | check_flag(0x02) |
| has_kwargs | bool | 是否有 **kwargs | check_flag(0x04) |
| has_closure | bool | 是否有闭包 | check_flag(0x08) |
| decorators | List[str] | 装饰器列表 | extract_decorators() |
| is_async | bool | 是否为异步函数 | check_code_flags() |
| is_nested | bool | 是否为嵌套函数 | check_parent_context() |

## 识别伪代码

```
FUNCTION identify_function_def_pattern(instructions, start_offset, context)
    # 检查是否为函数定义开始
    # 可能有默认参数加载，先跳过
    current = start_offset
    
    # 查找代码对象加载
    WHILE instructions[current].opcode == LOAD_CONST AND 
          is_default_value(instructions[current].argval)
        current += 2
    END WHILE
    
    # 检查是否加载了代码对象
    IF instructions[current].opcode != LOAD_CONST OR
       NOT isinstance(instructions[current].argval, CodeType) THEN
        RETURN None
    END IF
    
    code_obj = instructions[current].argval
    func_name = code_obj.co_name
    
    # 查找函数名加载
    current += 2
    IF instructions[current].opcode != LOAD_CONST OR
       instructions[current].argval != func_name THEN
        RETURN None
    END IF
    
    # 查找 MAKE_FUNCTION
    current += 2
    IF instructions[current].opcode != MAKE_FUNCTION THEN
        RETURN None
    END IF
    
    make_func_flags = instructions[current].operand
    
    # 检查是否有装饰器
    decorators = []
    IF current > start_offset AND 
       instructions[start_offset].opcode == LOAD_GLOBAL THEN
        # 可能有装饰器
        decorators = extract_decorators(instructions, start_offset, current)
    END IF
    
    # 检查是否为异步函数
    is_async = check_async_function(code_obj)
    
    # 检查是否为嵌套函数
    is_nested = context.is_inside_function
    
    # 提取参数信息
    args = extract_arguments(code_obj)
    defaults = extract_defaults(instructions, start_offset, current) IF has_defaults ELSE []
    
    RETURN FunctionDefPattern(
        name=func_name,
        code=code_obj,
        args=args,
        defaults=defaults,
        decorators=decorators,
        is_async=is_async,
        is_nested=is_nested,
        flags=make_func_flags
    )
END FUNCTION
```

## 关键修复点

### 修复1：正确识别嵌套函数
```python
# 问题：嵌套函数被错误地识别为全局函数
# 修复：检查上下文，确定是否为嵌套函数

def check_is_nested_function(context, func_name):
    # 检查是否在另一个函数体内
    if context.current_function is not None:
        return True
    
    # 检查代码对象的 co_freevars（闭包变量）
    if code_obj.co_freevars:
        return True
    
    return False
```

### 修复2：处理带装饰器的函数
```python
# 问题：装饰器函数被忽略，导致反编译结果缺少装饰器
# 修复：识别并提取装饰器链

def extract_decorators(instructions, start, end):
    decorators = []
    
    # 从后向前查找装饰器
    for i in range(end - 1, start - 1, -1):
        if instructions[i].opcode == CALL_FUNCTION:
            # 找到装饰器调用，向前查找装饰器函数
            decorator_name = find_decorator_function(instructions, start, i)
            if decorator_name:
                decorators.insert(0, decorator_name)
    
    return decorators
```

### 修复3：识别异步函数
```python
# 问题：异步函数被识别为普通函数
# 修复：检查代码对象的 co_flags

def check_async_function(code_obj):
    # CO_COROUTINE = 0x80
    # CO_ITERABLE_COROUTINE = 0x100
    return (code_obj.co_flags & 0x80) != 0 or (code_obj.co_flags & 0x100) != 0
```

## 测试用例

### 测试用例1：基本函数定义
```python
# 源代码
def test():
    return 42

# 期望反编译结果
def test():
    return 42
```

### 测试用例2：带参数的函数定义
```python
# 源代码
def test(x, y, z=10):
    return x + y + z

# 期望反编译结果
def test(x, y, z=10):
    return x + y + z
```

### 测试用例3：带 *args 和 **kwargs 的函数定义
```python
# 源代码
def test(a, b, *args, **kwargs):
    return a, b, args, kwargs

# 期望反编译结果
def test(a, b, *args, **kwargs):
    return a, b, args, kwargs
```

### 测试用例4：嵌套函数定义
```python
# 源代码
def outer(x):
    def inner(y):
        return x + y
    return inner

# 期望反编译结果
def outer(x):
    def inner(y):
        return x + y
    return inner
```

### 测试用例5：带装饰器的函数定义
```python
# 源代码
@decorator
def test():
    return 42

# 期望反编译结果
@decorator
def test():
    return 42
```

### 测试用例6：异步函数定义
```python
# 源代码
async def test():
    await asyncio.sleep(1)
    return 42

# 期望反编译结果
async def test():
    await asyncio.sleep(1)
    return 42
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | 嵌套函数被错误识别为全局函数 | 检查上下文和闭包变量 | 通过 |
| 2026-03-01 | 装饰器函数被忽略 | 识别并提取装饰器链 | 通过 |
| 2026-03-01 | 异步函数被识别为普通函数 | 检查代码对象的 co_flags | 通过 |

## 相关模式

- [类定义模式](./class_def_pattern.md)
- [Lambda 表达式模式](./lambda_pattern.md)
- [装饰器模式](./decorator_pattern.md)

## 注意事项

1. MAKE_FUNCTION 的操作数表示函数的特性（默认参数、*args、**kwargs、闭包）
2. 嵌套函数有闭包变量（co_freevars），需要特殊处理
3. 装饰器在 MAKE_FUNCTION 之后、STORE_FAST 之前应用
4. 异步函数的标志在代码对象的 co_flags 中
5. 默认参数在代码对象之前加载
6. 函数名在代码对象之后加载

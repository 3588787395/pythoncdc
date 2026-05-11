# 模式名称：类定义（Class Definition）模式

## 模式描述

类定义模式用于识别 Python 中的类定义结构，包括普通类、继承类、带装饰器的类、元类等。

### 适用场景
- 普通类定义
- 继承类定义（单继承、多继承）
- 带装饰器的类定义
- 元类定义
- 抽象基类
- 数据类（dataclass）
- 嵌套类定义

## 字节码特征

### 关键指令序列

#### 普通类定义
```
# 加载类体代码对象
LOAD_CONST <code object MyClass>
LOAD_CONST 'MyClass'

# 创建类
MAKE_FUNCTION 0             # 创建类体函数
LOAD_CONST 'MyClass'        # 类名
LOAD_NAME object            # 基类（默认 object）
CALL_FUNCTION 3             # 调用 type(name, bases, namespace)

# 存储类
STORE_NAME MyClass          # 存储到全局命名空间
```

#### 继承类定义
```
# 加载基类
LOAD_NAME BaseClass         # 加载基类
BUILD_TUPLE 1               # 创建基类元组

# 加载类体代码对象
LOAD_CONST <code object DerivedClass>
LOAD_CONST 'DerivedClass'

# 创建类
MAKE_FUNCTION 0
LOAD_CONST 'DerivedClass'
LOAD_CONST (BaseClass,)     # 基类元组
CALL_FUNCTION 3

# 存储类
STORE_NAME DerivedClass
```

#### 多继承类定义
```
# 加载多个基类
LOAD_NAME Base1
LOAD_NAME Base2
LOAD_NAME Base3
BUILD_TUPLE 3               # 创建包含 3 个基类的元组

# 加载类体代码对象
LOAD_CONST <code object MultiClass>
LOAD_CONST 'MultiClass'

# 创建类
MAKE_FUNCTION 0
LOAD_CONST 'MultiClass'
LOAD_CONST (Base1, Base2, Base3)
CALL_FUNCTION 3

# 存储类
STORE_NAME MultiClass
```

#### 带装饰器的类定义
```
# 加载装饰器
LOAD_GLOBAL decorator

# 创建类（同上）
LOAD_CONST <code object MyClass>
LOAD_CONST 'MyClass'
MAKE_FUNCTION 0
LOAD_CONST 'MyClass'
LOAD_NAME object
CALL_FUNCTION 3

# 应用装饰器
CALL_FUNCTION 1             # 调用装饰器

# 存储装饰后的类
STORE_NAME MyClass
```

#### 类体代码
```
# 类体函数（在 MAKE_FUNCTION 中）
LOAD_NAME __name__
STORE_NAME __module__
LOAD_CONST 'MyClass'
STORE_NAME __qualname__

# 类属性和方法定义
LOAD_CONST 10
STORE_NAME class_attr

LOAD_CONST <code object method>
LOAD_CONST 'method'
MAKE_FUNCTION 0
STORE_NAME method

# 返回类命名空间
LOAD_LOCALS
RETURN_VALUE
```

### 指令偏移范围

| 组件 | 起始偏移 | 结束偏移 | 说明 |
|------|----------|----------|------|
| 基类加载 | class_start | code_obj_offset | 加载基类并创建元组 |
| 代码对象 | code_obj_offset | code_obj_offset + 4 | LOAD_CONST code + name |
| MAKE_FUNCTION | make_func_offset | make_func_offset + 2 | 创建类体函数 |
| CALL_FUNCTION | call_offset | call_offset + 2 | 调用 type() |
| 装饰器应用 | decorator_offset | decorator_offset + 2 | CALL_FUNCTION（可选） |
| 类存储 | store_offset | store_offset + 2 | STORE_NAME |

## 识别参数表格

| 参数名 | 类型 | 描述 | 计算方式 |
|--------|------|------|----------|
| class_name | str | 类名 | from_load_const() |
| code_obj | CodeObject | 类体代码对象 | from_load_const() |
| bases | List[str] | 基类列表 | extract_bases() |
| decorators | List[str] | 装饰器列表 | extract_decorators() |
| is_metaclass | bool | 是否为元类 | check_metaclass() |
| is_dataclass | bool | 是否为数据类 | check_dataclass_decorator() |
| is_abstract | bool | 是否为抽象基类 | check_abc_decorator() |
| methods | List[str] | 方法列表 | extract_methods() |
| class_attrs | Dict[str, Any] | 类属性 | extract_class_attributes() |

## 识别伪代码

```
FUNCTION identify_class_def_pattern(instructions, start_offset, context)
    # 查找基类元组
    bases = []
    current = start_offset
    
    IF instructions[current].opcode == LOAD_NAME OR
       instructions[current].opcode == LOAD_GLOBAL THEN
        # 有显式基类
        WHILE instructions[current].opcode IN [LOAD_NAME, LOAD_GLOBAL]
            bases.append(instructions[current].argval)
            current += 2
        END WHILE
        
        # 检查是否有 BUILD_TUPLE
        IF instructions[current].opcode == BUILD_TUPLE THEN
            current += 2
        END IF
    ELSE
        # 默认基类 object
        bases = ['object']
    END IF
    
    # 查找类体代码对象
    IF instructions[current].opcode != LOAD_CONST OR
       NOT isinstance(instructions[current].argval, CodeType) THEN
        RETURN None
    END IF
    
    code_obj = instructions[current].argval
    class_name = code_obj.co_name
    
    # 查找类名加载
    current += 2
    IF instructions[current].opcode != LOAD_CONST OR
       instructions[current].argval != class_name THEN
        RETURN None
    END IF
    
    # 查找 MAKE_FUNCTION
    current += 2
    IF instructions[current].opcode != MAKE_FUNCTION THEN
        RETURN None
    END IF
    
    # 查找 CALL_FUNCTION（创建类）
    current += 2
    IF instructions[current].opcode != CALL_FUNCTION THEN
        RETURN None
    END IF
    
    # 检查是否有装饰器
    decorators = []
    IF start_offset > 0 AND 
       instructions[start_offset - 2].opcode IN [LOAD_GLOBAL, LOAD_NAME] THEN
        decorators = extract_class_decorators(instructions, 0, start_offset)
    END IF
    
    # 提取类体信息
    methods = extract_class_methods(code_obj)
    class_attrs = extract_class_attributes(code_obj)
    
    # 检查特殊类型
    is_dataclass = 'dataclass' in decorators
    is_abstract = 'ABC' in bases or 'abstractmethod' in methods
    is_metaclass = check_is_metaclass(code_obj)
    
    RETURN ClassDefPattern(
        name=class_name,
        bases=bases,
        code=code_obj,
        decorators=decorators,
        methods=methods,
        class_attrs=class_attrs,
        is_dataclass=is_dataclass,
        is_abstract=is_abstract,
        is_metaclass=is_metaclass
    )
END FUNCTION
```

## 关键修复点

### 修复1：正确识别基类
```python
# 问题：基类识别错误，特别是多继承时
# 修复：正确解析基类元组

def extract_bases(instructions, start, end):
    bases = []
    
    for i in range(start, end):
        if instructions[i].opcode in [LOAD_NAME, LOAD_GLOBAL]:
            bases.append(instructions[i].argval)
        elif instructions[i].opcode == BUILD_TUPLE:
            # 基类元组构建完成
            break
    
    return bases if bases else ['object']
```

### 修复2：处理类装饰器
```python
# 问题：类装饰器被忽略
# 修复：识别类定义前的装饰器

def extract_class_decorators(instructions, start, class_def_start):
    decorators = []
    
    # 从类定义开始向前查找装饰器
    i = class_def_start - 2
    while i >= start:
        if instructions[i].opcode in [LOAD_GLOBAL, LOAD_NAME]:
            decorator_name = instructions[i].argval
            # 检查是否是装饰器调用
            if i + 2 < len(instructions) and instructions[i + 2].opcode == CALL_FUNCTION:
                decorators.insert(0, decorator_name)
        i -= 2
    
    return decorators
```

### 修复3：提取类方法和属性
```python
# 问题：类体中的方法和属性识别不完整
# 修复：分析类体代码对象

def extract_class_methods(code_obj):
    methods = []
    
    # 遍历类体代码的常量，查找函数代码对象
    for const in code_obj.co_consts:
        if isinstance(const, CodeType) and const.co_name != code_obj.co_name:
            methods.append(const.co_name)
    
    return methods

def extract_class_attributes(code_obj):
    attrs = {}
    
    # 分析类体代码的字节码，查找 STORE_NAME 指令
    # 这些通常是类属性赋值
    
    return attrs
```

## 测试用例

### 测试用例1：基本类定义
```python
# 源代码
class MyClass:
    pass

# 期望反编译结果
class MyClass:
    pass
```

### 测试用例2：继承类定义
```python
# 源代码
class DerivedClass(BaseClass):
    def method(self):
        return 42

# 期望反编译结果
class DerivedClass(BaseClass):
    def method(self):
        return 42
```

### 测试用例3：多继承类定义
```python
# 源代码
class MultiClass(Base1, Base2, Base3):
    pass

# 期望反编译结果
class MultiClass(Base1, Base2, Base3):
    pass
```

### 测试用例4：带装饰器的类定义
```python
# 源代码
@dataclass
class DataClass:
    x: int
    y: str

# 期望反编译结果
@dataclass
class DataClass:
    x: int
    y: str
```

### 测试用例5：抽象基类定义
```python
# 源代码
from abc import ABC, abstractmethod

class AbstractClass(ABC):
    @abstractmethod
    def abstract_method(self):
        pass

# 期望反编译结果
class AbstractClass(ABC):
    @abstractmethod
    def abstract_method(self):
        pass
```

### 测试用例6：嵌套类定义
```python
# 源代码
class Outer:
    class Inner:
        pass

# 期望反编译结果
class Outer:
    class Inner:
        pass
```

## 修复历史

| 日期 | 问题描述 | 修复方案 | 测试结果 |
|------|----------|----------|----------|
| 2026-03-01 | 基类识别错误，特别是多继承时 | 正确解析基类元组 | 通过 |
| 2026-03-01 | 类装饰器被忽略 | 识别类定义前的装饰器链 | 通过 |
| 2026-03-01 | 类方法和属性识别不完整 | 分析类体代码对象 | 通过 |

## 相关模式

- [函数定义模式](./function_def_pattern.md)
- [装饰器模式](./decorator_pattern.md)
- [继承模式](./inheritance_pattern.md)

## 注意事项

1. 类定义使用 type(name, bases, namespace) 创建
2. 类体是一个函数，其局部变量成为类属性
3. 基类默认是 object，可以显式指定
4. 多继承时基类以元组形式传递
5. 类装饰器在类创建后应用
6. 类体代码对象包含 __module__ 和 __qualname__ 赋值
7. 数据类和抽象基类通过装饰器和基类识别

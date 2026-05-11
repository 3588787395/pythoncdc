# 模式名称：装饰器（Decorator）模式

## 模式描述
装饰器模式用于识别 Python 中的函数和类装饰器，包括单装饰器、多装饰器堆叠和带参数的装饰器。

## 字节码特征

### 关键指令序列
```
# 加载装饰器
LOAD_GLOBAL decorator

# 创建函数/类
LOAD_CONST <code object func>
LOAD_CONST 'func'
MAKE_FUNCTION 0

# 应用装饰器
CALL_FUNCTION 1

# 存储装饰后的对象
STORE_FAST func
```

## 识别参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| decorator_name | str | 装饰器名称 |
| decorator_args | List[Any] | 装饰器参数 |
| is_class_decorator | bool | 是否为类装饰器 |

## 测试用例

### 单装饰器
```python
@decorator
def func():
    pass
```

### 多装饰器
```python
@decorator1
@decorator2
def func():
    pass
```

## 相关模式
- [函数定义模式](./function_def_pattern.md)
- [类定义模式](./class_def_pattern.md)

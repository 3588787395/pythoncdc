# 模式名称：全局/非局部声明（Global/Nonlocal）模式

## 模式描述
全局/非局部声明模式用于识别 Python 中的 global 和 nonlocal 声明语句。

## 字节码特征

### 关键指令序列

#### global 声明
```
# global x
# x = 10
LOAD_CONST 10
STORE_GLOBAL x
```

#### nonlocal 声明
```
# nonlocal x
# x = 10
LOAD_CONST 10
STORE_DEREF x
```

## 识别参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| declaration_type | str | 'global' 或 'nonlocal' |
| names | List[str] | 声明的名称列表 |

## 测试用例

### global 声明
```python
def func():
    global x
    x = 10
```

### nonlocal 声明
```python
def outer():
    x = 10
    def inner():
        nonlocal x
        x = 20
```

## 相关模式
- [函数定义模式](./function_def_pattern.md)
- [导入模式](./import_pattern.md)

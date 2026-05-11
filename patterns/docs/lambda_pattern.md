# 模式名称：Lambda 表达式模式

## 模式描述
Lambda 表达式模式用于识别 Python 中的匿名函数定义，包括简单 lambda、带默认参数的 lambda 和嵌套 lambda。

## 字节码特征

### 关键指令序列
```
# 加载代码对象
LOAD_CONST <code object <lambda>>
LOAD_CONST '<lambda>'

# 创建函数
MAKE_FUNCTION 0

# 使用 lambda
STORE_FAST func  # 或直接调用
```

## 识别参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| args | List[str] | 参数列表 |
| body | ASTNode | 函数体表达式 |
| defaults | List[Any] | 默认参数值 |

## 测试用例

### 简单 Lambda
```python
f = lambda x: x + 1
```

### 带默认参数的 Lambda
```python
f = lambda x, y=10: x + y
```

## 相关模式
- [函数定义模式](./function_def_pattern.md)

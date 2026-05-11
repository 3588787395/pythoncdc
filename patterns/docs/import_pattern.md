# 模式名称：导入（Import）模式

## 模式描述
导入模式用于识别 Python 中的 import 语句，包括 import module、from module import name、from module import * 和 import module as alias。

## 字节码特征

### 关键指令序列

#### import module
```
LOAD_CONST 0 ('module')
IMPORT_NAME module
STORE_NAME module
```

#### from module import name
```
LOAD_CONST 0 ('module')
IMPORT_NAME module
IMPORT_FROM name
STORE_NAME name
POP_TOP
```

#### from module import *
```
LOAD_CONST 0 ('module')
IMPORT_NAME module
IMPORT_STAR
```

## 识别参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| import_type | str | 导入类型 |
| module_name | str | 模块名 |
| imported_names | List[str] | 导入的名称列表 |
| alias | str | 别名 |

## 测试用例

### import module
```python
import os
```

### from module import name
```python
from os import path
```

### import as
```python
import numpy as np
```

## 相关模式
- [全局/非局部声明模式](./global_nonlocal_pattern.md)

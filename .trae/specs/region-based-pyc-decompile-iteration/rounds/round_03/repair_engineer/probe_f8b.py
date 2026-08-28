#!/usr/bin/env python
"""Round 03 修复工程师探针：F8 缩小——嵌套 if + 尾赋值形状。"""
import sys
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
from core.cfg import decompile

SRCS = {
 # 嵌套 if + 普通属性赋值（无 boolop）
 'P7_nested_if_plain_attr': "def f(engine):\n    if engine.a:\n        if engine.b:\n            engine.c()\n        engine.a = 1\n",
 # 嵌套 if + 局部变量 boolop 赋值（STORE_FAST 而非 STORE_ATTR）
 'P8_nested_if_boolop_local': "def f(engine):\n    if engine.a:\n        if engine.b:\n            engine.c()\n        x = engine.a or 10\n        engine.a = x\n",
 # 嵌套 if + boolop 属性赋值（P5 复制，确认稳定）
 'P9_nested_if_boolop_attr': "def f(engine):\n    if engine.a:\n        if engine.b:\n            engine.c()\n        engine.a = engine.a or 10\n",
 # 无嵌套：if 体直接是 boolop 属性赋值
 'P10_flat_boolop_attr': "def f(engine):\n    if engine.a:\n        engine.a = engine.b or 10\n    return engine\n",
 # 嵌套 if 在 boolop 赋值之后
 'P11_assign_then_nested': "def f(engine):\n    if engine.a:\n        engine.a = engine.b or 10\n        if engine.b:\n            engine.c()\n",
 # 模块级（非函数体）
 'P12_module_level': "if engine.a:\n    if engine.b:\n        engine.c()\n    engine.a = engine.b or 10\n",
}
for k, s in SRCS.items():
    try:
        out = decompile(s)
    except Exception as e:
        print('====', k, 'CRASH', type(e).__name__, e)
        continue
    print('====', k)
    print(out)

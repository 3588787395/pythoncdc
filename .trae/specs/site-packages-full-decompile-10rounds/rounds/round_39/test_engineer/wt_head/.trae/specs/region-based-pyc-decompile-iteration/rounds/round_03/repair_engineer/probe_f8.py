#!/usr/bin/env python
"""Round 03 修复工程师探针：F8 if 内 import 重排。"""
import sys
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
from core.cfg import decompile

SRCS = {
 # 基线：import + 普通赋值（repro_09 形状，应 PASS）
 'P1_import_assign': "def f(engine):\n    if engine.a:\n        import ptvsd\n        engine.a = 1\n",
 # import + 嵌套 if（无 boolop）
 'P2_import_nested_if': "def f(engine):\n    if engine.a:\n        import ptvsd\n        if engine.b:\n            ptvsd.reset()\n",
 # import + boolop 赋值（无嵌套 if）
 'P3_import_boolop': "def f(engine):\n    if engine.a:\n        import ptvsd\n        engine.a = engine.b or 10\n",
 # 全组合（repro_04 精确形状）
 'P4_full': "def f(engine):\n    if engine.a:\n        import ptvsd\n        if engine.b:\n            ptvsd.reset()\n        engine.a = engine.b or 10\n",
 # 无 import：boolop 赋值 + 嵌套 if
 'P5_noimport_boolop_nested': "def f(engine):\n    if engine.a:\n        if engine.b:\n            engine.c()\n        engine.a = engine.b or 10\n",
 # from-import 变体
 'P6_from_import': "def f(engine):\n    if engine.a:\n        from x import y\n        engine.a = engine.b or 10\n",
}
for k, s in SRCS.items():
    try:
        out = decompile(s)
    except Exception as e:
        print('====', k, 'CRASH', type(e).__name__, e)
        continue
    print('====', k)
    print(out)

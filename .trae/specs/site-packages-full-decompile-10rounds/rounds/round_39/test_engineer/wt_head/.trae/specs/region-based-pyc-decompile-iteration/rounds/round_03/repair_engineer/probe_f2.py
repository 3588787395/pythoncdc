#!/usr/bin/env python
"""Round 03 修复工程师探针：F2 类体别名赋值。"""
import sys
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
from core.cfg import decompile

SRCS = {
 'A_class_const': 'class C:\n    X = 1\n',
 'B_class_selfalias': 'class C:\n    X = X\n',
 'C_module_selfalias': 'X = X\n',
 'D_class_mixed': 'class C:\n    Y = 1\n    X = X\n    def m(self):\n        return 1\n',
 'E_class_crossalias': 'class C:\n    X = Y\n',
 'F_two_methods_only': 'class C:\n    def m(self):\n        return 1\n    def n(self):\n        return 2\n',
}
for k, s in SRCS.items():
    try:
        out = decompile(s)
    except Exception as e:
        print(k, 'CRASH', type(e).__name__, e)
        continue
    print('====', k)
    print(out)

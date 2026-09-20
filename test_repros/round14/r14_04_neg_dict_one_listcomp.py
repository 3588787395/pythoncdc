# -*- coding: utf-8 -*-
"""R14-04 负对照：dict 只有**一个**推导式值 + 一个标量值。

`comprehension_generator.py:112` 的成对焊接分支要求 `len(comp_indices) >= 2`，
单推导式时不进入该分支，通用栈重建路径正确处理 BUILD_CONST_KEY_MAP。
实测：产物 `{'a': [x for x in t], 'b': 1}` 严格一致。
期望：MATCH（负对照，必须保持一致；它证明缺陷需要 ≥2 个同级推导式，
不是「dict 字面量本身不会重建」）。
"""


def comp_and_scalar(t, u):
    return {'a': [x for x in t], 'b': 1}


def scalar_then_comp(t, u):
    return {'b': 1, 'a': [x for x in t]}


def comp_and_call(t, u):
    return {'a': [x for x in t], 'b': len(u)}

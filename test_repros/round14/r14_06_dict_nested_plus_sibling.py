# -*- coding: utf-8 -*-
"""R14-06 复现：dict 的一个值是**合法嵌套**推导式、另一个是单层推导式。

形状：`{'a': [[x for x in row] for row in t], 'b': [y for y in u]}`
原始字节码里有 3 个推导式 code 对象：#1 外层、#2 它的内层（真嵌套）、
#3 是 dict 的第二个值（与 #1/#2 是兄弟，其 MAKE_FUNCTION 出现在
#1/#2 的调用链闭合之后）。chained-pair 探测器按「相邻 MAKE_FUNCTION」配对，
把 #2/#3 这一对**兄弟**焊成嵌套，dict 的键元组 + BUILD_CONST_KEY_MAP 随之消失。
实测缺陷指纹：
  <module>.f               [seq_len] orig=14 decomp=11
  <module>.f.<listcomp>    [seq_len] orig=13 decomp=9   （内层被连带改写）
期望：MISMATCH（缺陷复现）。
"""


def nested_plus_sibling(t, u):
    return {'a': [[x for x in row] for row in t], 'b': [y for y in u]}

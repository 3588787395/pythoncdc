# -*- coding: utf-8 -*-
"""R14-16 复现：dict 两个值是**不同种类**的推导式（list comp + set comp）。

形状：`{'a': [x for x in t], 'b': {y for y in u}}`
两个推导式的 code 对象名不同（`<listcomp>` / `<setcomp>`）、内层收集操作码不同
（LIST_APPEND / SET_ADD），但仍然被配对焊接 ⇒ 探测器完全不看推导式种类，
只看「block 内相邻的两个 MAKE_FUNCTION + 中间无语句终止符」。
实测缺陷指纹：`<module>.f [seq_len] orig=14 decomp=11`。
期望：MISMATCH（缺陷复现）。
"""


def dict_listcomp_and_setcomp(t, u):
    return {'a': [x for x in t], 'b': {y for y in u}}

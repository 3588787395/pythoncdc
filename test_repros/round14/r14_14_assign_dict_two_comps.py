# -*- coding: utf-8 -*-
"""R14-14 复现：坍缩与「是否作为 return 值」无关 —— 赋值形态 + 条件分支形态。

`d = {'a': [...], 'b': [...]}` 与 `if flag: return {...}` 与裸 `return {...}`
三种宿主语句里，chained-pair 探测器都在同一个位置（block 指令序列）命中：
`try_generate_comprehension_assign` 是从 `_generate_block_statements_body`
(region_ast_generator.py:43106) 调用的，与语句类型无关。
产物形态：
  d = [y for y in [x for x in t]]; return d            （赋值形态，dict 与 u 消失）
实测缺陷指纹：
  赋值形态   <module>.f [seq_len] orig=16 decomp=13
  条件形态   <module>.f [seq_len] orig=18 decomp=15
期望：MISMATCH（缺陷复现）。
"""


def assign_two_comps(t, u):
    d = {'a': [x for x in t], 'b': [y for y in u]}
    return d


def two_comps_in_if(t, u, flag):
    if flag:
        return {'a': [x for x in t], 'b': [y for y in u]}
    return {}

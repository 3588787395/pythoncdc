# -*- coding: utf-8 -*-
"""R14-11 复现：dict 的两个值是 **set 推导式** `{x for x in t}`。

推导式 code 对象名 `<setcomp>`，内层用 SET_ADD 而非 LIST_APPEND；
MAKE_FUNCTION flags 与 listcomp 相同（0），尾部消费者仍是键元组 + BUILD_CONST_KEY_MAP
⇒ 同样被 chained-pair 探测器焊接。
实测缺陷指纹：
  <module>.f            [seq_len] orig=14 decomp=11
  <module>.f.<setcomp>  [seq_diff] #4 orig=("'x'", 'STORE_FAST') …（内层目标名被改写）
期望：MISMATCH（缺陷复现，与 list 版同族 ⇒ 与推导式种类无关）。
"""


def dict_two_setcomps(t, u):
    return {'a': {x for x in t}, 'b': {y for y in u}}

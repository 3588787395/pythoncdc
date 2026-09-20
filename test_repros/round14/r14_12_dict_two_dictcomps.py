# -*- coding: utf-8 -*-
"""R14-12 复现：dict 的两个值是 **dict 推导式** `{x: x for x in t}`。

推导式 code 对象名 `<dictcomp>`，内层用 MAP_ADD；MAKE_FUNCTION flags = 0。
外层容器仍是 dict 字面量（键元组 + BUILD_CONST_KEY_MAP）⇒ 消费者不在白名单 ⇒ 焊接。
产物形态 `{y: y for y in {x: x for x in t}}`（外层 dict 字面量整个退化成一个 dictcomp）。
实测缺陷指纹：
  <module>.f             [seq_len] orig=14 decomp=11
  <module>.f.<dictcomp>  [seq_diff] #4 orig=("'x'", 'STORE_FAST') decomp=("'y'", …)
对照：把外层容器换成 list（`[{x: x for x in t}, {y: y for y in u}]`）即 r14_07 同族，
实测 MATCH —— 见 r14_07_neg_list_two_listcomps 的说明。
期望：MISMATCH（缺陷复现）。
"""


def dict_two_dictcomps(t, u):
    return {'a': {x: x for x in t}, 'b': {y: y for y in u}}

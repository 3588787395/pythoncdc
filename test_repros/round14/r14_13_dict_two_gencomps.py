# -*- coding: utf-8 -*-
"""R14-13 复现：dict 的两个值是 **生成器表达式** `(x for x in t)`。

生成器表达式是唯一 MAKE_FUNCTION flags ≠ 0（flag 1 = GEN_FUNC）的推导式；
内层用 FOR_ITER + YIELD_VALUE，无 LIST_APPEND。
结论：缺陷与 MAKE_FUNCTION flags、与内层收集操作码（LIST_APPEND / SET_ADD /
MAP_ADD / YIELD_VALUE）都无关，只取决于**外层消费者 opcode**（此处 BUILD_CONST_KEY_MAP）。
实测缺陷指纹：
  <module>.f              [seq_len] orig=14 decomp=11
  <module>.f.<genexpr>    [seq_diff] #5 orig=("'x'", 'STORE_FAST') decomp=("'y'", …)
对照：dict 里只放一个生成器表达式（`{'a': (x for x in t), 'b': 1}`）实测 MATCH。
期望：MISMATCH（缺陷复现）。
"""


def dict_two_gencomps(t, u):
    return {'a': (x for x in t), 'b': (y for y in u)}


def dict_one_gencomp(t, u):
    return {'a': (x for x in t), 'b': 1}

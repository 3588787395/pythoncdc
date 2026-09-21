# -*- coding: utf-8 -*-
# R22 锚点 02 —— J1'(a) 作用域分裂：if/else 两臂各含一个 for 循环节。
#
# 塌缩后 else_blocks 归空（entry == merge），else 臂的循环被推到父序列，
# base 核产物丢掉 `else:` 层级 → strict seq_len −2。
# 语料锚点 plugin_fly_data/__init__.pyc <module>.ApiMethodPlugin.resist_api
#   base: seq_len orig=107 decomp=105；after: ok
# 本复现（<module>.f，orig=27）：base=MISMATCH decomp=25，after=MATCH。
# 类别 FIX（仅 J1'(a) 可修）。
def f(xs, ys, flag):
    if flag is None:
        for x in xs:
            print(x)
    else:
        for y in ys:
            if y:
                print(y)

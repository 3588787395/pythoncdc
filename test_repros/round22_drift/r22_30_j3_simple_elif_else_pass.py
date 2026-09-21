# -*- coding: utf-8 -*-
# R22 锚点 30 —— 最简 elif 链 + `else: pass` + 尾随语句（臂内无嵌套 if）。
#
# 本复现（<module>.f，orig=25）：base=MISMATCH decomp=24，after=MATCH。类别 FIX。
def f(mode):
    if mode == 1:
        print(1)
    elif mode == 2:
        print(2)
    else:
        pass
    print('tail')

# -*- coding: utf-8 -*-
# R22 负对照 36 —— `else: pass` 在 try 体内（exception_table 半段接管判定）。
#
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(mode, a):
    try:
        if mode == 1:
            if a:
                print(1)
        else:
            pass
    except BaseException:
        print('bad')

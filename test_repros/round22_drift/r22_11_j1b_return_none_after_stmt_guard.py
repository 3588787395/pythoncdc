# -*- coding: utf-8 -*-
# R22 负对照 11 —— 同 10，但臂里 return None 之前还有一条语句（两块臂）。
#
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(a):
    if a:
        print('in')
        return None
    print('out')

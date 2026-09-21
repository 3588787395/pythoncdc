# -*- coding: utf-8 -*-
# R22 负对照 08 —— 只有 then 臂是循环、else 臂是普通语句。
#
# 与 02 只差一处（else 臂的 for 换成 print），说明 (a) 的判据必须精确到
# 「臂入口 vs else_succ」两点，而不是「本 if 附近有没有循环」。
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(xs, flag):
    if flag:
        for x in xs:
            print(x)
    else:
        print('no')

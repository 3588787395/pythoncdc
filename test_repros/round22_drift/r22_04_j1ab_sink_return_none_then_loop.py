# -*- coding: utf-8 -*-
# R22 锚点 04 —— J1' 两条前置条件同时命中的形状（汇点臂含 return None + 循环）。
#
# 臂 = `for …: print` + 裸 `return None`，else_succ = try 体尾语句；
# (a) 与 (b) 在这里都为真，任一单独生效即可修好 → 说明两条判据在该族上冗余，
# 也说明 corpus 里同类函数的归因必须逐条测（不能只看 J1' 整体）。
# 语料同族：IQData/plugins/plugin_system_realquote/real_quote.pyc
#   <module>.RealQuoteData.get_real_minute_kline_bk base seq_len 169→171(+2) → ok
# 本复现（<module>.f，orig=40）：base=MISMATCH decomp=38，after=MATCH。
# 类别 FIX（mirror/j1a 与 mirror/j1b 各自单独都能修）。
import sys


def f(xs, n):
    try:
        if n:
            for x in xs:
                print(x)
            return None
        sys.stdout.write('empty')
    except BaseException:
        sys.stdout.write('bad')
        return None

# -*- coding: utf-8 -*-
# R22 锚点 03 —— J1'(a) 生成器版本（与 02 同族，臂内含 continue/yield）。
#
# 语料锚点 site-packages/fly/data/quote_handler.pyc 的三个孪生
#   <module>.get_all_fundamentals_daily / get_all_valuation / get_all_valuation_new
#   base: seq_len orig=73 decomp=71；after: ok（三份同形，各 +1 函数）
#   base 产物把尾巴的 `for stock in stocks: yield (...)` 放到 if 之外，
#   after 产物还原为 `else:` 臂内。
# 本复现（<module>.f，orig=44）：base=MISMATCH decomp=42，after=MATCH。
# 类别 FIX（仅 J1'(a) 可修）。
def f(stocks, mp):
    if mp:
        for s in stocks:
            if s in mp:
                yield (s, mp[s])
                continue
            yield (s, None)
    else:
        for s in stocks:
            yield (s, 0)

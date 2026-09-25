# -*- coding: utf-8 -*-
"""R64 diag2 repro (c2 机制): 非紧邻取值上下文 COMPARE_OP 被误判为 if 条件起点。
真实缺陷 IQData/api/api_base.pyc get_future_history_df [973,957,3,229]（丢 17 条 @4274..@4360
= `count_c = len(df[(df['datetime'] >= q) & (df['datetime'] > left)])`）。
机制/证据见 D:/Temp/opencode/r64gate/diag2/ANALYSIS.md，读数表见 FACTS.md §4。"""


def r64d2_valuectx(df, q, left, engine, sym):
    c = df['dt']
    m = c.mean()
    n = len(df[(df['dt'] >= q) & (df['dt'] > left)])
    k = engine.get(sym, n)
    if k > 0:
        return k
    return 0

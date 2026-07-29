"""repro_10: get_str_data 完整模式缩影（根因 B+C 综合复现）。

模拟 get_str_data 的完整结构：
- 外层 for stock 循环（LoopRegion）
- 内层 if not datas: continue（IfRegion@614）
- else 分支含 7 键 dict 构造：4 普通 LOAD + 2 三元 + 1 普通 LOAD
- 2 个三元链式共享 merge_block（根因 C）
- BUILD_CONST_KEY_MAP 7 + STORE_SUBSCR（data.loc[i] = dict）
- i 递增

R18 已修复根因 A（value_target 对 STORE_SUBSCR 误识别）。
R19 重点修复根因 B（兄弟三元遗漏）+ C（链式共享 merge_block 独占标记）。
"""

import numpy


def f(rdata, count, typet):
    order_data = {}
    for stock in rdata:
        stock_df = rdata[stock]
        n = len(stock_df)
        data = {}
        i = 0
        for j in range(n):
            data_is_nan = j % 2
            data.loc[i] = {
                'open': stock_df[j],
                'close': stock_df[j],
                'high': stock_df[j].max(),
                'low': stock_df[j].min(),
                'volume': numpy.nan if data_is_nan == 1 else stock_df[j].sum(),
                'price': stock_df[j],
                'money': numpy.nan if data_is_nan == 1 else stock_df[j].sum(),
            }
            i += 1
        order_data[stock] = data
    return order_data

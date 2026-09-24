# -*- coding: utf-8 -*-
"""Round63 第 3 批 最小合成复现：值语境链式比较 + 同块前导赋值语句整体丢失。

对应真实缺陷：IQEngine/plugins/plugin_system_matcher/matcher.pyc 的 match，
原源码行 227-229（`stock_listed_date = ...` / `next_trading_date = ...` /
`is_first_five_trading_days = a <= b <= c`）三条语句在反编译产物中全部消失（-26 条指令）。

形态要点（缺一不可，均为结构条件）：
 1) 链式比较 `a <= b <= c` 出现在**赋值右侧**（值语境，非 if 条件）；
 2) 比较的中段操作数是属性/方法调用链（`self._engine.trading_dt`），左段之前同块
    还有**已完结的赋值语句**（含 LOAD_METHOD 调用）——于是链式比较的 cond 块是
    「前导语句 + 表达式前导」复合直线块；
 3) 该语句处于 if/else 分支内，由 _process_if_blocks 分发给值语境子区域。
"""


def r63b3_match_like(order, engine, gem_change_date, trading_date, listed_str):
    if order.symbol[:3] == '300' and trading_date < gem_change_date:
        flag = 1
    if order.symbol[:3] == '300' and listed_str < gem_change_date:
        flag = 2
    stock_listed_date = order.listed_date
    next_trading_date = engine.data_proxy.get_next_trading_date(stock_listed_date, 5)
    is_first_five_trading_days = stock_listed_date <= engine.trading_dt <= next_trading_date
    if is_first_five_trading_days:
        return 3
    return 0

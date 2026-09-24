# -*- coding: utf-8 -*-
"""Round63 第 3 批（fix1）最小合成复现：值语境链式比较 + 同块前导语句整体丢失。

对应真实缺陷：site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc ::
Matcher.match 的原源码行 227-229
    stock_listed_date = order.asset.listed_date
    next_trading_date = self._engine.data_proxy.get_next_trading_date(...)
    is_first_five_trading_days = stock_listed_date <= self._engine.trading_dt <= next_trading_date
三条语句在产物中全部消失（orig 713 / decomp 689，deficit -24）。

形态要点（缺一不可，均为结构条件，与 matcher.match 一致）：
 1) 链式比较 `a <= b <= c` 处于**赋值右侧**（值语境，非 if 条件），且中段操作数是
    属性/调用链，比较左段之前同块还有已完结的赋值语句（含 LOAD_METHOD 调用）；
 2) 该语句位于 if/elif/…/else 链的 else 分支内，且兄弟分支全部以 continue 收尾
    —— 于是它由 _process_if_blocks 的分支序列作为**嵌套**三元子区域派发，
    _generate_ternary 返回空后分支序列仍无条件 generated_blocks.add(块)，语句丢失；
 3) else 分支里链式比较之后紧跟另一个消费该变量的 if/elif continue 链，使 merge
    块非空（merge_context='store'，value_target=被赋值名）。
"""

GEM = '20200824'


def probe(amounts, proxy, listed_dt, trading_dt, direction, deal_price, limit_up, limit_down, sym):
    total = 0
    for item in amounts:
        if item < 0:
            total += 1
        elif sym[:3] == '300':
            if not trading_dt < limit_up:
                if sym[:3] == '300' and listed_dt < GEM:
                    if direction == 'buy' and deal_price >= limit_up:
                        continue
                    elif direction == 'sell' and deal_price <= limit_down:
                        continue
                    else:
                        stock_listed_date = listed_dt
                        next_trading_date = proxy.get_next_trading_date(stock_listed_date, 5)
                        is_first_five = stock_listed_date <= trading_dt <= next_trading_date
                        if sym[:3] == '300' and trading_dt >= GEM and listed_dt >= GEM:
                            if is_first_five or direction == 'buy' and deal_price >= limit_up:
                                continue
                            elif direction == 'sell' and deal_price <= limit_down:
                                continue
                            elif sym[:3] in ('688', '689'):
                                if is_first_five or direction == 'buy' and deal_price >= limit_up:
                                    continue
                                elif direction == 'sell' and deal_price <= limit_down:
                                    continue
                        total += item
    return total

# -*- coding: utf-8 -*-
# R76-E 复现（对照 Quote.build_current_period_df，round3 r3_06 同型）：
# if/else 内尾部 `tempdict['is_open'] = [1 if c else 0]` 后跟
# `tmp = pandas.DataFrame(tempdict, index=index); return tmp`。
# 预期缺陷：下标赋值降级为裸 `[1 if ... else 0]`，DataFrame/return 被吞。
def f(df, index_data=False):
    if not df.empty:
        tempdict = OrderedDict()
        index = None
        if index_data:
            index = [df.index[-1]]
        else:
            tempdict['min_time'] = [df.index[-1]]
        tempdict['open'] = [df['open'][0]]
        tempdict['close'] = [df['close'][-1]]
        tempdict['is_open'] = [1 if df['is_open'] != 0 else 0]
        tmp = pandas.DataFrame(tempdict, index=index)
        return tmp
    else:
        return None

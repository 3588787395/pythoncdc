"""R9 repro_05: get_date_and_count while 循环 if/elif 链语句丢失(-27)。
缺陷: while 循环体内 if/elif/else 链部分分支语句丢失。
区域类型: Loop + Conditional  违反原则: 4(入口引用语义)
"""
def f(start, end, candle_period):
    trade_days = []
    d = start
    weekday = 0
    while d <= end:
        if weekday not in (6, 7):
            trade_days.append(d)
        elif candle_period == 1:
            trade_days.append(d)
            d = d + 1
        elif candle_period == 2:
            trade_days.append(d)
            d = d + 1
        else:
            d = d + 1
    return trade_days

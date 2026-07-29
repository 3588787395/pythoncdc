"""R8 repro_05: get_date_and_count if/elif 链语句丢失。
缺陷: if/elif/else 链中部分分支语句被丢弃，导致 -27 指令差异。
区域类型: Conditional  违反原则: 4(入口引用语义)
"""
def f(query_date, count, candle_period):
    end_time_str = str(query_date)[:8]
    weekday = 0
    if weekday in (6, 7):
        start_date = end_time_str - count * 7 - weekday
    else:
        start_date = end_time_str - count * 7
    trade_days = []
    d = start_date
    while d <= end_time_str:
        if weekday not in (6, 7):
            trade_days.append(d)
        elif candle_period == 1:
            trade_days.append(d)
        elif candle_period == 2:
            trade_days.append(d)
        d = d + 1
    return trade_days

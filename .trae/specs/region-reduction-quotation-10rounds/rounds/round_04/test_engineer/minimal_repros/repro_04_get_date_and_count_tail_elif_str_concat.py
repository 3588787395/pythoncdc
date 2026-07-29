"""repro_04: 尾部 elif 分支体 `start_date = str(year) + str(month) + '01'` 丢失（get_date_and_count）。

get_date_and_count 的 -27 指令差异源于尾部 elif 分支体（字符串拼接 + 赋值）丢失。
镜像实际 CFG：
  - if candle_period == 8: ... elif candle_period == 9: ... elif candle_period == 10: ...
  - 每个分支含 year/month 赋值 + start_date 字符串拼接
  - 尾部 elif 的字符串拼接 body 丢失
"""


def get_date_and_count_repro(candle_period, query_date):
    if candle_period == 8:
        year = query_date.year
        month = query_date.month
        if month <= 10:
            month = month + 2
        else:
            year = year + 1
            month = month - 10
        start_date = str(year) + str(month).zfill(2)
    elif candle_period == 9:
        year = query_date.year
        month = query_date.month
        start_date = str(year) + str(month).zfill(2) + '01'
    elif candle_period == 10:
        year = query_date.year
        month = query_date.month
        start_date = str(year) + str(month) + '01'
    return (start_date, query_date)

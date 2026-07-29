"""repro_13: elif 分支含 strftime 重赋值 + while + 尾部 if/in 字符串拼接丢失（get_date_and_count）。

原始 get_date_and_count 的 `elif candle_period == 8:` 分支含：
    query_date = datetime.strftime(query_date, '%Y%m%d')
    this_month_start_date = query_date[:6] + '01'
    if len(get_trade_days(...)) == 0:
        while count > 0: ...
        if month in (10, 11, 12):
            start_date = str(year) + str(month) + '01'
        else:
            start_date = str(year) + '0' + str(month) + '01'
JUMP_FORWARD 3046→2946，尾部 if/in + 字符串拼接 + return 丢失（-27 指令）。
本 repro 聚焦 Conditional 尾部 elif 含 while + if/in 元组 + 字符串拼接归约缺陷。
"""
import datetime


def get_date_and_count(query_date, count, candle_period):
    query_date = datetime.datetime.strptime(query_date, '%Y%m%d')
    if candle_period == 7:
        start_date = query_date - datetime.timedelta(days=count * 7)
    elif candle_period == 8:
        year = query_date.year
        month = query_date.month
        query_date = datetime.datetime.strftime(query_date, '%Y%m%d')
        this_month_start_date = query_date[:6] + '01'
        if len(get_trade_days(this_month_start_date, query_date)) == 0:
            query_date = datetime.datetime.strptime(this_month_start_date, '%Y%m%d') - datetime.timedelta(1)
            query_date = datetime.datetime.strftime(query_date, '%Y%m%d')
            while count > 0:
                if month - count <= 0:
                    year -= 1
                    count -= month
                    month = 12
                else:
                    month = month - count
                    count = 0
            if month in (10, 11, 12):
                start_date = str(year) + str(month) + '01'
            else:
                start_date = str(year) + '0' + str(month) + '01'
        elif count == 1:
            start_date = this_month_start_date
        else:
            count -= 1
            start_date = str(year) + '0' + str(month) + '01'
        start_date = this_month_start_date
        if month in (10, 11, 12):
            start_date = str(year) + str(month) + '01'
        else:
            start_date = str(year) + '0' + str(month) + '01'
    elif candle_period == 9:
        start_date = str(year) + '0101'
    return (start_date, query_date)

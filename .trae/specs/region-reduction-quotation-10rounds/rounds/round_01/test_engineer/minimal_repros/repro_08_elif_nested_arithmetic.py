"""repro_08: if/elif 链 + 嵌套算术 + 尾部 elif 丢失（get_date_and_count 模式）。

复现原始字节码结构：if candle_period == 7: ... elif candle_period == 8: ...
每个分支含 datetime/timedelta/strftime 算术运算链，
尾部 elif 分支（含 str(year) + str(month) + '01' 拼接）被丢失（少 27 条）。
对应 _identify_conditional_regions / _generate_if 尾部 elif 归约。
"""


def get_date_and_count(query_date, count, candle_period):
    query_date = datetime.strptime(query_date, '%Y%m%d')
    if candle_period == 7:
        a = query_date.isocalendar()
        this_week_start = datetime.strftime(query_date - timedelta(days=a[2] - 1), '%Y%m%d')
        if len(get_trade_days(this_week_start, datetime.strftime(query_date, '%Y%m%d'))) == 0:
            start_date = datetime.strftime(query_date - timedelta(days=7 * count + count - 1 + a[2] - 1), '%Y%m%d')
            query_date = query_date - timedelta(days=7 * a[2] - 5)
        elif count == 1:
            start_date = this_week_start
        else:
            count = count - 1
            start_date = datetime.strftime(query_date - timedelta(days=7 * count + count - 1 + a[2] - 1), '%Y%m%d')
    elif candle_period == 8:
        year = query_date.year
        month = query_date.month
        if count == 1:
            start_date = str(year) + str(month) + '01'
        else:
            start_date = str(year) + '0' + str(month) + '01'
    else:
        start_date = str(query_date)
    return (start_date, query_date)

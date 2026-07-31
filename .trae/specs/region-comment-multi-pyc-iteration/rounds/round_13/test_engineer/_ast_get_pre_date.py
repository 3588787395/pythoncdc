# AST dump for get_pre_date
def get_pre_date(bar_count, cur_date, frequency, trading_time=''):
    if trading_time:
        if isinstance(cur_date, datetime.datetime):
            min_datetime = int(datetime.datetime.strftime(cur_date, '%Y%m%d')) * 10000 + 800
            _df_nan_data, _ = get_kline_time_by_asset(frequency, min_datetime, trading_time)
            if frequency[-1] == 'm':
                multi = 1 / length * int(frequency[:-1])
            else:
                multi = 1
    elif frequency == Frequency.DAILY.value:
        multi = 1
    elif frequency == Frequency.MINUTE.value:
        multi = 0.004166666666666667
    elif frequency == Frequency.TICK.value:
        multi = 0.00020833333333333332
    elif frequency == Frequency.MINUTE5.value:
        multi = 0.020833333333333332
    elif frequency == Frequency.MINUTE15.value:
        multi = 0.0625
    elif frequency == Frequency.MINUTE30.value:
        multi = 0.125
    elif frequency == Frequency.MINUTE60.value:
        multi = 0.25
    elif frequency == Frequency.MINUTE120.value:
        multi = 0.5
    else:
        multi = 1
    pre_date_count = ceil(bar_count * multi) + 1
    if pre_date_count > 0:
        from fly.common.tradingday_calendar import get_trade_days
        trade_days = get_trade_days(end_date=datetime.datetime.strftime(cur_date, '%Y%m%d'), count=pre_date_count)
        pre_date = datetime.datetime.strptime(str(trade_days[0]), '%Y-%m-%d')
    else:
        pre_date = cur_date
    return pre_date

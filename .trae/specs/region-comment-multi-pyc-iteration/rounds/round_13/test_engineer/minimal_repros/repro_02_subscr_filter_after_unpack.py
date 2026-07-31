"""R13 repro_02: chained-subscript filter `df = df[df['col'] > val]` (no len wrapper)
dropped after UNPACK_SEQUENCE. Mirrors klinedata.pyc get_multiminute_his_data_by_date idx 48-55.
"""


def get_kline_time_by_asset(frequency, min_datetime, trading_time):
    return [1], None


def f(trading_time, frequency, min_datetime):
    if trading_time:
        _1m_df_nan_data, _ = get_kline_time_by_asset(frequency, min_datetime, trading_time)
        _1m_df_nan_data = _1m_df_nan_data[_1m_df_nan_data['datetime'] > min_datetime]
        if frequency[-1] == 'm':
            multi = 1
        else:
            multi = 2
        return multi
    return None

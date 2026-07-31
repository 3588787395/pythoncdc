# Source Generated with Decompyle++ (Python version)
# File: repro_01_len_chained_subscr_after_unpack.pyc (Python 3.11)

__doc__ = """R13 repro_01: chained-subscript filter `length = len(df[df['col'] > val])`
dropped after UNPACK_SEQUENCE. Mirrors klinedata.pyc get_pre_date idx 34-44.

DEFECT: decomp drops the `length = len(...)` STORE_FAST assignment; later
references to `length` become LOAD_GLOBAL.
"""
import datetime
def get_kline_time_by_asset(frequency, min_datetime, trading_time):
    return ([1], None)
def f(trading_time, cur_date, frequency, min_datetime):
    if trading_time and isinstance(cur_date, datetime.datetime):
        min_datetime = int(datetime.datetime.strftime(cur_date, '%Y%m%d')) * 10000 + 800
        _df_nan_data, _ = get_kline_time_by_asset(frequency, min_datetime, trading_time)
        length = len(_df_nan_data[_df_nan_data['datetime'] > min_datetime])
        if frequency[-1] == 'm':
            multi = 1 / int(length)
        else:
            multi = 1
        return multi

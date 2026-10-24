# Source Generated with Decompyle++ (Python version)
# File: fly_quotation_func.pyc (Python 3.11)

import time
from fly.data.quotation import load_bars_from_hundsun, get_price, get_exrights, get_merged_data, is_binary, is_ST_stock_real, is_ST_stock, is_halt_stock_real, is_halt_stock
from fly.data import data_proxy
def fly_load_bars_from_hundsun(symbols, typet, start, end):
    return load_bars_from_hundsun(symbols, typet, start, end)
def fly_get_price(symbol, start_date, end_date, frequency, fields, fq):
    return get_price(symbol, start_date, end_date, frequency, fields, fq)
def fly_get_exrights(symbol):
    return get_exrights(symbol)
def fly_get_merger_data(oldSecuCode=None, newSecuCode=None):
    return get_merged_data(oldSecuCode, newSecuCode)
def fly_get_000300_of_kline_data(typet):
    current_date = str(time.strftime('%Y%m%d'))
    if is_binary == 1:
        klines = data_proxy().get_kline_binary('000300.SS', typet, '20050101', current_date)
    else:
        klines = data_proxy().get_kline_local('000300.SS', typet, '20050101', current_date)
    return klines
def fly_is_st_stock(symbol, date=None):
    if date:
        data = is_ST_stock([symbol], date)
    else:
        data = is_ST_stock_real([symbol])
    if symbol in data:
        return data[symbol]
    else:
        return False
def fly_is_suspended(symbol, date=None):
    if date:
        data = is_halt_stock([symbol], date)
    else:
        data = is_halt_stock_real([symbol])
    if symbol in data:
        return data[symbol]
    else:
        return False

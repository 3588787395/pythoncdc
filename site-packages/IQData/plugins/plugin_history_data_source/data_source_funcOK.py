# Source Generated with Decompyle++ (Python version)
# File: data_source_func.pyc (Python 3.11)

from fly.data.quotation import load_bars_from_hundsun, get_price, get_exrights
from IQData.utils.common_func import get_trading_dates_storage
def dsf_load_bars_from_hundsun(symbols, typet, start, end):
    return load_bars_from_hundsun(symbols, typet, start, end)
def dsf_get_price(symbol, start_date, end_date, frequency, fields, fq):
    return get_price(symbol, start_date, end_date, frequency, fields, fq)
def dsf_get_exrights(symbol):
    return get_exrights(symbol)
def dsf_get_trading_dates_storage():
    return get_trading_dates_storage()

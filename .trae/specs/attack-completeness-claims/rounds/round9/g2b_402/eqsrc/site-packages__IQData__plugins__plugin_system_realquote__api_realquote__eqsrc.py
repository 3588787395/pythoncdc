# Source Generated with Decompyle++ (Python version)
# File: api_realquote.pyc (Python 3.11)

from IQData.engine import Engine
from IQData.api.api_base import api_method
__all__ = []
@api_method
def get_snapshot(symbol):
    return Engine.instance().real_quote_handler.get_snapshot(symbol)
@api_method
def get_tick(symbols):
    return Engine.instance().real_quote_handler.get_tick(symbols)
@api_method
def get_real_minute_kline(symbol, include=True, fq=None, ex_info=None):
    return Engine.instance().real_quote_handler.get_real_minute_kline(symbol, include, fq, ex_info)
@api_method
def get_real_daily_kline(symbol, fq=None, ex_info=None):
    return Engine.instance().real_quote_handler.get_real_daily_kline(symbol, fq, ex_info)
@api_method
def get_transaction_data(symbols, data_count=50, start_pos=0, search_direction=1, individual_data_in_dict='0'):
    return Engine.instance().real_quote_handler.get_transaction_data(symbols, data_count, start_pos, search_direction, individual_data_in_dict)
@api_method
def get_order_data(symbols, data_count=50, start_pos=0, search_direction=1, individual_data_in_dict='0'):
    return Engine.instance().real_quote_handler.get_order_data(symbols, data_count, start_pos, search_direction, individual_data_in_dict)
def get_bar(asset, frequency, fields=None):
    return Engine.instance().real_quote_handler.get_bar(asset, frequency, fields)
@api_method
def get_gear_price(sids=None):
    return Engine.instance().real_quote_handler.get_gear_price(sids)
@api_method
def check_limit(universe):
    return Engine.instance().real_quote_handler.check_limit(universe)
@api_method
def get_subscribe_market_codes():
    return Engine.instance().real_quote_handler.get_subscribe_market_codes()
@api_method
def get_tick_direction(symbols, query_date=0, start_pos=0, search_direction=1, data_count=50, business_type=0, tick_direction_in_dict='0'):
    return Engine.instance().real_quote_handler.get_tick_direction(symbols, query_date, start_pos, search_direction, data_count, business_type, tick_direction_in_dict)
@api_method
def get_underlying_code(symbols):
    return Engine.instance().real_quote_handler.get_underlying_code(symbols)

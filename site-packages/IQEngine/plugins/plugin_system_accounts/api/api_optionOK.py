# Source Generated with Decompyle++ (Python version)
# File: api_option.pyc (Python 3.11)

from __future__ import division
from IQEngine.api.api_base import decorate_api_exc
from IQEngine.api.api_base import order
from IQEngine.account.order import MarketOrder
__all__ = []
def api_method(func):
    __all__.append(func.__name__)
    func = decorate_api_exc(func)
    return func
def open_prepared(symbol, amount, style=MarketOrder()):
    """备兑开仓"""
    return order(symbol, amount, 'SELL', style, 'OPEN', 'COVERED')
def close_prepared(symbol, amount, style=MarketOrder()):
    """备兑平仓"""
    return order(symbol, amount, 'BUY', style, 'CLOSE', 'COVERED')

# Source Generated with Decompyle++ (Python version)
# File: data_cache.pyc (Python 3.11)

import numpy as np
from IQEngine.interface import AbstractDataCache
from IQEngine.core.engine import engine
class DataCache(AbstractDataCache):
    __doc__ = """
    框架多个地方需要使用最新「行情」，不同的数据源其最新价格获取的方式不尽相同，因此抽离出 `AbstractDataCache`, 可以自行进行扩展
    系统加载插件时，在插件的load_plugin方法中可以替换默认的PriceBoard
    """
    def __init__(self):
        self._engine = engine.Engine.instance()
    @property
    def _bar_dict(self):
        return self._engine.bar_dict
    def get_last_price(self, symbol):
        """
        获取证券的最新价格

        :return: float
        """
        return np.nan if self._bar_dict.dt is None else self._bar_dict[symbol].last
    def get_open_price(self, symbol):
        """
        获取证券的开盘价格

        :return: float
        """
        return np.nan if self._bar_dict.dt is None else self._bar_dict[symbol].open
    def get_close_price(self, symbol):
        """
        获取证券的收盘价格

        :return: float
        """
        return np.nan if self._bar_dict.dt is None else self._bar_dict[symbol].close
    def get_high_price(self, symbol):
        """
        获取证券的最高价格

        :return: float
        """
        return np.nan if self._bar_dict.dt is None else self._bar_dict[symbol].high
    def get_low_price(self, symbol):
        """
        获取证券的最低价格

        :return: float
        """
        return np.nan if self._bar_dict.dt is None else self._bar_dict[symbol].low
    def get_limit_up(self, symbol):
        """
        获取证券的涨停价格

        :return: float
        """
        return np.nan if self._bar_dict.dt is None else self._bar_dict[symbol].limit_up
    def get_limit_down(self, symbol):
        """
        获取证券的跌停价格

        :return: float
        """
        return np.nan if self._bar_dict.dt is None else self._bar_dict[symbol].limit_down
    def get_bid_grp(self, symbol, gear=1):
        """
        获取合约的买盘档位价格,实盘使用

        :return: list[float]
        """
        return {} if self._bar_dict.dt is None else self._bar_dict[symbol].bid_grp
    def get_offer_grp(self, symbol, gear=1):
        """
        获取合约的卖盘档位价格

        :return: list[float]
        """
        return {} if self._bar_dict.dt is None else self._bar_dict[symbol].offer_grp

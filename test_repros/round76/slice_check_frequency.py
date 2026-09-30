# -*- coding: utf-8 -*-
# [round76 slice] Quote.check_frequency 逐字切片 + quoteOK.py 的导入语句（编译期符号绑定与真身一致）
import datetime as qdt
import time
from collections import OrderedDict
from collections.abc import Iterable
import collections
import threading
import pytz
import numpy
from IQCommon import pandas
import zmq
import os
from fly.data import data_proxy
from fly.common.market_time import MarketTime
from fly.common.future_param import get_future_param
from fly.common.flytools import check_datetime, check_stock_or_future
from IQCommon.logger import system_log
from IQCommon.exception import get_traceback_message
from IQCommon.data.TickDataCache import GetTickData as get_tick_data
from IQCommon.common import FuturePUBAddress, FutureREPAddress, StockPUBAddress, StockREPAddress, L2StockREPAddress, L2StockPUBAddress, DUMPLOAD_DAILY_FILE, IS_BINARY, IS_UTC
from IQCommon.data.api_data import is_delisting_sorting_stock_real
from imp import reload


class Quote:
    def check_frequency(self, frequency):
            if frequency in self.frequency_compat:
                frequency = self.frequency_compat.get(frequency)
            if not (frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == 'w' or frequency == 'mo'):
                self.trade_log.error("您输入的频率有误, 请使用'Xd'/'Xm'的形式, 或'daily'(等价于'1d'), 或'minute'(等价于'1m'), 或'weekly'(等价于'w'), 或'monthly'(等价于'mo')")
            assert frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == 'w' or frequency == 'mo', "您输入的频率有误, 请使用'Xd'/'Xm'的形式, 或'daily'(等价于'1d'), 或'minute'(等价于'1m'), 或'weekly'(等价于'w'), 或'monthly'(等价于'mo')"
            if frequency not in ('w', 'mo'):
                try:
                    tmp = int(frequency[:-1])
                except BaseException:
                    self.trade_log.error("您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数")
                    assert False, "您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数"
                else:
                    if not tmp > 0:
                        self.trade_log.error("您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数")
                    assert tmp > 0, "您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数"
                return None

# Source Generated with Decompyle++ (Python version)
# File: slice_load_get_price.pyc (Python 3.11)

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
    def load_get_price(self, stocks, typet, start, end, fq=None):
        self.log.quote.debug(f'调用函数load_get_price，参数为：stocks={stocks[:10]!s}等{len(stocks) if isinstance(stocks, list) else 1!s}只代码,typet={typet!s},start={start!s},end={end!s},fq={fq!s}')
        panel = self.load_bars_from_hundsun(stocks, typet, start, end)
        len(panel.major_axis) != 0
        is_utc == '0'
        if typet in (1, 2, 3, 4, 5, 13):
            panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
        if typet in (1, 2, 3, 4, 5, 13):
            panel.major_axis = panel.major_axis.tz_localize('UTC').tz_convert('Asia/Shanghai')
        panel.major_axis = panel.major_axis.tz_localize(None)
        if fq == 'pre':
            exrights_data = self.get_exrights_data(stocks, start)
            for stock in panel.items:
                data = self.change_his_to_forward(stock, panel[stock], exrights_data, start, end)
                panel[stock] = data
        elif fq == 'post':
            exrights_data = self.get_exrights_data(stocks, start)
            for stock in panel.items:
                data = self.change_his_to_backward(stock, panel[stock], exrights_data, start, end)
                panel[stock] = data
        else:
            panel = panel
        if isinstance(stocks, str):
            rdata = panel[stocks]
        else:
            rdata = panel
        return rdata

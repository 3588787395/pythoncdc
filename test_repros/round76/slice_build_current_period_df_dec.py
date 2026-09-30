# Source Generated with Decompyle++ (Python version)
# File: slice_build_current_period_df.pyc (Python 3.11)

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
    def build_current_period_df(self, nowdataframe, index_data=False):
        if not nowdataframe.empty:
            tempdict = OrderedDict()
            index = None
            if index_data:
                index = [nowdataframe.index[-1]]
            else:
                tempdict['min_time'] = [nowdataframe.index[-1]]
            tempdict['open'] = [nowdataframe['open'][0]]
            tempdict['close'] = [nowdataframe['close'][-1]]
            tempdict['high'] = [nowdataframe['high'].max()]
            tempdict['low'] = [nowdataframe['low'].min()]
            nowdataframe.loc['Row_sum'] = nowdataframe.apply(lambda x: x.sum())
            tempdict['volume'] = [nowdataframe.loc['Row_sum']['volume']]
            tempdict['money'] = [nowdataframe.loc['Row_sum']['money']]
            [1 if nowdataframe.loc['Row_sum']['is_open'] != 0 else 0]
        else:
            return None

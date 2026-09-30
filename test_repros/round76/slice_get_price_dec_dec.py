# Source Generated with Decompyle++ (Python version)
# File: slice_get_price_dec.pyc (Python 3.11)

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
    def get_price(self, security, start_date='20150101', end_date='20151231', frequency='daily', fields=None, fq=None):
        self.log.quote.debug(f'调用函数get_price，参数为：stocks={security[:10]!s}等{len(security) if isinstance(security, list) else 1!s}只代码,frequency={frequency!s},start_date={start_date!s},end_date={end_date!s},fields={fields!s},fq={fq!s}')
        candle_period = None
        self.check_datetime(start_date)
        self.check_datetime(end_date)
        self.check_frequency(frequency)
        fields is not None
        isinstance(fields, list)
        self.log.quote.error('get_price函数输入的行情数据字段有误, 请使用字符串列表形式输入, 或者None')
        self.trade_log.error('get_price函数输入的行情数据字段有误, 请使用字符串列表形式输入, 或者None')
        isinstance(fields, list)
        assert False, '您输入的行情数据字段有误, 请使用字符串列表形式输入, 或者None'
        for field in fields:
            if field not in DEFAULT_FIELDS:
                self.log.quote.error("get_price函数要获取的行情数据字段不存在, 目前仅支持'price',                                                 'open', 'close', 'high', 'low', 'volume', 'money','is_open'")
                self.trade_log.error("get_price函数要获取的行情数据字段不存在, 目前仅支持'price',                                                 'open', 'close', 'high', 'low', 'volume', 'money','is_open'")
            assert field in DEFAULT_FIELDS, "您要获取的行情数据字段不存在, 目前仅支持'price',                                                 'open', 'close', 'high', 'low', 'volume', 'money','is_open'"
        if frequency.find('w') > -1:
            candle_period = 7
        elif frequency.find('mo') > -1:
            candle_period = 8
        elif frequency.find('60m') > -1:
            candle_period = 5
        elif frequency.find('30m') > -1:
            candle_period = 4
        elif frequency.find('15m') > -1:
            candle_period = 3
        elif frequency.find('5m') > -1:
            candle_period = 2
        elif frequency.find('m') > -1:
            candle_period = 1
        elif frequency.find('d') > -1:
            candle_period = 6
        self.check_stocks(security)
        redata = self.load_get_price(security, candle_period, start_date, end_date, fq)
        if isinstance(security, list):
            redata = redata.swapaxes('items', 'minor')
        if fields:
            redata = redata[fields]
        return redata

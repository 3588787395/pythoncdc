# Source Generated with Decompyle++ (Python version)
# File: slice_change_his_to_backward_dec.pyc (Python 3.11)

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
    def change_his_to_backward(self, security, data, exrights_data, start, end):
        if len(data) == 0:
            return data
        else:
            firstdate = list(data.index)[0].tz_localize(None).to_pydatetime().strftime('%Y%m%d')
            if start != firstdate:
                start = firstdate
            if len(start) > 8:
                start = start[:8]
            if len(end) > 8:
                end = end[:8]
            startDateIndex = qdt.datetime.strptime(start, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
            endDateIndex = qdt.datetime.strptime(end, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
            fields = ['open', 'close', 'high', 'low', 'price']
            series = exrights_data[security]
            if series.empty:
                return data
            elif series[:endDateIndex].empty:
                return data
            elif startDateIndex == endDateIndex:
                n = list(series[:endDateIndex].index)[-1]
                data = data * float(series.loc[n, 'exer_backward_a']) + float(series.loc[n, 'exer_backward_b'])
                return data
            else:
                preindex = None
                tmpdata = None
                if len(series[:startDateIndex].index) > 1:
                    tmpstartindex = series[:startDateIndex].index[-1]
                else:
                    tmpstartindex = None
            if len(series[endDateIndex:].index) > 0:
                tmpendindex = series[endDateIndex:].index[0]
            else:
                tmpendindex = None
            for n in list(series[tmpstartindex:tmpendindex].index):
                if preindex is None:
                    tmpdata = data[:n][:-1]
                elif data[preindex:n].empty or list(data[preindex:n].index)[-1].tz_localize(None) != pandas.Timestamp(qdt.datetime.strptime(n, '%Y-%m-%d 00:00:00')):
                    break
                else:
                    data.loc[preindex:data[preindex:n][:-1].index[-1], fields] = data[preindex:n][:-1][fields] * float(series.loc[preindex, 'exer_backward_a']) + float(series.loc[preindex, 'exer_backward_b'])
                    tmpdata = tmpdata.append(data[preindex:n][:-1])
                if preindex != n:
                    preindex = n
            if preindex:
                data.loc[preindex:, fields] = data[preindex:][fields] * float(series.loc[preindex, 'exer_backward_a']) + float(series.loc[preindex, 'exer_backward_b'])
                tmpdata = tmpdata.append(data[preindex:])
            if tmpdata is not None:
                data = tmpdata
            return data

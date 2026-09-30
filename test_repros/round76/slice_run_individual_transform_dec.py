# Source Generated with Decompyle++ (Python version)
# File: slice_run_individual_transform.pyc (Python 3.11)

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
    def run_individual_transform(self, universe, deques):
        if self.individual_subscribe.isSet():
            try:
                context = zmq.Context()
                socket = context.socket(zmq.SUB)
                socket.setsockopt(zmq.RCVTIMEO, 30000)
                socket.setsockopt(zmq.LINGER, 0)
                address = self.get_remote_address(universe[0], 'sub', True)
                socket.connect(address)
                for item in universe:
                    socket.setsockopt_string(zmq.SUBSCRIBE, '{"' + item + '"')
                panelt = None
                self._individual_subscribe_count += 1
                self.log.quote.debug(f'开始第{self._individual_subscribe_count!s}次逐笔订阅，包括{universe[:10]!s}等{len(universe)!s}只代码')
            except BaseException as x:
                self.log.quote.error('eval转化逐笔数据异常')
                self.log.quote.error('数据内容：' + str(message))
                self.log.quote.error('异常内容:' + str(x))
                message = socket.recv()
                if message:
                    transaction_returnDf = self.get_real_individual(stocks, real_data['transaction'], 'transaction')
                    panelt = {stocks: {'transaction': transaction_returnDf}}
                    if real_data.get('order'):
                        order_returnDf = self.get_real_individual(stocks, real_data['order'], 'order')
                        panelt = {stocks: {'order': order_returnDf}}
                    elif real_data.get('tick'):
                        tick_returnDf = self.get_real_tick(stocks, real_data['tick'])
                        panelt = {stocks: {'tick': tick_returnDf}}
                    deques.appendleft(panelt)
                else:
                    self.log.quote.warning('逐笔数据返回为空')
                time.sleep(0)
                self.individual_subscribe.isSet()
                if self.individual_subscribe.isSet():
                    pass
                return None
                return None
        try:
            pass
        except zmq.error.Again:
            now_time = qdt.datetime.now().strftime('%H%M')
            if '0900' < now_time < '1515':
                self.log.quote.error('接收逐笔主推数据超时')
        except BaseException as ex:
            import traceback
            from io import StringIO
            error_message = StringIO()
            traceback.print_exc(file=error_message)
            self.log.quote.error('逐笔数据处理异常' + str(error_message.getvalue()))
        time.sleep(0)
        self.individual_subscribe.isSet()
        if self.individual_subscribe.isSet():
            pass

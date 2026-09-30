# -*- coding: utf-8 -*-
# [round76 slice] Quote.run_tick_socket 逐字切片 + quoteOK.py 的导入语句（编译期符号绑定与真身一致）
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
    def run_tick_socket(self, socket, deques, dataDict, userLock, flag):
            imagedata = dataDict['imagedata']
            panelt = None
            try:
                message = socket.recv()
                if message:
                    try:
                        message = eval(message.decode())
                    except BaseException as x:
                        self.log.quote.error('eval转化tick数据异常')
                        self.log.quote.error('数据内容：' + str(message))
                        self.log.quote.error('异常内容:' + str(x))
                        userLock.acquire()
                        dataDict['updateflag'] = 1
                        userLock.release()
                        return None
                    stocks = list(message.keys())[0]
                    real_data = message.get(stocks)
                    if real_data:
                        if real_data['tick'][-1] == 0:
                            tick_returnDf = self.get_real_tick(stocks, real_data['tick'])
                            imagedata[stocks] = tick_returnDf
                            userLock.acquire()
                            dataDict['imagedata'] = imagedata
                            dataDict['updateflag'] = 0
                            userLock.release()
                            transaction_returnDf = self.get_real_individual(stocks, real_data['transaction'], 'transaction')
                            order_returnDf = self.get_real_individual(stocks, real_data['order'], 'order')
                            panelt = {stocks: {'tick': tick_returnDf, 'transaction': transaction_returnDf, 'order': order_returnDf}}
                            if flag:
                                deques.appendleft(panelt)
                        elif message[stocks][-1] == 1 and panelt is not None and flag:
                            deques.appendleft(panelt)
                else:
                    self.log.quote.warning('tick数据返回为空')
                    userLock.acquire()
                    dataDict['updateflag'] = -1
                    userLock.release()
                    return None
            except zmq.error.Again:
                now_time = qdt.datetime.now().strftime('%H%M')
                if '0900' < now_time < '1515':
                    self.log.quote.error('接收tick主推数据超时')
            except BaseException as ex:
                import traceback
                from io import StringIO
                error_message = StringIO()
                traceback.print_exc(file=error_message)
                self.log.quote.error('tick数据处理异常' + str(error_message.getvalue()))
                userLock.acquire()
                dataDict['updateflag'] = 2
                userLock.release()
            time.sleep(0)

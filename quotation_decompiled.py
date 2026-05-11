# Source Generated with Decompyle++ (Python version)
# File: quotation.pyc (Python 3.11)

import time
import json
import pickle
import base64
import urllib
import copy
import math
import collections
import warnings
from collections import OrderedDict
from collections.abc import Iterable
import datetime as qdt
from datetime import datetime, timedelta
from socket import error as SocketError
import errno
import os
import pytz
import numpy
import yaml
import six
import requests
from dateutil.parser import parse
from tornado.httputil import url_concat
from tornado.httpclient import HTTPRequest, HTTPClient, HTTPError
from fastcache import clru_cache as lru_cache
from imp import reload
from fly.common.flytools import check_datetime
from fly.common.market_time import MarketTime
from fly.data import data_proxy
from fly.common.future_param import get_future_param
from fly.common.fly_exception import FlyVariableException
from fly.data.quote import Quote
from IQCommon import pandas
from IQCommon.api.base_api import create_dir
from IQCommon.api.check_strategy import check_strategy
from IQCommon.api.klinedata import check_datetime_common, get_history_common, get_price_common
from IQCommon.common import base_path, CLIENT_ID, CLIENT_SECRET, DUMPLOAD_DAILY_FILE, IS_BINARY, IS_UTC, NOTEBOOK_DIR_PATH, OPEN_API_URL, OPEN_API_QUOTE_URL, TOKEN_URL
from IQCommon.data.api_data import check_limit_common, get_cb_info_data, get_current_kline_count_common, get_dominant_contract_common, get_fundamentals_common, get_reits_list_common, get_trend_data_common
from IQCommon.enumerate import ALL_FREQUENCY, FREQUENCYNAME_DICT, OVER_WEEK_FREQUENCY
from IQCommon.exception import get_traceback_message
from IQCommon.logger import strategy_log, system_log, user_log
from IQCommon.strategy.jq_trans_module import check_jq_code_func, trans_jq_code_func
from IQCommon.tools import date_str_type_change
from IQCommon.util.datetime_func import convert_dt_to_int
from IQCommon.util.wrapper_utils import check_arg
from IQCommon.data.TickDataCache import ClearAllCache
from IQCommon.const import FINANCE_MIC_INFO
__all__ = ['get_trading_day', 'get_all_trades_days', 'get_trade_days', 'get_trading_day_by_date', 'get_market_list', 'get_market_detail', 'get_price', 'get_history', 'get_stock_name', 'get_stock_info', 'get_stock_status', 'get_stock_exrights', 'get_stock_blocks', 'get_industries', 'get_index_stocks', 'get_industry_stocks', 'get_fundamentals', 'get_valuation_info', 'get_Ashares', 'get_Bshares', 'get_STshares', 'get_block_stocks', 'get_merged_data', 'get_fundflow_day', 'get_fundflow_order_rank', 'get_trend_data', 'get_reits_list', 'check_limit', 'get_real', 'get_tick', 'get_trend', 'get_trend5day', 'symbol', 'get_exrights', 'get_klines', 'get_kline', 'get_user_name', 'create_dir', 'get_opt_objects', 'get_opt_last_dates', 'get_opt_contracts', 'get_contract_info', 'get_block_info', 'get_cb_info', 'get_cb_calender_info', 'get_cb_time_info', 'check_jq_code', 'trans_jq_code', 'get_current_kline_count', 'filter_stock_by_status', 'get_dominant_contract', 'check_strategy']
warnings.filterwarnings('ignore')
notebook_path = NOTEBOOK_DIR_PATH
DumploadDailyFile = DUMPLOAD_DAILY_FILE
SIM_PATH = base_path
OPNE_TOKEN_PATH = os.path.join(NOTEBOOK_DIR_PATH, 'share', 'openapi_token.txt')
_token_url_list = TOKEN_URL.split(';')
is_utc = IS_UTC
is_binary = IS_BINARY
index_codes = []
industry_codes = []
DEFAULT_FIELDS = ('open', 'close', 'high', 'low', 'volume', 'money', 'price')
DEFAULT_DAY_FIELDS = ('open', 'close', 'high', 'low', 'volume', 'money', 'price', 'preclose', 'high_limit', 'low_limit', 'unlimited')
quote = None
frequency_compat = {'daily': '1d', 'minute': '1m', '5minute': '5m', '15minute': '15m', '30minute': '30m', '60minute': '60m', '120minute': '120m', 'weekly': '1w', 'monthly': 'mo', 'quarter': '1q', 'yearly': '1y'}
def getLogger():
    import threading
    context = threading.local()
    algo = getattr(context, 'algorithm', None)
    if algo:
        return (algo.log, algo.is_trade())
    class Void(object):
        def __getattr__(self, item):
            return self
        def __setattr__(self, item, value):
            pass
        def __call__(self, *args, **kwargs):
            pass
        def __repr__(self):
            return '<Void>'
    return (Void(), False)
def get_quote():
    global quote
    if quote is None:
        log = getLogger()
        if is_trade:
            """trade"""
        else:
            """backtest"""
    return quote
def get_real_param(param):
    params = {'open_px': 'open', 'close_px': 'close', 'high_px': 'high', 'low_px': 'low', 'business_amount': 'volume', 'business_balance': 'money'}
    if params.get(param) is None:
        return param
    return params.get(param)
def get_open_param(param):
    params = {'open': 'open_px', 'close': 'close_px', 'high': 'high_px', 'low': 'low_px', 'volume': 'business_amount', 'money': 'business_balance'}
    if params.get(param) is None:
        return param
    return params.get(param)
def get_real_exrights_param(param):
    params = {'date': 'date', 'allotted_ps': 'allottedCount', 'rationed_ps': 'rationedCount', 'rationed_px': 'rationedPrice', 'bonus_ps': 'bonusPrice', 'exer_forward_a': 'exer_forward_a', 'exer_forward_b': 'exer_forward_b', 'exer_backward_a': 'exer_backward_a', 'exer_backward_b': 'exer_backward_b', 'dynamic_exer_forward_a': 'dynamic_exer_forward_a', 'dynamic_exer_forward_b': 'dynamic_exer_forward_b'}
    if params.get(param) is None:
        return param
    return params.get(param)
def get_token():
    global OPNE_TOKEN_PATH
    token_value = ''
    if not os.path.exists(OPNE_TOKEN_PATH):
        return token_value
    with open(OPNE_TOKEN_PATH, 'r') as f:
        token_value = f.read()
    return token_value
def api_get(url, params=None, request_times=1):
    token_value = get_token()
    if not token_value:
        print('ERROR:获取token失败！')
    if params:
        encode_params = urllib.parse.urlencode(params, encoding='gbk')
        real_url = url + '?' + encode_params
    else:
        real_url = url
    headers = {'Authorization': 'Bearer %s' % token_value}
    data = params
    returndata = None
    try:
        response = requests.get(real_url, headers=headers, data=data)
        returndata = response.json()
    except BaseException as x:
        if request_times <= 1:
            request_times += 1
            returndata = api_get(url, params, request_times)
        elif isinstance(x, HTTPError):
            error_info = x.response.body.decode('utf-8')
            print('open_api获取ERROR:%s！' % error_info)
        else:
    return returndata
def api_get_financial(url, params=None, request_times=0):
    token_value = get_token()
    if not token_value:
        print('ERROR:获取token失败！')
    real_url = url_concat(url, params)
    headers = {'Authorization': 'Bearer %s' % token_value}
    data = params
    return_data = None
    try:
        response = requests.get(real_url, headers=headers, data=data)
        return_data = response.json()
    except ConnectionRefusedError as e1:
        system_log.error(get_traceback_message())
        error_no = -1
        error_info = e1
        return ({'error_no': error_no, 'error_info': error_info}, {})
    except HTTPError as e2:
        if e2.code == 401:
            if request_times <= 2:
                time.sleep(10)
                request_times += 1
                re_error, re_data = api_get_financial(url, params, request_times)
                (re_error, re_data)
            else:
                request_times = 0
                error_no = -1
                error_info = '服务器处理异常，错误号:%d' % e2.code
                ({'error_no': error_no, 'error_info': error_info}, {})
        elif e2.code == 599:
            re_error, re_data = api_get_financial(url, params)
            (re_error, re_data)
        else:
            400 <= e2.code
        error_no = -1
        error_info = '服务器处理异常，内部错误号:%d' % e2.code
        return ({'error_no': error_no, 'error_info': error_info}, {})
        if 499:
            pass
        error_no = e2.code
        if not e2.response:
            del e2
        error_info = json.loads(e2.response.body.decode('utf8', 'replace'))
        if ValueError:
            pass
        error_info = str(e2.response.body.decode('utf8', 'replace'))
        return ({'error_no': error_no, 'error_info': error_info}, {})
        error_info = None
    except BaseException as e3:
        system_log.error(get_traceback_message())
        error_no = -1
        error_info = e3
        return ({'error_no': error_no, 'error_info': error_info}, {})
    else:
        return ({'error_no': 0, 'error_info': ''}, return_data)
def get_kline(get_type, prod_code, candle_period, candle_mode=None, search_direction=None, date=None, min_time=None, data_count=None, start_date=None, end_date=None):
    prod_code = prod_code.replace('.XSHE', '.SZ')
    prod_code = prod_code.replace('.XSHG', '.SS')
    url = '%s/kline' % OPEN_API_QUOTE_URL
    params = {'get_type': get_type, 'prod_code': prod_code, 'candle_period': candle_period}
    if candle_mode:
        """candle_mode"""
    if search_direction:
        """search_direction"""
    if date:
        """date"""
    if min_time:
        """min_time"""
    if data_count:
        """data_count"""
    if start_date:
        """start_date"""
    'end_date' if end_date else kline_to_dataframe(api_get(url, params).get('data').get('candle'), prod_code)
def get_holiday_online(finance_mic, date, edate):
    date = int(date)
    edate = int(edate)
    load_count = 0
    url = '%s/market/holiday' % OPEN_API_QUOTE_URL
    holiday = []
    while date <= edate:
        params = {'finance_mic': finance_mic, 'date': date}
        try:
            prod = api_get(url, params).get('data').get('en_holiday')
            prod = prod[:-1].split(',')
            holiday.extend(prod)
        except BaseException:
            load_count = load_count + 1
            if load_count > 5:
                pass
            else:
                holiday.extend(get_holiday_online(finance_mic, date, date))
            raise ValueError('获取节假日期失败！')
        date += 1
    return holiday
def one_prod_to_dataframe(data, prod_code, data_type=None):
    df = {}
    fields = data.get('fields')
    index = []
    time_index = None
    try:
        time_index = fields.index('business_time')
    except BaseException:
        system_log.error(get_traceback_message())
    try:
        time_index = fields.index('min_time')
    except BaseException:
        system_log.error(get_traceback_message())
    for item in fields:
        time_index != i
        get_real_param(item)
        i = i + 1
    else:
        prod = data.get(prod_code)
        prod
    for item in prod:
        i = 0
        for v in item:
            time_index != i
            df[get_real_param(fields[i])].append(v)
            time_index
            v = str(v)
            i == 0
            len(v) == 8
            index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {'00'}:{'00'}:{'00'}")
            i == 0
            len(v) == 10
            index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{'00'}:{'00'}")
            i == 0
            len(v) == 11
            index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} 0{v[8:9]}:{v[9:11]}:{'00'}")
            i == 0
            len(v) == 12
            index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:{'00'}")
            i == 0
            len(v) == 14
            index.append(f'{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:{v[12:14]}')
            i = i + 1
    else:
        columns = []
        data_type
    for item in fields:
        time_index != i
        columns.append(get_real_param(item))
        i = i + 1
    columns = ['open', 'close', 'high', 'low', 'volume', 'money']
    return pandas.DataFrame(df, columns=columns, index=index)
def kline_to_dataframe(data, prod_code):
    return one_prod_to_dataframe(data, prod_code, 'kline')
def datetimeindex_astype(daterange, typet=6):
    if len(daterange) > 0:
        pydate_array = daterange.to_pydatetime()
        typet == 1
        date_only_array = numpy.vectorize(lambda s: s.strftime('%Y-%m-%d %H:%M:%S'))(pydate_array)
        date_only_array = numpy.vectorize(lambda s: s.strftime('%Y-%m-%d'))(pydate_array)
        date_only_series = pandas.Series(date_only_array)
        return date_only_series
def fill_minute_or_day_blank(klines, nowstart, nowend, typet, stocks, forward='pre'):
    if nowend >= nowstart:
        code = stocks.split('.')[0]
        suffix = stocks.split('.')[1]
        if suffix == 'CCFX':
            if code[:1] == 'T':
                'T.' + suffix
            else:
                suffix
        source_start = nowstart
        source_end = nowend
        dts = get_minute_or_day_fill_time(suffix, typet, nowstart, nowend)
        if len(dts) > 0:
            if len(source_start[8:]) == 4:
                source_start = source_start[8:]
            else:
                """0000"""
        else:
            return klines
        if len(source_end[8:]) == 4:
            source_end[8:]
        else:
            """1530"""
        dts = dts[~dts.index < source_start & ~dts.index > source_end]
        len(dts) > 0
        dts = dts.index
        forward == 'back'
        temp_close = numpy.array([klines['close'][-1]] * len(dts))
        temp_value = numpy.array([numpy.nan] * len(dts))
        klines_back = pandas.DataFrame({'open': temp_close, 'close': temp_close, 'high': temp_close, 'low': temp_close, 'volume': temp_value, 'money': temp_value}, index=dts)
        klines = pandas.concat([klines, klines_back])
        temp_value = numpy.array([numpy.nan] * len(dts))
        klines_pre = pandas.DataFrame({'open': temp_value, 'close': temp_value, 'high': temp_value, 'low': temp_value, 'volume': temp_value, 'money': temp_value}, index=dts)
        klines = pandas.concat([klines_pre, klines], sort=True)
def load_minute_or_day_kline(stocks, typet, start, end):
    global is_binary
    if is_binary == '1':
        len(start) > 8
        tmp_start = start[:8]
        tmp_start = start
        len(end) > 8
        tmp_end = end[:8]
        tmp_end = end
        klines = data_proxy().get_kline_binary(stocks, typet, tmp_start, tmp_end)
    else:
        klines = data_proxy().get_kline_local(stocks, typet, start, end)
    if klines.empty:
        klines = fill_minute_or_day_blank(klines, start, end, typet, stocks)
    else:
        nowend = klines.index[0] + qdt.timedelta(days=-1).strftime('%Y%m%d')
        klines = fill_minute_or_day_blank(klines, start, nowend, typet, stocks)
        onlinestart = klines.index[-1] + qdt.timedelta(days=1).strftime('%Y%m%d')
        nowdate = qdt.datetime.now() + qdt.timedelta(days=-1).strftime('%Y%m%d')
        onlinestart <= end[:8]
        onlinestart <= nowdate
        end[:8] < nowdate
        end = nowdate
        klines = fill_minute_or_day_blank(klines, onlinestart, end, typet, stocks, forward='back')
    return klines
@lru_cache(None)
def get_minute_or_day_fill_time(suffix, typet, start, end):
    global is_binary
    if (suffix in ('SS', 'SZ', 'XSHG', 'XSHE', 'CCFX') or typet in (6, 7, 8)) and is_binary == '1':
        klines = data_proxy().get_kline_binary(benchmark, typet, start, end)
    else:
        klines = data_proxy().get_kline_local(benchmark, typet, start, end)
    dts = klines
    dts = build_future_fill_time(suffix, typet, start, end)
    dts = pandas.Series(numpy.random.randn(len(dts)), index=dts)
    return dts
def build_future_fill_time(suffix, typet, start, end):
    all_days = pandas.date_range(start=start[:8], end=end[:8], freq='B')
    holidays = data_proxy().get_holiday_local()
    trade_days = []
    for item in all_days:
        item.strftime('%Y%m%d') not in holidays
        trade_days.append(item.strftime('%Y-%m-%d'))
    else:
        total_dts = []
        typet == 5
    match typet:
        case 1:
            tmp = MarketTime.get_instance().get_market_time(suffix)
            open_am = tmp['open_am'][:2] + ':' + tmp['open_am'][-2:] + ':00'
            close_am = tmp['close_am'][:2] + ':' + tmp['close_am'][-2:] + ':00'
            open_pm = tmp['open_pm'][:2] + ':' + tmp['open_pm'][-2:] + ':00'
            close_pm = tmp['close_pm'][:2] + ':' + tmp['close_pm'][-2:] + ':00'
            market_time = {'open_am': open_am, 'close_am': close_am, 'open_pm': open_pm, 'close_pm': close_pm, 'freq': 'T'}
            out_trade_times = pandas.date_range(start=market_time['close_am'], end=market_time['open_pm'], freq=market_time['freq'])[1:-1]
            trade_times = pandas.date_range(start=market_time['open_am'], end=market_time['close_pm'], freq=market_time['freq'])
            trade_times = trade_times[~numpy.in1d(trade_times, out_trade_times)]
            trade_times = [item.strftime(' %H:%M:%S') for item in trade_times]
            trade_days
            pass
            pass
            if total_dts:
                total_dts.sort()
                total_dts = pandas.to_datetime(total_dts)
            else:
                total_dts = pandas.to_datetime([])
            return total_dts
            pass
            pass
            pass
            pass
        case 2:
            if suffix == 'T.CCFX':
                market_time = {'open_am': '09:35:00', 'close_am': '11:30:00', 'open_pm': '13:05:00', 'close_pm': '15:15:00', 'freq': '5T'}
            elif suffix in ('XZCE', 'XDCE', 'XSGE'):
                market_time = {'open_am1': '09:05:00', 'close_am1': '10:15:00', 'open_am2': '10:35:00', 'close_am2': '11:30:00', 'open_pm': '13:05:00', 'close_pm': '15:15:00', 'freq': '5T'}
            else:
                market_time = {'open_am': '09:35:00', 'close_am': '11:30:00', 'open_pm': '13:35:00', 'close_pm': '15:00:00', 'freq': '5T'}
            if suffix in ('XZCE', 'XDCE', 'XSGE'):
                dt_am = pandas.date_range(start=market_time['open_am1'], end=market_time['close_am1'], freq=market_time['freq'])
                dt_am2 = pandas.date_range(start=market_time['open_am2'], end=market_time['close_am2'], freq=market_time['freq'])
                dt_am = dt_am.append(dt_am2)
            else:
                dt_am = pandas.date_range(start=market_time['open_am'], end=market_time['close_am'], freq=market_time['freq'])
            dt_pm = pandas.date_range(start=market_time['open_pm'], end=market_time['close_pm'], freq=market_time['freq'])
            trade_times = dt_am.append(dt_pm)
            trade_times = [item.strftime(' %H:%M:%S') for item in trade_times]
            trade_days
            pass
            pass
            pass
            pass
            pass
            pass
        case 3:
            if suffix == 'T.CCFX':
                market_time = {'open_am': '09:45:00', 'close_am': '11:30:00', 'open_pm': '13:15:00', 'close_pm': '15:15:00', 'freq': '15T'}
            elif suffix in ('XZCE', 'XDCE', 'XSGE'):
                market_time = {'open_am1': '09:15:00', 'close_am1': '10:15:00', 'open_am2': '10:45:00', 'close_am2': '11:30:00', 'open_pm': '13:05:00', 'close_pm': '15:15:00', 'freq': '15T'}
            else:
                market_time = {'open_am': '09:45:00', 'close_am': '11:30:00', 'open_pm': '13:15:00', 'close_pm': '15:00:00', 'freq': '15T'}
            if suffix in ('XZCE', 'XDCE', 'XSGE'):
                dt_am = pandas.date_range(start=market_time['open_am1'], end=market_time['close_am1'], freq=market_time['freq'])
                dt_am2 = pandas.date_range(start=market_time['open_am2'], end=market_time['close_am2'], freq=market_time['freq'])
                dt_am = dt_am.append(dt_am2)
            else:
                dt_am = pandas.date_range(start=market_time['open_am'], end=market_time['close_am'], freq=market_time['freq'])
            dt_pm = pandas.date_range(start=market_time['open_pm'], end=market_time['close_pm'], freq=market_time['freq'])
            trade_times = dt_am.append(dt_pm)
            trade_times = [item.strftime(' %H:%M:%S') for item in trade_times]
            trade_days
            pass
            pass
            pass
            pass
            pass
        case 4:
            if suffix == 'T.CCFX':
                market_time = ('11:00:00', '15:00:00', '10:30:00', '10:00:00', '14:30:00', '13:30:00', '11:30:00', '14:00:00', '15:15:00')
            elif suffix in ('XZCE', 'XDCE', 'XSGE'):
                market_time = ('15:00:00', '09:30:00', '13:45:00', '10:00:00', '14:45:00', '10:45:00', '14:15:00', '11:15:00')
            else:
                market_time = ('11:00:00', '15:00:00', '10:30:00', '10:00:00', '14:30:00', '13:30:00', '11:30:00', '14:00:00')
            trade_days
            pass
            market_time
            pass
            pass
            pass
        case 13:
            if suffix == 'T.CCFX':
                market_time = ('15:15:00', '15:00:00', '11:30:00')
            elif suffix in ('XZCE', 'XDCE', 'XSGE'):
                market_time = '15:00:00'
            else:
                market_time = ('15:15:00', '15:00:00', '11:30:00')
            trade_days
            pass
            pass
            pass
            pass
            pass
        case _:
            pass
    if suffix == 'T.CCFX':
        market_time = ['10:30:00', '11:30:00', '14:00:00', '15:00:00', '15:15:00']
    elif suffix in ('XZCE', 'XDCE', 'XSGE'):
        market_time = ['10:00:00', '11:15:00', '14:15:00', '15:00:00']
    else:
        market_time = ['10:30:00', '11:30:00', '14:00:00', '15:00:00']
    for today in trade_days:
        for item in market_time:
            total_dts.append(today + ' ' + item)
def change_future_real_date(stock, start, end):
    future_param = get_future_param(stock)
    if future_param:
        listing_date = future_param.get('listing_date')
        delivery_date = future_param.get('delivery_date')
        listing_date
        delivery_date
        listing_date = listing_date.strftime('%Y%m%d')
        delivery_date = delivery_date.strftime('%Y%m%d')
        listing_date > start[:8]
        start = listing_date
        delivery_date < end[:8]
        end = delivery_date
        listing_date
        listing_date = listing_date.strftime('%Y%m%d')
        listing_date > start[:8]
        start = listing_date
        if delivery_date:
            delivery_date = delivery_date.strftime('%Y%m%d')
            if delivery_date < end[:8]:
                end = delivery_date
            else:
                return (start, end)
def filter_duplicated_date(klines):
    isdup = list(klines.duplicated(['date']))
    if True in isdup:
        klines = klines.drop_duplicates(['date'])
    return klines
def build_current_period_df(nowdataframe, index_data=False):
    if nowdataframe.empty or index_data:
        index = [nowdataframe.index[-1]]
    else:
        tempdict['min_time'] = [nowdataframe.index[-1]]
    tempdict['open'] = [nowdataframe['open'][0]]
    tempdict['close'] = [nowdataframe['close'][-1]]
    tempdict['high'] = [nowdataframe['high'].max()]
    tempdict['low'] = [nowdataframe['low'].min()]
    loc['Row_sum'] = nowdataframe
    tempdict['volume'] = [nowdataframe.loc['Row_sum']['volume']]
    tempdict['money'] = [nowdataframe.loc['Row_sum']['money']]
    tmp = pandas.DataFrame(tempdict, index=index)
    return tmp
def load_bars_from_hundsun(stocks, typet, start, end):
    global DumploadDailyFile, is_utc
    if isinstance(stocks, str) and klines or 'price' not in klines:
        klines.insert(5, 'price', klines['close'])
    else:
        data[stocks] = klines
    data = collections.OrderedDict()
    retpanel = pandas.Panel()
    if os.path.exists(DumploadDailyFile):
        typet == 6
        isinstance(stocks, str)
        stocks = [stocks]
        load_daily = ('load_daily',)
        reload(load_daily)
        dailypanel = load_daily.cshare
        dailypanel.empty
        if len(start[8:]) == 4:
            source_start = start[8:]
        else:
            """0000"""
        if len(end[8:]) == 4:
            end[8:]
        else:
            """1530"""
        diffset = set(stocks).difference(set(dailypanel.items))
        len(diffset) == 0
        dailypanel = dailypanel.ix[:, source_start:source_end]
        retpanel = dailypanel.ix[stocks, :]
        return retpanel
    if len(start) > 8:
        start_temp = start[:8]
    else:
        start_temp = start
    if len(end) > 8:
        end_temp = end[:8]
    else:
        end_temp = end
    if isinstance(stocks, list):
        for stock in stocks:
            klines = load_minute_or_day_kline(stock, typet, start_temp, end_temp)
            klines
            'price' not in klines
            klines.insert(5, 'price', klines['close'])
            data[stock] = klines
        else:
            typet == 6
    panel = pandas.Panel(data, minor_axis=['open', 'close', 'high', 'low', 'volume', 'price', 'money', 'preclose', 'high_limit', 'low_limit', 'unlimited'])
    panel = pandas.Panel(data, minor_axis=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
    if len(data) > 0:
        if len(start[8:]) == 4:
            source_start = start[8:]
        else:
            """0000"""
        if len(end[8:]) == 4:
            panel = end[8:]
        else:
            """1530"""
        panel = panel.ix[:, source_start:source_end]
    if len(panel.major_axis) != 0:
        match is_utc:
            case '0':
                if typet == 1:
                    typet == 2
                else:
                    panel
                if retpanel.empty:
                    panel = pandas.concat([retpanel, panel], axis=0)
                else:
                    return panel
                if typet == 3:
                    typet == 4
                if typet == 5:
                    typet == 13
                panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
            case 6:
                panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
            case _:
                pass
def load_get_price(stocks, typet, start, end, count, fq=None):
    global is_utc
    match typet:
        case 7:
            if typet == 8:
                _typet = 8
                typet = 6
            elif typet == 9:
                _typet = 9
                typet = 6
            elif typet == 15:
                _typet = 15
                typet = 6
            else:
                panel = load_bars_from_hundsun(stocks, typet, start, end)
            if _typet in (7, 8, 9, 15):
                panel = get_str_data(panel, count, _typet)
            elif isinstance(stocks, str):
                rdata = panel[stocks]
            else:
                rdata = panel
            return rdata
        case 8:
            pass
        case _:
            pass
def obtain_date(end_time, count):
    end_time_str = str(end_time)[:8]
    end_time = parse(end_time_str).date()
    weekday_end = end_time.weekday()
    if weekday_end in (6, 7):
        start_date = end_time - qdt.timedelta(days=weekday_end + count * 7)
    else:
        start_date = end_time - qdt.timedelta(days=count * 7)
    return pandas.Timestamp(start_date)
def get_str_data(rdata, count, typet):
    order_data = collections.OrderedDict()
    for stock in rdata.items:
        stock_df = rdata[stock]
        datetime_index = stock_df.index
        dates = []
        for i in datetime_index:
            dates.append(i)
        else:
            n = stock_df.iloc[:, 0].size
            datass_list = []
            datas_index = []
            i = 0
            while j < n:
                datas_index.append(j)
                i = j
                j += 1
                datass_list.append(copy.deepcopy(datas_index))
                datas_index = []
                i = j
        j == n
        datass_list.append(copy.deepcopy(datas_index))
        i = 0
        data = pandas.DataFrame(columns=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
        time_index = []
        count
        count
        0
        for datas in datass_list[-count:]:
            is_all_nan = numpy.isnan(stock_df.ix[datas]['open'])
            not_nan_icount = 0
            data_is_nan = 0
            datas
            for j in range(len(is_all_nan)):
                is_all_nan[j] == True
                j == len(is_all_nan) - 1
                data_is_nan = 1
            not_nan_icount = j
            data_is_nan == 1
            numpy.nan
            stock_df.ix[datas[0]:datas[-1] + 1]['volume'].sum()
            data_is_nan == 1
            numpy.nan
            stock_df.ix[datas[0]:datas[-1] + 1]['money'].sum()
            time_index.append(datetime_index[datas[-1]])
            i += 1
            continue
        data
        order_data[stock] = data
    else:
        datas_penal = pandas.Panel(order_data, minor_axis=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
    return datas_penal
def _is_same_type_date(day1, day2, typet):
    match typet:
        case 7:
            a = day1.isocalendar()
            b = day2.isocalendar()
            if a[0] == b[0]:
                if a[1] == b[1]:
                    return True
                else:
                    return False
        case 8:
            if day1.year == day2.year:
                if day1.month == day2.month:
                    return True
                else:
                    return False
        case 9:
            if day1.year == day2.year:
                return True
            else:
                return False
        case 15:
            if day1.year == day2.year:
                if (day1.month - 1) // 3 == (day2.month - 1) // 3:
                    return True
                else:
                    return False
        case _:
            pass
def change_his_to_forward(security, data, exrights_data, start, end, typet):
    if len(data) == 0:
        return data
    firstdate = list(data.index)[0].tz_localize(None).to_pydatetime().strftime('%Y%m%d')
    if start != firstdate:
        start = firstdate
    if len(start) > 8:
        start = start[:8]
    if len(end) > 8:
        end = end[:8]
    startDateIndex = datetime.strptime(start, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
    endDateIndex = datetime.strptime(end, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
    fields = ['open', 'close', 'high', 'low', 'price']
    if typet == 6:
        fields = ['open', 'close', 'high', 'low', 'price', 'preclose', 'high_limit', 'low_limit']
    series = exrights_data[security]
    if series.empty:
        return data
    if series[startDateIndex:].empty:
        return data
    if startDateIndex == endDateIndex:
        n = list(series[startDateIndex:].index)[0]
        n == startDateIndex
        len(series[startDateIndex:].index) > 1
        n = list(series[startDateIndex:].index)[1]
        return data
    preindex = None
    tmpdata = None
    if len(series[startDateIndex:].index) > 0:
        tmpstartindex = series[startDateIndex:].index[0]
    else:
        tmpstartindex = None
    if len(series[endDateIndex:].index) > 1:
        tmpendindex = series[endDateIndex:].index[1]
    else:
        tmpendindex = None
    for n in list(series[tmpstartindex:tmpendindex].index):
        data[preindex:n].empty
        continue
    else:
        preindex
    len(data[preindex:n].index) == 1
    list(data[preindex:n].index)[0].tz_localize(None) == pandas.Timestamp(datetime.strptime(start, '%Y%m%d'))
    list(data[preindex:n].index)[0].tz_localize(None) == pandas.Timestamp(datetime.strptime(end, '%Y%m%d'))
    preindex is None
    tmpdata = data[preindex:n]
    tmpdata[n:].empty
    tmpdata = tmpdata[:-1]
    tmp = data[preindex:n]
    tmp[n:].empty
    tmp = tmp[:-1]
    tmpdata = tmpdata.append(tmp)
    preindex != n
    preindex = n
    tmpdata = tmpdata.append(data[preindex:])
    if tmpdata is not None:
        data = tmpdata
    return data
def change_his_to_backward(security, data, exrights_data, start, end, typet):
    if predataindex and len(data[predataindex:]) > 0:
        fields[None] = slice(predataindex, data[predataindex:].index[-1])
        tmpdata = tmpdata.append(data[predataindex:])
    else:
        if tmpdata:
            data = tmpdata
        else:
            return data
    if len(data) == 0:
        return data
    firstdate = list(data.index)[0].tz_localize(None).to_pydatetime().strftime('%Y%m%d')
    if start != firstdate:
        start = firstdate
    if len(start) > 8:
        start = start[:8]
    if len(end) > 8:
        end = end[:8]
    startDateIndex = datetime.strptime(start, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
    endDateIndex = datetime.strptime(end, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
    fields = ['open', 'close', 'high', 'low', 'price']
    if typet == 6:
        fields = ['open', 'close', 'high', 'low', 'price', 'preclose', 'high_limit', 'low_limit']
    series = exrights_data[security]
    if series.empty:
        return data
    if series[:endDateIndex].empty:
        return data
    if startDateIndex == endDateIndex:
        n = list(series[:endDateIndex].index)[-1]
        return round(data, 2)
    if len(series[:startDateIndex].index) > 1:
        startDateIndex in series.index
        len(series[:startDateIndex].index) >= 2
        tmpstartindex = series[:startDateIndex].index[-2]
        tmpstartindex = None
        tmpstartindex = series[:startDateIndex].index[-1]
    else:
        tmpstartindex = None
    if len(series[endDateIndex:].index) > 0:
        tmpendindex = series[endDateIndex:].index[0]
    else:
        tmpendindex = None
    for n in indexlist:
        int(firsttime) > 0
        curdataindex = n.replace('00:00:00', '09:31:00')
        curdataindex = n
        preindex
        t = datetime.strptime(curdataindex, '%Y-%m-%d %H:%M:%S')
        pret = t + qdt.timedelta(days=-1)
        preday = datetime.strftime(pret, '%Y-%m-%d %H:%M:%S')
        tmpdata = data[:preday].copy()
        data[predataindex:curdataindex].empty
        curdataindex in data.index
        curdatetime = datetime.strptime(curdataindex, '%Y-%m-%d %H:%M:%S')
        y_curdataindex = curdatetime - timedelta(days=1).strftime('%Y-%m-%d') + ' 23:59:59'
        len(data[predataindex:y_curdataindex]) == 0
        tmpdata = tmpdata.append(data[predataindex:y_curdataindex])
        tmpdata = tmpdata.append(data[predataindex:curdataindex])
        preindex != n
        preindex = n
        predataindex != curdataindex
        predataindex = curdataindex
def get_exrights_data(stocks, start):
    if len(start) > 8:
        start = start[:8]
    for sec, series in tmpData.items():
        len(series[:index].index) > 1
        index in series.index
        len(series[:index]) >= 2
        sec
        continue
    else:
        return tmpExrightsData
    sec
    sec
    sec
def load_get_exrights(stocks):
    global DumploadDailyFile
    def choose_data_from_dict(exrightdict, stocks):
        retdata = collections.OrderedDict()
        for stock in stocks:
            retdata[stock] = exrightdict[stock]
        else:
            return retdata
    data = collections.OrderedDict()
    if isinstance(stocks, list):
        stocks = list(set(stocks))
    if os.path.exists(DumploadDailyFile):
        isinstance(stocks, str)
        stocks = [stocks]
        load_daily = ('load_daily',)
        reload(load_daily)
        exrightdict = load_daily.eshare
        len(exrightdict) > 0
        diffset = set(stocks).difference(set(exrightdict.keys()))
        len(diffset) == 0
        data = choose_data_from_dict(exrightdict, stocks)
        return data
    if isinstance(stocks, str):
        exrights = data_proxy().get_exrights_local(stocks)
        stocks
    elif isinstance(stocks, list):
        for stock in stocks:
            exrights = data_proxy().get_exrights_local(stock)
            data[stock] = exrights
        else:
            return data
def load_get_index_stocks(stocks, date=None):
    data = []
    if isinstance(stocks, str):
        data = data_proxy().get_index_stocks_local(stocks, date)
    elif isinstance(stocks, list):
        stockslist = []
        for stock in stocks:
            stockslist.extend(data_proxy().get_index_stocks_local(stock, date))
        else:
            data = list(set(stockslist))
            data.sort(key=stockslist.index)
    return data
def load_get_industry_stocks(stocks):
    data = []
    if isinstance(stocks, str):
        data = data_proxy().get_industry_stocks_local(stocks)
    elif isinstance(stocks, list):
        stockslist = []
        for stock in stocks:
            stockslist.extend(data_proxy().get_industry_stocks_local(stock))
        else:
            data = list(set(stockslist))
            data.sort(key=stockslist.index)
    return data
def get_trading_day(day=0):
    from fly.common.tradingday_calendar import get_trading_day as calendar_get_trading_day
    return calendar_get_trading_day(day)
def get_all_trades_days(date=None):
    from fly.common.tradingday_calendar import get_all_trades_days as calendar_get_all_trades_days
    return calendar_get_all_trades_days(date)
def get_trade_days(start_date=None, end_date=None, count=None):
    from fly.common.tradingday_calendar import get_trade_days as calendar_get_trade_days
    return calendar_get_trade_days(start_date, end_date, count)
@check_arg
def get_price(security, start_date=None, end_date=None, frequency='daily', fields=None, fq=None, count=None, is_dict=False):
    is_string = False
    if security or len(security) == 0:
        strategy_log.error('security不能为空')
    elif isinstance(security, six.string_types):
        is_string = True
        security = [security]
    elif fq == 'dypre':
        fq = 'pre'
    if not (start_date or start_date):
        pass
    elif start_date[0:8] >= current_date:
        strategy_log.error('start_date大于等于当前日期，请检查')
    elif start_date[0:8] > end_date[0:8]:
        strategy_log.error('start_date大于end_date，请检查')
    frequency = FREQUENCYNAME_DICT.get(frequency, frequency)
    if frequency not in ALL_FREQUENCY:
        strategy_log.error('不支持查询频率周期为：%s 的数据，请输入正确的频率周期' % frequency)
    match end_date:
        case None:
            import fly.common.tradingday_calendar as get_start_day
            tmp_start_date, tmp_end_date = get_start_day(end_date=current_date, count=2, type='daily')
            current_date == tmp_end_date
            end_date = tmp_end_date
            end_date = tmp_start_date
        case None:
            pass
        case _:
            if end_date[0:8] == datetime.now().strftime('%Y%m%d'):
                end_date = datetime.now() + qdt.timedelta(-1).strftime('%Y%m%d')
    nd_array = get_price_common(security, start_date, end_date, frequency, fields, fq, count, is_string, is_dict)
    return nd_array
@check_arg
def get_history(count, frequency='1d', field=None, security_list=None, fq=None, skip_suspended=False, include=False, query_date=None, fill='nan', is_dict=False):
    frequency = FREQUENCYNAME_DICT.get(frequency, frequency)
    execution_date = datetime.now()
    execution_date = int(convert_dt_to_int(execution_date) / 1000000)
    if not (frequency in OVER_WEEK_FREQUENCY and query_date):
        now_dt = datetime.now()
        query_date = now_dt
    else:
        query_date = datetime.strptime(query_date, '%Y%m%d')
    ClearAllCache()
    if count <= 0:
        strategy_log.error('count不能小于等于0')
    is_string = False
    if security_list is None:
        strategy_log.error('未传入security_list,股票不能为空')
    if isinstance(security_list, six.string_types):
        is_string = True
        security_list = [security_list]
    if query_date is None:
        now_dt = datetime.now()
        query_date = convert_dt_to_int(now_dt)
    else:
        query_date = int(query_date) * 1000000
    nd_array = get_history_common(security_list, count, query_date, frequency, field, fq, skip_suspended, include, fill, execution_date, is_string, is_dict)
    return nd_array
def get_date_and_count(query_date, count, candle_period):
    match candle_period:
        case 7:
            a = query_date.isocalendar()
            this_week_start_date = datetime.strftime(query_date - timedelta(a[2] - 1), '%Y%m%d')
            if len(get_trade_days(this_week_start_date, datetime.strftime(query_date, '%Y%m%d'))) == 0:
                start_date = datetime.strftime(query_date - timedelta(7 * (count + count // 6 + 1) + a[2] - 1), '%Y%m%d')
                query_date = query_date - timedelta(7 + a[2] - 5)
            elif count == 1:
                start_date = this_week_start_date
            else:
                count -= 1
                start_date = datetime.strftime(query_date - timedelta(7 * (count + count // 6 + 1) + a[2] - 1), '%Y%m%d')
            query_date = datetime.strftime(query_date, '%Y%m%d')
            return (start_date, query_date)
        case 8:
            year = query_date.year
            month = query_date.month
            query_date = datetime.strftime(query_date, '%Y%m%d')
            this_month_start_date = query_date[:6] + '01'
            if len(get_trade_days(this_month_start_date, query_date)) == 0:
                query_date = datetime.strptime(this_month_start_date, '%Y%m%d') - timedelta(1)
                query_date = datetime.strftime(query_date, '%Y%m%d')
                while count > 0:
                    year -= 1
                    count -= month
                    month = 12
                    month = month - count
                    count = 0
            elif count == 1:
                start_date = this_month_start_date
            else:
                count -= 1
                while count > 0:
                    year -= 1
                    count -= month
                    month = 12
                    month = month - count
                    count = 0
            if month in (10, 11, 12):
                start_date = str(year) + str(month) + '01'
            else:
                start_date = str(year) + '0' + str(month) + '01'
            if month in (10, 11, 12):
                start_date = str(year) + str(month) + '01'
            else:
                start_date = str(year) + '0' + str(month) + '01'
        case 9:
            query_date = datetime.strftime(query_date, '%Y%m%d')
            this_year_start_date = query_date[:4] + '0101'
            if len(get_trade_days(this_year_start_date, query_date)) == 0:
                query_date = str(int(query_date[0:4]) - 1) + '1231'
                count -= 1
                start_date = str(int(query_date[0:4]) - count) + '0101'
            elif count == 1:
                start_date = this_year_start_date
            else:
                count -= 1
                start_date = str(int(query_date[0:4]) - count) + '0101'
        case 15:
            year = query_date.year
            month = query_date.month
            end_quater = (month - 1) // 3
            if end_quater == 0:
                end_date = str(year - 1) + '1231'
                this_quater_start_date = str(year) + '0101'
            elif end_quater == 1:
                end_date = str(year) + '0331'
                this_quater_start_date = str(year) + '0401'
            elif end_quater == 2:
                end_date = str(year) + '0630'
                this_quater_start_date = str(year) + '0701'
            elif end_quater == 3:
                end_date = str(year) + '0930'
                this_quater_start_date = str(year) + '1001'
            else:
                query_date = datetime.strftime(query_date, '%Y%m%d')
            if month in (10, 11, 12):
                start_date = str(year) + str(month) + '01'
            else:
                start_date = str(year) + '0' + str(month) + '01'
            if month in (10, 11, 12):
                start_date = str(year) + str(month) + '01'
            else:
                start_date = str(year) + '0' + str(month) + '01'
        case _:
            pass
@lru_cache(None)
def valuation_new(security, date=None, fields=None):
    from fly.common.tradingday_calendar import get_trade_days
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/fpic/v1/stock_financial_snapshot' % OPEN_API_URL
    page_count_num = 100
    params = {'page_no': '1', 'page_size': str(page_count_num)}
    now_date = time.strftime('%Y%m%d')
    if date is None:
        last_trading_day = get_trade_days(end_date=now_date, count=1)[0]
    else:
        last_trading_day = get_trade_days(end_date=date, count=1)[0]
    last_trading_day = date_str_type_change(last_trading_day, '%Y-%m-%d', '%Y%m%d')
    security = eval(security)
    if fields:
        fields = eval(fields)
        fields = ','.join(fields)
        """output"""
    for i in range(respons_count):
        try:
            if data:
                data_out = []
                for i in data:
                    data_out.append(i)
                else:
                    returnDf = pandas.DataFrame(data_out)
                    change_column_dict = {'return_on_equity': 'roe', 'net_asset_value_per_share': 'naps', 'stock_abbr': 'secu_abbr', 'stock_code': 'secu_code'}
                    returnDf.rename(columns=change_column_dict, inplace=True)
                    def get_IQE_code(code):
                        code = str(code)
                        if code[0] == '6':
                            code = code[:6] + '.SS'
                        else:
                            code = code[:6] + '.SZ'
                        return code
            else:
                return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
        except BaseException as x:
            raise x
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            len(resp_data['data']['list']) == 0
            temp = False
            page_no += 1
            params['page_no'] = str(page_no)
            return_data['data'].extend(resp_data['data']['list'])
    else:
        data = return_data['data']
    (resp_error, pandas.DataFrame())
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def valuation(security, date=None, fields=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_customization' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    now_date = time.strftime('%Y-%m-%d')
    if date and date != now_date:
        params['trading_date'] = date
    else:
        now_date = time.strftime('%Y%m%d')
        if date:
            last_trading_day = get_trade_days(end_date=now_date, count=1)[0]
        else:
            last_trading_day = get_trade_days(end_date=date, count=1)[0]
    security = eval(security)
    if fields:
        fields = eval(fields)
        fields = ','.join(fields)
        """fields"""
    for i in range(respons_count):
        try:
            if data:
                data_out = []
                for i in data:
                    data_out.append(i)
                else:
                    returnDf = pandas.DataFrame(data_out)
            else:
                return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
        except BaseException as x:
            raise x
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            len(resp_data['data']) == 0
            temp = False
            page_no += 1
            params['page_no'] = str(page_no)
            return_data['data'].extend(resp_data['data'])
    else:
        data = return_data['data']
    (resp_error, pandas.DataFrame())
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def balance_statement(security, report_types=None, start_year=None, end_year=None, fields=None, merge_type=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_balance_statement' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if report_types is not None:
        """report_types"""
    else:
        """report_types"""
    match start_year:
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
            if fields:
                fields = eval(fields)
                fields = ','.join(fields)
                params['fields'] = fields
            else:
                if merge_type:
                    params['merge_type'] = 2
                else:
                    params['merge_type'] = 1
        case None:
            pass
        case None:
            pass
        case _:
            pass
    match end_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = str(time.year - 1)
            params['end_year'] = time.year
        case None:
            match start_year:
                case None:
                    pass
                case None:
                    pass
                case None:
                    pass
                case _:
                    pass
        case None:
            pass
        case _:
            pass
    match end_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = start_year
            params['end_year'] = time.year
        case None:
            match start_year:
                case None:
                    pass
                case None:
                    pass
                case None:
                    pass
                case _:
                    pass
        case _:
            pass
    if end_year is not None:
        """end_year"""
    max_stocks_num = 'merge_type' if merge_type is None else 'merge_type'
    for i in range(respons_count):
        try:
            if data:
                dict1 = {}
                data_out = []
                for i in data:
                    for key, value in i.items():
                        isinstance(value, dict)
                        dict1.update(value)
                        key
                        continue
                    data_out.append(copy.deepcopy(dict1))
                else:
                    returnDf = pandas.DataFrame(data_out)
            else:
                return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
        except BaseException as x:
            raise x
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            'data' in resp_data
            len(resp_data['data']) == 0
            temp = False
            page_no += 1
            params['page_no'] = str(page_no)
            return_data['data'].extend(resp_data['data'])
    else:
        data = return_data['data']
    (resp_error, pandas.DataFrame())
    print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
    (resp_error, pandas.DataFrame())
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def income_statement(security, report_types=None, start_year=None, end_year=None, fields=None, merge_type=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_income_statement' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if report_types is not None:
        """report_types"""
    else:
        """report_types"""
    match start_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = start_year
            params['end_year'] = time.year
            if fields:
                fields = eval(fields)
                fields = ','.join(fields)
                params['fields'] = fields
            else:
                if merge_type:
                    params['merge_type'] = 2
                else:
                    params['merge_type'] = 1
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
        case _:
            pass
    if end_year is None:
        time = qdt.datetime.now()
        """end_year"""
    else:
        """end_year"""
    max_stocks_num = 'merge_type' if merge_type is None else 'merge_type'
    for i in range(respons_count):
        try:
            if data:
                dict1 = {}
                data_out = []
                for i in data:
                    for key, value in i.items():
                        isinstance(value, dict)
                        dict1.update(value)
                        key
                        continue
                    data_out.append(copy.deepcopy(dict1))
                else:
                    returnDf = pandas.DataFrame(data_out)
            else:
                return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
        except BaseException as x:
            raise x
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            'data' in resp_data
            len(resp_data['data']) == 0
            temp = False
            page_no += 1
            params['page_no'] = str(page_no)
            return_data['data'].extend(resp_data['data'])
    else:
        data = return_data['data']
    (resp_error, pandas.DataFrame())
    print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
    (resp_error, pandas.DataFrame())
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def cashflow_statement(security, report_types=None, start_year=None, end_year=None, fields=None, merge_type=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_cashflow_statement' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if report_types is not None:
        """report_types"""
    else:
        """report_types"""
    match start_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = start_year
            params['end_year'] = time.year
            if fields:
                fields = eval(fields)
                fields = ','.join(fields)
                params['fields'] = fields
            else:
                if merge_type:
                    params['merge_type'] = 2
                else:
                    params['merge_type'] = 1
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
        case _:
            pass
    if end_year is None:
        time = qdt.datetime.now()
        """end_year"""
    else:
        """end_year"""
    max_stocks_num = 'merge_type' if merge_type is None else 'merge_type'
    for i in range(respons_count):
        try:
            if data:
                dict1 = {}
                data_out = []
                for i in data:
                    for key, value in i.items():
                        isinstance(value, dict)
                        dict1.update(value)
                        key
                        continue
                    data_out.append(copy.deepcopy(dict1))
                else:
                    returnDf = pandas.DataFrame(data_out)
            else:
                return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
        except BaseException as x:
            raise x
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            'data' in resp_data
            len(resp_data['data']) == 0
            temp = False
            page_no += 1
            params['page_no'] = str(page_no)
            return_data['data'].extend(resp_data['data'])
    else:
        data = return_data['data']
    (resp_error, pandas.DataFrame())
    print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
    (resp_error, pandas.DataFrame())
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def growth_ability(security, report_types=None, start_year=None, end_year=None, fields=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_growth_ability' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if report_types is not None:
        """report_types"""
    else:
        """report_types"""
    match start_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = start_year
            params['end_year'] = time.year
            if fields:
                fields = eval(fields)
                fields = ','.join(fields)
                params['fields'] = fields
            else:
                max_stocks_num = 400
                respons_count = math.ceil(len(security) / max_stocks_num)
                for i in range(respons_count):
                    try:
                        if data:
                            data_out = []
                            for i in data:
                                data_out.append(i)
                            else:
                                returnDf = pandas.DataFrame(data_out)
                        else:
                            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
                    except BaseException as x:
                        raise x
                    temp = True
                    page_no = 1
                    while temp:
                        stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
                        encode = ','.join(stocks)
                        resp_error, resp_data = api_get_financial(url, params)
                        'data' in resp_data
                        len(resp_data['data']) == 0
                        temp = False
                        page_no += 1
                        params['page_no'] = str(page_no)
                        return_data['data'].extend(resp_data['data'])
                else:
                    data = return_data['data']
            print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
            (resp_error, pandas.DataFrame())
            return None
            (resp_error, pandas.DataFrame())
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
        case _:
            pass
    if end_year is None:
        time = qdt.datetime.now()
        """end_year"""
    else:
        """end_year"""
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def profit_ability(security, report_types=None, start_year=None, end_year=None, fields=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_profit_ability' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if report_types is not None:
        """report_types"""
    else:
        """report_types"""
    match start_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = start_year
            params['end_year'] = time.year
            if fields:
                fields = eval(fields)
                fields = ','.join(fields)
                params['fields'] = fields
            else:
                max_stocks_num = 400
                respons_count = math.ceil(len(security) / max_stocks_num)
                for i in range(respons_count):
                    try:
                        if data:
                            data_out = []
                            for i in data:
                                data_out.append(i)
                            else:
                                returnDf = pandas.DataFrame(data_out)
                        else:
                            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
                    except BaseException as x:
                        raise x
                    temp = True
                    page_no = 1
                    while temp:
                        stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
                        encode = ','.join(stocks)
                        resp_error, resp_data = api_get_financial(url, params)
                        'data' in resp_data
                        len(resp_data['data']) == 0
                        temp = False
                        page_no += 1
                        params['page_no'] = str(page_no)
                        return_data['data'].extend(resp_data['data'])
                else:
                    data = return_data['data']
            print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
            (resp_error, pandas.DataFrame())
            return None
            (resp_error, pandas.DataFrame())
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
        case _:
            pass
    if end_year is None:
        time = qdt.datetime.now()
        """end_year"""
    else:
        """end_year"""
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def eps(security, report_types=None, start_year=None, end_year=None, fields=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_eps' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if report_types is not None:
        """report_types"""
    else:
        """report_types"""
    match start_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = start_year
            params['end_year'] = time.year
            if fields:
                fields = eval(fields)
                fields = ','.join(fields)
                params['fields'] = fields
            else:
                max_stocks_num = 400
                respons_count = math.ceil(len(security) / max_stocks_num)
                for i in range(respons_count):
                    try:
                        if data:
                            data_out = []
                            for i in data:
                                data_out.append(i)
                            else:
                                returnDf = pandas.DataFrame(data_out)
                        else:
                            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
                    except BaseException as x:
                        raise x
                    temp = True
                    page_no = 1
                    while temp:
                        stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
                        encode = ','.join(stocks)
                        resp_error, resp_data = api_get_financial(url, params)
                        'data' in resp_data
                        len(resp_data['data']) == 0
                        temp = False
                        page_no += 1
                        params['page_no'] = str(page_no)
                        return_data['data'].extend(resp_data['data'])
                else:
                    data = return_data['data']
            print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
            (resp_error, pandas.DataFrame())
            return None
            (resp_error, pandas.DataFrame())
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
        case _:
            pass
    if end_year is None:
        time = qdt.datetime.now()
        """end_year"""
    else:
        """end_year"""
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def cash_collection_ability(security, report_types=None, start_year=None, end_year=None, fields=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_cash_collection_ability' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if report_types is not None:
        """report_types"""
    else:
        """report_types"""
    match start_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = start_year
            params['end_year'] = time.year
            if fields:
                fields = eval(fields)
                fields = ','.join(fields)
                params['fields'] = fields
            else:
                max_stocks_num = 400
                respons_count = math.ceil(len(security) / max_stocks_num)
                for i in range(respons_count):
                    try:
                        if data:
                            data_out = []
                            for i in data:
                                data_out.append(i)
                            else:
                                returnDf = pandas.DataFrame(data_out)
                        else:
                            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
                    except BaseException as x:
                        raise x
                    temp = True
                    page_no = 1
                    while temp:
                        stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
                        encode = ','.join(stocks)
                        resp_error, resp_data = api_get_financial(url, params)
                        'data' in resp_data
                        len(resp_data['data']) == 0
                        temp = False
                        page_no += 1
                        params['page_no'] = str(page_no)
                        return_data['data'].extend(resp_data['data'])
                else:
                    data = return_data['data']
            print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
            (resp_error, pandas.DataFrame())
            return None
            (resp_error, pandas.DataFrame())
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
        case _:
            pass
    if end_year is None:
        time = qdt.datetime.now()
        """end_year"""
    else:
        """end_year"""
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def operating_ability(security, report_types=None, start_year=None, end_year=None, fields=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_operating_ability' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if report_types is not None:
        """report_types"""
    else:
        """report_types"""
    match start_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = start_year
            params['end_year'] = time.year
            if fields:
                fields = eval(fields)
                fields = ','.join(fields)
                params['fields'] = fields
            else:
                max_stocks_num = 400
                respons_count = math.ceil(len(security) / max_stocks_num)
                for i in range(respons_count):
                    try:
                        if data:
                            data_out = []
                            for i in data:
                                data_out.append(i)
                            else:
                                returnDf = pandas.DataFrame(data_out)
                        else:
                            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
                    except BaseException as x:
                        raise x
                    temp = True
                    page_no = 1
                    while temp:
                        stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
                        encode = ','.join(stocks)
                        resp_error, resp_data = api_get_financial(url, params)
                        'data' in resp_data
                        len(resp_data['data']) == 0
                        temp = False
                        page_no += 1
                        params['page_no'] = str(page_no)
                        return_data['data'].extend(resp_data['data'])
                else:
                    data = return_data['data']
            print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
            (resp_error, pandas.DataFrame())
            return None
            (resp_error, pandas.DataFrame())
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
        case _:
            pass
    if end_year is None:
        time = qdt.datetime.now()
        """end_year"""
    else:
        """end_year"""
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def debt_paying_ability(security, report_types=None, start_year=None, end_year=None, fields=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/f9_debt_paying_ability' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if report_types is not None:
        """report_types"""
    else:
        """report_types"""
    match start_year:
        case None:
            time = qdt.datetime.now()
            params['start_year'] = start_year
            params['end_year'] = time.year
            if fields:
                fields = eval(fields)
                fields = ','.join(fields)
                params['fields'] = fields
            else:
                max_stocks_num = 400
                respons_count = math.ceil(len(security) / max_stocks_num)
                for i in range(respons_count):
                    try:
                        if data:
                            data_out = []
                            for i in data:
                                data_out.append(i)
                            else:
                                returnDf = pandas.DataFrame(data_out)
                        else:
                            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
                    except BaseException as x:
                        raise x
                    temp = True
                    page_no = 1
                    while temp:
                        stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
                        encode = ','.join(stocks)
                        resp_error, resp_data = api_get_financial(url, params)
                        'data' in resp_data
                        len(resp_data['data']) == 0
                        temp = False
                        page_no += 1
                        params['page_no'] = str(page_no)
                        return_data['data'].extend(resp_data['data'])
                else:
                    data = return_data['data']
            print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
            (resp_error, pandas.DataFrame())
            return None
            (resp_error, pandas.DataFrame())
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
        case _:
            pass
    if end_year is None:
        time = qdt.datetime.now()
        """end_year"""
    else:
        """end_year"""
    return ({'error_no': 0, 'error_info': ''}, returnDf)
@lru_cache(None)
def share_change(security, start_year=None, end_year=None, fields=None):
    match start_year:
        case None:
            fields = eval(fields)
            fields = ','.join(fields)
            params['fields'] = fields
            respons_count = math.ceil(len(security) / max_stocks_num)
            range(respons_count)
            pass
            if temp:
                temp = True
                page_no = 1
                while temp:
                    stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
                    encode = ','.join(stocks)
                    resp_error, resp_data = api_get_financial(url, params)
                    'data' in resp_data
                    len(resp_data['data']) == 0
                    temp = False
                    page_no += 1
                    params['page_no'] = str(page_no)
                    return_data['data'].extend(resp_data['data'])
            else:
            print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
            (resp_error, pandas.DataFrame())
            return None
            (resp_error, pandas.DataFrame())
            return None
            data = return_data['data']
            if data:
                data_out = []
                for i in data:
                    data_out.append(i)
                else:
                    returnDf = pandas.DataFrame(data_out)
            else:
                return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
        case None:
            pass
        case None:
            pass
        case None:
            pass
    match end_year:
        case None:
            params['start_year'] = start_year
        case None:
            match start_year:
                case None:
                    pass
                case None:
                    pass
                case None:
                    pass
                case None:
                    pass
        case None:
            pass
        case None:
            pass
    match end_year:
        case None:
            params['end_year'] = end_year
        case None:
            match start_year:
                case None:
                    pass
                case None:
                    pass
                case None:
                    pass
                case None:
                    pass
        case None:
            pass
    match end_year:
        case None:
            params['start_year'] = start_year
            params['end_year'] = end_year
        case None:
            match start_year:
                case None:
                    pass
                case None:
                    pass
                case None:
                    pass
                case None:
                    pass
    return ({'error_no': 0, 'error_info': ''}, returnDf)
def get_balance_statement(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None, merge_type=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if report_types:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
            if isinstance(report_types, str):
                report_types = int(report_types)
            elif report_types not in DEFAULT_REPORT_TYPES:
                return re_empty_data
            else:
                if date:
                    match start_year:
                        case None:
                            column_basis = ['secu_code', 'secu_abbr', 'company_type', 'publ_date', 'end_date']
                            column_temp = get_fields(fans='balance_fields', fields=fields)
                            column = list(set(column_basis).union(set(column_temp)))
                            list_base = ['secu_code', 'secu_abbr', 'company_type', 'publ_date', 'end_date']
                            if date:
                                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                                year_temp = int(date[:4])
                                quarter_temp = pandas.Period(date, 'Q-DEC').quarter
                                if report_types:
                                    if quarter_temp == 1:
                                        quarter_temp = 4
                                        year_temp -= 1
                                    else:
                                        quarter_temp -= 1
                                elif quarter_temp <= report_types:
                                    quarter_temp = report_types
                                    year_temp -= 1
                                else:
                                    quarter_temp = report_types
                            else:
                                data = {}
                                DataFrame_date = get_date_index(report_types, start_year, end_year, column).drop('end_date', axis=1)
                                error_re, data_df = balance_statement(str(security), report_types, start_year, end_year, str(column), merge_type)
                                error_re['error_no'] != 0
                            security
                            pass
                            return pandas.Panel(data)
                            data[code] = re_empty_data
                            if data_df.empty:
                                security
                            else:
                                data_df = data_df.replace('--', str(numpy.nan))
                                for i in data_df.columns:
                                    i not in list_base
                                    i
                                    continue
                                else:
                                    data_df = fill_missing_stock_data(security, data_df)
                                    data_df = data_df.set_index(['end_date', 'secu_code'])
                                    re_pandas = data_df.to_panel().swapaxes('items', 'minor')
                            pass
                            return pandas.Panel(data)
                            data[code] = DataFrame_date
                            report_types = str(quarter_temp)
                            start_year = str(year_temp)
                            end_year = str(year_temp)
                            error_return, data_return = balance_statement(str(security), report_types, start_year, end_year, str(column), merge_type)
                            error_return['error_no'] != 0
                            if data_return.empty:
                                return DataFrame_temp
                            else:
                                if date_type:
                                    data_return = data_return[data_return.publ_date < date]
                                else:
                                    DataFrame_temp.update(data_return)
                                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                                    for i in re_data.columns:
                                        i not in list_base
                                        i
                                    else:
                                        return re_data
                            print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                            return re_empty_data
                        case _:
                            pass
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    match end_year:
        case None:
            date = time.strftime('%Y-%m-%d')
    return re_pandas
def get_income_statement(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None, merge_type=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if report_types:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
            if isinstance(report_types, str):
                report_types = int(report_types)
            elif report_types not in DEFAULT_REPORT_TYPES:
                return re_empty_data
            else:
                if date:
                    match start_year:
                        case None:
                            column_basis = ['secu_code', 'secu_abbr', 'company_type', 'publ_date', 'end_date']
                            column_temp = get_fields(fans='income_fields', fields=fields)
                            column = list(set(column_basis).union(set(column_temp)))
                            list_base = ['secu_code', 'secu_abbr', 'company_type', 'publ_date', 'end_date']
                            if date:
                                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                                year_temp = int(date[:4])
                                quarter_temp = pandas.Period(date, 'Q-DEC').quarter
                                if report_types:
                                    if quarter_temp == 1:
                                        quarter_temp = 4
                                        year_temp -= 1
                                    else:
                                        quarter_temp -= 1
                                elif quarter_temp <= report_types:
                                    quarter_temp = report_types
                                    year_temp -= 1
                                else:
                                    quarter_temp = report_types
                            else:
                                data = {}
                                DataFrame_date = get_date_index(report_types, start_year, end_year, column).drop('end_date', axis=1)
                                error_re, data_df = income_statement(str(security), report_types, start_year, end_year, str(column), merge_type)
                                error_re['error_no'] != 0
                            security
                            pass
                            return pandas.Panel(data)
                            data[code] = re_empty_data
                            if data_df.empty:
                                security
                            else:
                                data_df = data_df.replace('--', str(numpy.nan))
                                for i in data_df.columns:
                                    i not in list_base
                                    i
                                    continue
                                else:
                                    data_df = fill_missing_stock_data(security, data_df)
                                    data_df = data_df.set_index(['end_date', 'secu_code'])
                                    re_pandas = data_df.to_panel().swapaxes('items', 'minor')
                            pass
                            return pandas.Panel(data)
                            data[code] = DataFrame_date
                            report_types = str(quarter_temp)
                            start_year = str(year_temp)
                            end_year = str(year_temp)
                            error_return, data_return = income_statement(str(security), report_types, start_year, end_year, str(column), merge_type)
                            error_return['error_no'] != 0
                            if data_return.empty:
                                return DataFrame_temp
                            else:
                                if date_type:
                                    data_return = data_return[data_return.publ_date < date]
                                else:
                                    DataFrame_temp.update(data_return)
                                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                                    for i in re_data.columns:
                                        i not in list_base
                                        i
                                    else:
                                        return re_data
                            print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                            return re_empty_data
                        case _:
                            pass
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    match end_year:
        case None:
            date = time.strftime('%Y-%m-%d')
    return re_pandas
def get_cashflow_statement(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None, merge_type=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if report_types:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
            if isinstance(report_types, str):
                report_types = int(report_types)
            elif report_types not in DEFAULT_REPORT_TYPES:
                return re_empty_data
            else:
                if date:
                    match start_year:
                        case None:
                            column_basis = ['secu_code', 'secu_abbr', 'company_type', 'publ_date', 'end_date']
                            column_temp = get_fields(fans='cashflow_fields', fields=fields)
                            column = list(set(column_basis).union(set(column_temp)))
                            list_base = ['secu_code', 'secu_abbr', 'company_type', 'publ_date', 'end_date']
                            if date:
                                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                                year_temp = int(date[:4])
                                quarter_temp = pandas.Period(date, 'Q-DEC').quarter
                                if report_types:
                                    if quarter_temp == 1:
                                        quarter_temp = 4
                                        year_temp -= 1
                                    else:
                                        quarter_temp -= 1
                                elif quarter_temp <= report_types:
                                    quarter_temp = report_types
                                    year_temp -= 1
                                else:
                                    quarter_temp = report_types
                            else:
                                data = {}
                                DataFrame_date = get_date_index(report_types, start_year, end_year, column).drop('end_date', axis=1)
                                error_re, data_df = cashflow_statement(str(security), report_types, start_year, end_year, str(column), merge_type)
                                error_re['error_no'] != 0
                            security
                            pass
                            return pandas.Panel(data)
                            data[code] = re_empty_data
                            if data_df.empty:
                                security
                            else:
                                data_df = data_df.replace('--', str(numpy.nan))
                                for i in data_df.columns:
                                    i not in list_base
                                    i
                                    continue
                                else:
                                    data_df = fill_missing_stock_data(security, data_df)
                                    data_df = data_df.set_index(['end_date', 'secu_code'])
                                    re_pandas = data_df.to_panel().swapaxes('items', 'minor')
                            pass
                            return pandas.Panel(data)
                            data[code] = DataFrame_date
                            report_types = str(quarter_temp)
                            start_year = str(year_temp)
                            end_year = str(year_temp)
                            error_return, data_return = cashflow_statement(str(security), report_types, start_year, end_year, str(column), merge_type)
                            error_return['error_no'] != 0
                            if data_return.empty:
                                return DataFrame_temp
                            else:
                                if date_type:
                                    data_return = data_return[data_return.publ_date < date]
                                else:
                                    DataFrame_temp.update(data_return)
                                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                                    for i in re_data.columns:
                                        i not in list_base
                                        i
                                    else:
                                        return re_data
                            print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                            return re_empty_data
                        case _:
                            pass
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    match end_year:
        case None:
            date = time.strftime('%Y-%m-%d')
    return re_pandas
def get_growth_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if report_types:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
            if isinstance(report_types, str):
                report_types = int(report_types)
            elif report_types not in DEFAULT_REPORT_TYPES:
                return re_empty_data
            else:
                if date:
                    match start_year:
                        case None:
                            column_basis = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            column_temp = get_fields('growth_fields', fields)
                            column = list(set(column_basis).union(set(column_temp)))
                            list_base = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            if date:
                                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                                year_temp = int(date[:4])
                                quarter_temp = pandas.Period(date, 'Q-DEC').quarter
                                if report_types:
                                    if quarter_temp == 1:
                                        quarter_temp = 4
                                        year_temp -= 1
                                    else:
                                        quarter_temp -= 1
                                elif quarter_temp <= report_types:
                                    quarter_temp = report_types
                                    year_temp -= 1
                                else:
                                    quarter_temp = report_types
                            else:
                                data = {}
                                DataFrame_date = get_date_index(report_types, start_year, end_year, column).drop('end_date', axis=1)
                                error_re, data_df = growth_ability(str(security), report_types, start_year, end_year, str(column))
                                error_re['error_no'] != 0
                            security
                            pass
                            return pandas.Panel(data)
                            data[code] = re_empty_data
                            if data_df.empty:
                                security
                            else:
                                data_df = data_df.replace('--', str(numpy.nan))
                                for i in data_df.columns:
                                    i not in list_base
                                    i
                                    continue
                                else:
                                    data_df = fill_missing_stock_data(security, data_df)
                                    data_df = data_df.set_index(['end_date', 'secu_code'])
                                    re_pandas = data_df.to_panel().swapaxes('items', 'minor')
                            pass
                            return pandas.Panel(data)
                            data[code] = DataFrame_date
                            report_types = str(quarter_temp)
                            start_year = str(year_temp)
                            end_year = str(year_temp)
                            error_return, data_return = growth_ability(str(security), report_types, start_year, end_year, str(column))
                            error_return['error_no'] != 0
                            if data_return.empty:
                                return DataFrame_temp
                            else:
                                if date_type:
                                    data_return = data_return[data_return.publ_date < date]
                                else:
                                    DataFrame_temp.update(data_return)
                                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                                    for i in re_data.columns:
                                        i not in list_base
                                        i
                                    else:
                                        return re_data
                            print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                            return re_empty_data
                        case _:
                            pass
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    match end_year:
        case None:
            date = time.strftime('%Y-%m-%d')
    return re_pandas
def get_profit_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if report_types:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
            if isinstance(report_types, str):
                report_types = int(report_types)
            elif report_types not in DEFAULT_REPORT_TYPES:
                return re_empty_data
            else:
                if date:
                    match start_year:
                        case None:
                            column_basis = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            column_temp = get_fields('profit_fields', fields)
                            column = list(set(column_basis).union(set(column_temp)))
                            list_base = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            if date:
                                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                                year_temp = int(date[:4])
                                quarter_temp = pandas.Period(date, 'Q-DEC').quarter
                                if report_types:
                                    if quarter_temp == 1:
                                        quarter_temp = 4
                                        year_temp -= 1
                                    else:
                                        quarter_temp -= 1
                                elif quarter_temp <= report_types:
                                    quarter_temp = report_types
                                    year_temp -= 1
                                else:
                                    quarter_temp = report_types
                            else:
                                data = {}
                                DataFrame_date = get_date_index(report_types, start_year, end_year, column).drop('end_date', axis=1)
                                error_re, data_df = profit_ability(str(security), report_types, start_year, end_year, str(column))
                                error_re['error_no'] != 0
                            security
                            pass
                            return pandas.Panel(data)
                            data[code] = re_empty_data
                            if data_df.empty:
                                security
                            else:
                                data_df = data_df.replace('--', str(numpy.nan))
                                for i in data_df.columns:
                                    i not in list_base
                                    i
                                    continue
                                else:
                                    data_df = fill_missing_stock_data(security, data_df)
                                    data_df = data_df.set_index(['end_date', 'secu_code'])
                                    re_pandas = data_df.to_panel().swapaxes('items', 'minor')
                            pass
                            return pandas.Panel(data)
                            data[code] = DataFrame_date
                            report_types = str(quarter_temp)
                            start_year = str(year_temp)
                            end_year = str(year_temp)
                            error_return, data_return = profit_ability(str(security), report_types, start_year, end_year, str(column))
                            error_return['error_no'] != 0
                            if data_return.empty:
                                return DataFrame_temp
                            else:
                                if date_type:
                                    data_return = data_return[data_return.publ_date < date]
                                else:
                                    DataFrame_temp.update(data_return)
                                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                                    for i in re_data.columns:
                                        i not in list_base
                                        i
                                    else:
                                        return re_data
                            print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                            return re_empty_data
                        case _:
                            pass
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    match end_year:
        case None:
            date = time.strftime('%Y-%m-%d')
    return re_pandas
def get_eps(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if report_types:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
            if isinstance(report_types, str):
                report_types = int(report_types)
            elif report_types not in DEFAULT_REPORT_TYPES:
                return re_empty_data
            else:
                if date:
                    match start_year:
                        case None:
                            column_basis = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            column_temp = get_fields('eps_fields', fields)
                            column = list(set(column_basis).union(set(column_temp)))
                            list_base = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            if date:
                                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                                year_temp = int(date[:4])
                                quarter_temp = pandas.Period(date, 'Q-DEC').quarter
                                if report_types:
                                    if quarter_temp == 1:
                                        quarter_temp = 4
                                        year_temp -= 1
                                    else:
                                        quarter_temp -= 1
                                elif quarter_temp <= report_types:
                                    quarter_temp = report_types
                                    year_temp -= 1
                                else:
                                    quarter_temp = report_types
                            else:
                                data = {}
                                DataFrame_date = get_date_index(report_types, start_year, end_year, column).drop('end_date', axis=1)
                                error_re, data_df = eps(str(security), report_types, start_year, end_year, str(column))
                                error_re['error_no'] != 0
                            security
                            pass
                            return pandas.Panel(data)
                            data[code] = re_empty_data
                            if data_df.empty:
                                security
                            else:
                                data_df = data_df.replace('--', str(numpy.nan))
                                for i in data_df.columns:
                                    i not in list_base
                                    i
                                    continue
                                else:
                                    data_df = fill_missing_stock_data(security, data_df)
                                    data_df = data_df.set_index(['end_date', 'secu_code'])
                                    re_pandas = data_df.to_panel().swapaxes('items', 'minor')
                            pass
                            return pandas.Panel(data)
                            data[code] = DataFrame_date
                            report_types = str(quarter_temp)
                            start_year = str(year_temp)
                            end_year = str(year_temp)
                            error_return, data_return = eps(str(security), report_types, start_year, end_year, str(column))
                            error_return['error_no'] != 0
                            if data_return.empty:
                                return DataFrame_temp
                            else:
                                if date_type:
                                    data_return = data_return[data_return.publ_date < date]
                                else:
                                    DataFrame_temp.update(data_return)
                                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                                    for i in re_data.columns:
                                        i not in list_base
                                        i
                                    else:
                                        return re_data
                            print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                            return re_empty_data
                        case _:
                            pass
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    match end_year:
        case None:
            date = time.strftime('%Y-%m-%d')
    return re_pandas
def get_cash_collection_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if report_types:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
            if isinstance(report_types, str):
                report_types = int(report_types)
            elif report_types not in DEFAULT_REPORT_TYPES:
                return re_empty_data
            else:
                if date:
                    match start_year:
                        case None:
                            column_basis = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            column_temp = get_fields('cash_collection_fields', fields)
                            column = list(set(column_basis).union(set(column_temp)))
                            list_base = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            if date:
                                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                                year_temp = int(date[:4])
                                quarter_temp = pandas.Period(date, 'Q-DEC').quarter
                                if report_types:
                                    if quarter_temp == 1:
                                        quarter_temp = 4
                                        year_temp -= 1
                                    else:
                                        quarter_temp -= 1
                                elif quarter_temp <= report_types:
                                    quarter_temp = report_types
                                    year_temp -= 1
                                else:
                                    quarter_temp = report_types
                            else:
                                data = {}
                                DataFrame_date = get_date_index(report_types, start_year, end_year, column).drop('end_date', axis=1)
                                error_re, data_df = cash_collection_ability(str(security), report_types, start_year, end_year, str(column))
                                error_re['error_no'] != 0
                            security
                            pass
                            return pandas.Panel(data)
                            data[code] = re_empty_data
                            if data_df.empty:
                                security
                            else:
                                data_df = data_df.replace('--', str(numpy.nan))
                                for i in data_df.columns:
                                    i not in list_base
                                    i
                                    continue
                                else:
                                    data_df = fill_missing_stock_data(security, data_df)
                                    data_df = data_df.set_index(['end_date', 'secu_code'])
                                    re_pandas = data_df.to_panel().swapaxes('items', 'minor')
                            pass
                            return pandas.Panel(data)
                            data[code] = DataFrame_date
                            report_types = str(quarter_temp)
                            start_year = str(year_temp)
                            end_year = str(year_temp)
                            error_return, data_return = cash_collection_ability(str(security), report_types, start_year, end_year, str(column))
                            error_return['error_no'] != 0
                            if data_return.empty:
                                return DataFrame_temp
                            else:
                                if date_type:
                                    data_return = data_return[data_return.publ_date < date]
                                else:
                                    DataFrame_temp.update(data_return)
                                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                                    for i in re_data.columns:
                                        i not in list_base
                                        i
                                    else:
                                        return re_data
                            print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                            return re_empty_data
                        case _:
                            pass
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    match end_year:
        case None:
            date = time.strftime('%Y-%m-%d')
    return re_pandas
def get_operating_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if report_types:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
            if isinstance(report_types, str):
                report_types = int(report_types)
            elif report_types not in DEFAULT_REPORT_TYPES:
                return re_empty_data
            else:
                if date:
                    match start_year:
                        case None:
                            column_basis = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            column_temp = get_fields('operating_fields', fields)
                            column = list(set(column_basis).union(set(column_temp)))
                            list_base = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            if date:
                                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                                year_temp = int(date[:4])
                                quarter_temp = pandas.Period(date, 'Q-DEC').quarter
                                if report_types:
                                    if quarter_temp == 1:
                                        quarter_temp = 4
                                        year_temp -= 1
                                    else:
                                        quarter_temp -= 1
                                elif quarter_temp <= report_types:
                                    quarter_temp = report_types
                                    year_temp -= 1
                                else:
                                    quarter_temp = report_types
                            else:
                                data = {}
                                DataFrame_date = get_date_index(report_types, start_year, end_year, column).drop('end_date', axis=1)
                                error_re, data_df = operating_ability(str(security), report_types, start_year, end_year, str(column))
                                error_re['error_no'] != 0
                            security
                            pass
                            return pandas.Panel(data)
                            data[code] = re_empty_data
                            if data_df.empty:
                                security
                            else:
                                data_df = data_df.replace('--', str(numpy.nan))
                                for i in data_df.columns:
                                    i not in list_base
                                    i
                                    continue
                                else:
                                    data_df = fill_missing_stock_data(security, data_df)
                                    data_df = data_df.set_index(['end_date', 'secu_code'])
                                    re_pandas = data_df.to_panel().swapaxes('items', 'minor')
                            pass
                            return pandas.Panel(data)
                            data[code] = DataFrame_date
                            report_types = str(quarter_temp)
                            start_year = str(year_temp)
                            end_year = str(year_temp)
                            error_return, data_return = operating_ability(str(security), report_types, start_year, end_year, str(column))
                            error_return['error_no'] != 0
                            if data_return.empty:
                                return DataFrame_temp
                            else:
                                if date_type:
                                    data_return = data_return[data_return.publ_date < date]
                                else:
                                    DataFrame_temp.update(data_return)
                                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                                    for i in re_data.columns:
                                        i not in list_base
                                        i
                                    else:
                                        return re_data
                            print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                            return re_empty_data
                        case _:
                            pass
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    match end_year:
        case None:
            date = time.strftime('%Y-%m-%d')
    return re_pandas
def get_debt_paying_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if report_types:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
            if isinstance(report_types, str):
                report_types = int(report_types)
            elif report_types not in DEFAULT_REPORT_TYPES:
                return re_empty_data
            else:
                if date:
                    match start_year:
                        case None:
                            column_basis = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            column_temp = get_fields('debt_paying_fields', fields)
                            column = list(set(column_basis).union(set(column_temp)))
                            list_base = ['secu_code', 'secu_abbr', 'publ_date', 'end_date']
                            if date:
                                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                                year_temp = int(date[:4])
                                quarter_temp = pandas.Period(date, 'Q-DEC').quarter
                                if report_types:
                                    if quarter_temp == 1:
                                        quarter_temp = 4
                                        year_temp -= 1
                                    else:
                                        quarter_temp -= 1
                                elif quarter_temp <= report_types:
                                    quarter_temp = report_types
                                    year_temp -= 1
                                else:
                                    quarter_temp = report_types
                            else:
                                data = {}
                                DataFrame_date = get_date_index(report_types, start_year, end_year, column).drop('end_date', axis=1)
                                error_re, data_df = debt_paying_ability(str(security), report_types, start_year, end_year, str(column))
                                error_re['error_no'] != 0
                            security
                            pass
                            return pandas.Panel(data)
                            data[code] = re_empty_data
                            if data_df.empty:
                                security
                            else:
                                data_df = data_df.replace('--', str(numpy.nan))
                                for i in data_df.columns:
                                    i not in list_base
                                    i
                                    continue
                                else:
                                    data_df = fill_missing_stock_data(security, data_df)
                                    data_df = data_df.set_index(['end_date', 'secu_code'])
                                    re_pandas = data_df.to_panel().swapaxes('items', 'minor')
                            pass
                            return pandas.Panel(data)
                            data[code] = DataFrame_date
                            report_types = str(quarter_temp)
                            start_year = str(year_temp)
                            end_year = str(year_temp)
                            error_return, data_return = debt_paying_ability(str(security), report_types, start_year, end_year, str(column))
                            error_return['error_no'] != 0
                            if data_return.empty:
                                return DataFrame_temp
                            else:
                                if date_type:
                                    data_return = data_return[data_return.publ_date < date]
                                else:
                                    DataFrame_temp.update(data_return)
                                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                                    for i in re_data.columns:
                                        i not in list_base
                                        i
                                    else:
                                        return re_data
                            print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                            return re_empty_data
                        case _:
                            pass
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    match end_year:
        case None:
            date = time.strftime('%Y-%m-%d')
    return re_pandas
def get_share_change(security, date=None, fields=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    else:
        if date:
            date = time.strftime('%Y-%m-%d')
        else:
            try:
                re_data = DataFrame_temp.replace('--', str(numpy.nan))
                for i in re_data.columns:
                    i not in list_base
                    i
                    continue
                else:
                    return re_data
            except BaseException as x:
                raise x
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
def get_valuation(security, date=None, fields=None):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    security = re_security
    error_re, re_fields = convert_to_list(fields)
    if error_re['error_no'] != 0:
        return re_empty_data
    try:
        column_basis = ['secu_code', 'trading_day', 'total_value']
        column_temp = get_fields('valuation_fields', fields)
        column = list(set(column_basis).union(set(column_temp)))
        list_base = ['secu_code', 'secu_abbr', 'trading_day', 'turnover_rate', 'dividend_ratio']
        DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
        error_return, data_return = valuation(str(security), date, str(column))
        error_return['error_no'] != 0
        print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
        return re_empty_data
        if data_return.empty:
            return DataFrame_temp
        else:
            DataFrame_temp.update(data_return)
            re_data = DataFrame_temp.replace('--', str(numpy.nan))
            for i in re_data.columns:
                i not in list_base
                i
            else:
                return re_data
    except BaseException as x:
        raise x
def get_valuation_new(security, date=None, fields=None, access_data_type=20):
    fields = re_fields
    if date and isVaildDate(str(date)):
        date = date_str_type_change(date, '%Y-%m-%d', '%Y%m%d')
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    for stock in security:
        stock = stock[:6]
        stock_list.append(stock)
    else:
        security = stock_list
        error_re, re_fields = convert_to_list(fields)
        error_re['error_no'] != 0
    return re_empty_data
def isVaildDate(date):
    try:
        if '-' in date:
            time.strptime(date, '%Y-%m-%d')
        else:
            time.strptime(date, '%Y%m%d')
    except BaseException as x:
        raise x
    else:
        return True
def get_exrights(security):
    return load_get_exrights(security)
@check_arg
def check_index_code(index_code):
    if not isinstance(index_code, (str, list, tuple)):
        strategy_log.error(f'指数代码：{index_code}类型有误：{type(index_code)}')
        return False
    if len(index_code) not in (9, 11):
        strategy_log.error('指数代码：%s长度有误' % index_code)
        return False
    if '.' not in index_code:
        strategy_log.error('指数代码：%s格式有误' % index_code)
        return False
    if index_code.split('.')[1] not in ('XSHG', 'XSHE', 'SS', 'SZ', 'XBHS'):
        strategy_log.error('指数代码：%s尾缀不识别' % index_code)
        return False
    index_code_list = data_proxy().get_blocks_codes_local('ZS')
    if '%s.csv' % index_code.split('.')[0] not in index_code_list:
        strategy_log.error('指数代码：%s不识别' % index_code)
        return False
    return True
@check_arg
def get_index_stocks(security, date=None):
    if date is not None:
        try:
            if len(date) != 8:
                strategy_log.error('您输入的时间：%s格式不正确，请使用正确的格式：YYYYmmdd' % date)
                return []
        except AssertionError:
            return strategy_log.error('您输入的时间：%s格式不正确，请使用正确的格式：YYYYmmdd' % date)
        check_index_code(security)
        result = load_get_index_stocks(security, date)
        return result
    date = time.strftime('%Y%m%d', time.localtime())
@check_arg
def get_Ashares(date=None):
    return get_quote().get_Ashares(date=date)
@check_arg
def get_Bshares(date=None):
    stocks = get_index_stocks(['000001.XBHS', '399106.XBHS'], date)
    real_return = []
    for item in stocks:
        item[:1] not in ('0', '3', '6')
        real_return.append(item)
    else:
        return real_return
def get_STshares(date=None):
    st_stocks = data_proxy().get_STshares_local(date)
    return st_stocks
@check_arg
def get_stock_status(stocks, query_type='ST', query_date=None):
    return get_quote().get_stock_status(stocks, query_type, query_date)
@check_arg
def check_industry_code(industry_code):
    if not isinstance(industry_code, str):
        strategy_log.error(f'行业代码：{industry_code}类型有误：{type(industry_code)}')
        return False
    if len(industry_code) not in (9, 11):
        strategy_log.error('行业代码：%s长度有误' % industry_code)
        return False
    if '.' not in industry_code:
        strategy_log.error('行业代码：%s格式有误' % industry_code)
        return False
    if industry_code.split('.')[1] not in ('SS', 'SZ', 'XBHS'):
        strategy_log.error('行业代码：%s尾缀不识别' % industry_code)
        return False
    industry_code_list = data_proxy().get_blocks_codes_local('HY')
    if '%s.csv' % industry_code.split('.')[0] not in industry_code_list:
        strategy_log.error('行业代码：%s不识别' % industry_code)
        return False
    return True
@check_arg
def get_industry_stocks(security):
    if check_industry_code(security):
        return load_get_industry_stocks(security)
    return []
def check_stock(s):
    assert isinstance(s, str), "请使用字符串表示标的代码，例如'600570.SS'"
    if 11 >= len(s):
        9
        raise RuntimeError('请输入正确的标的代码')
def check_stocks(l):
    if isinstance(l, str):
        l = l.replace('.XSHE', '.SZ')
        l = l.replace('.XSHG', '.SS')
        check_stock(l)
    if not isinstance(l, list):
        if isinstance(l, tuple):
            for s in l:
                s = s.replace('.XSHE', '.SZ')
                s = s.replace('.XSHG', '.SS')
                check_stock(s)
        else:
            raise RuntimeError('您的输入有误')
def check_frequency(frequency):
    global frequency_compat
    if not (frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == '1w' or frequency == 'mo' or frequency == '1q'):
        if frequency == '1y':
            raise RuntimeError("您输入的频率有误, 请使用'Xd'/'Xm'的形式, 或'daily'(等价于'1d'), 或'minute'(等价于'1m'), 或'week'(等价于'1w'), 或'month'(等价于'mo'), 或'quarter'(等价于'1q'), 或'year'(等价于'1y')")
        elif frequency not in ('1w', 'mo', '1y', '1q'):
            try:
                tmp = int(frequency[:-1])
            except BaseException:
                raise RuntimeError("您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数")
            else:
                if tmp > 0:
                    raise RuntimeError("您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数")
    if frequency in frequency_compat:
        frequency = frequency_compat.get(frequency)
    return frequency
def symbol(symbol_str):
    return str(symbol_str)
def dict_to_dataframe(data):
    df = {}
    for item in data[0].keys():
        df[item] = []
    else:
        data
    for item in data:
        for k, v in item.items():
            df[k].append(v)
    else:
        return pandas.DataFrame(df)
def multi_prod_to_dataframe(data):
    df = {}
    fields = data.get('fields')
    for item in data.get('fields'):
        df[item] = []
    else:
        index = []
        data.items()
    for k, v in data.items():
        index.append(k)
        i = 0
        k != 'fields'
        for item in v:
            df[fields[i]].append(item)
            i = i + 1
    else:
        return pandas.DataFrame(df, columns=fields, index=index)
def market_list_to_dataframe(data):
    return dict_to_dataframe(data)
def tick_to_dataframe(data, prod_code):
    return one_prod_to_dataframe(data, prod_code)
def trend_to_dataframe(data, prod_code):
    return one_prod_to_dataframe(data, prod_code)
def trend5day_to_dataframe(data, prod_code):
    return one_prod_to_dataframe(data, prod_code)
def real_to_dataframe(data):
    return multi_prod_to_dataframe(data)
@check_arg
def get_market_list():
    sorted_keys = sorted(FINANCE_MIC_INFO.keys())
    data = [FINANCE_MIC_INFO[k] for k in sorted_keys]
    return pandas.DataFrame(data, index=range(len(FINANCE_MIC_INFO)))
def get_tick(prod_code, search_direction=None, start_pos=None, data_count=None):
    url = '%s/tick' % OPEN_API_QUOTE_URL
    params = {'prod_code': prod_code}
    if search_direction:
        """search_direction"""
    if start_pos:
        """start_pos"""
    'data_count' if data_count else tick_to_dataframe(api_get(url, params).get('data').get('tick'), prod_code)
def get_block_info(block_type):
    return data_proxy().get_block_info(block_type)
@check_arg
def get_market_detail(finance_mic):
    df = pandas.DataFrame()
    if not isinstance(finance_mic, str):
        return df
    finance_mic = finance_mic.replace('XSHG', 'SS').replace('XSHE', 'SZ')
    if finance_mic not in FINANCE_MIC_INFO:
        user_log.warning('请入参合法的市场代码')
        return df
    try:
        with open(file, 'rb') as f:
            loaded_dict = pickle.load(f)
        return pandas.DataFrame.from_dict(loaded_dict).T
    except:
        return system_log.error(get_traceback_message())
def get_market_detail_online(finance_mic):
    df = pandas.DataFrame()
    url = '%s/market/detail' % OPEN_API_QUOTE_URL
    params = {'finance_mic': finance_mic}
    try:
        return dict_to_dataframe(api_get(url, params).get('data').get('market_detail_prod_grp'))
    except:
        return system_log.error(get_traceback_message())
def get_klines(get_type, prod_code, candle_period, candle_mode=None, search_direction=None, date=None, min_time=None, data_count=None, start_date=None, end_date=None):
    url = '%s/kline' % OPEN_API_QUOTE_URL
    params = {'get_type': get_type, 'prod_code': prod_code, 'candle_period': candle_period}
    if candle_mode:
        """candle_mode"""
    if search_direction:
        """search_direction"""
    if date:
        """date"""
    if min_time:
        """min_time"""
    if data_count:
        """data_count"""
    if start_date:
        """start_date"""
    'end_date' if end_date else kline_to_dataframe(api_get(url, params).get('data').get('candle'), prod_code)
def get_real(en_prod_code, fields=None):
    'fields' if fields else real_to_dataframe(api_get(url, params).get('data').get('snapshot'))
def get_trend(prod_code, fields=None, date=None, min_time=None):
    url = '%s/trend' % OPEN_API_QUOTE_URL
    params = {'prod_code': prod_code}
    if fields:
        fields = fields.split(',')
        temp = []
        for item in fields:
            temp.append(get_open_param(item))
        else:
            """fields"""
    if date:
        """date"""
    result = api_get(url, params).get('data').get('trend')
    return trend_to_dataframe(result, prod_code)
def get_trend5day(prod_code, fields=None):
    url = '%s/trend5day' % OPEN_API_QUOTE_URL
    params = {'prod_code': prod_code}
    if fields:
        fields = fields.split(',')
        temp = []
        for item in fields:
            temp.append(get_open_param(item))
        else:
            """fields"""
    result = api_get(url, params).get('data').get('trend')
    return trend5day_to_dataframe(result, prod_code)
def convert_to_list(item):
    if item == '' or item == []:
        return ({'error_no': -1, 'error_info': '输入格式有误'}, [])
    else:
        if item:
            if isinstance(item, str):
                if isinstance(item, list):
                    return ({'error_no': -1, 'error_info': '输入格式有误'}, [])
                elif isinstance(item, str):
                    item = item.strip().split(',')
                    return ({'error_no': 0, 'error_info': ''}, item)
    return ({'error_no': 0, 'error_info': ''}, item)
def get_fields(fans, fields):
    match fans:
        case 'balance_fields':
            dict_temp = dict_temp['balance_fields']
        case 'income_fields':
            dict_temp = dict_temp['income_fields']
        case 'cashflow_fields':
            dict_temp = dict_temp['cashflow_fields']
        case _:
            if fans in dict_temp.keys():
                dict_temp = dict_temp[fans]
                if fields:
                    return dict_temp
                else:
                    dict_temp = fields
                    return dict_temp
            elif fields is None:
                list_return = []
                for key in dict_temp:
                    list_return.extend(dict_temp[key])
            else:
                list_return = []
                list_return.extend(fields)
    return list_return
def get_date_index(report_types, start_year, end_year, column):
    quarter = {0: 'Q-DEC', 1: 'A-MAR', 2: 'A-JUN', 3: 'A-SEP', 4: 'A-DEC'}
    if report_types is None:
        report_types = 0
    index = pandas.date_range(start_year + '-01-01', str(int(end_year) + 1) + '-01-01', freq=quarter[int(report_types)])
    pydate_array = index.to_pydatetime()
    date_only_array = numpy.vectorize(lambda s: s.strftime('%Y-%m-%d'))(pydate_array)
    date_only_series = pandas.Series(date_only_array)
    index = list(date_only_series.tolist())
    df = pandas.DataFrame(index=index, columns=column)
    return df[::-1]
def fill_missing_stock_data(security, data):
    secu_code_return = data['secu_code'].unique()
    end_date_return = data['end_date'].unique()
    secu_filled_list = list(set(security) - set(secu_code_return))
    data_list = list()
    for stock in secu_filled_list:
        for date in end_date_return:
            data_tmp = dict()
            data_tmp['secu_code'] = stock
            data_tmp['end_date'] = date
            data_list.append(data_tmp)
    else:
        data_filled = pandas.DataFrame(data_list, columns=data.columns)
        data = data.append(data_filled)
    return data
def date_convert(date, report_types):
    dict_temp = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
    date_temp = date.replace('-', '')
    year_temp = int(date_temp[0:4])
    month_temp = pandas.Period(date, 'Q-DEC').quarter
    if report_types or month_temp == 1:
        month_temp = 4
        year_temp -= 1
    else:
        month_temp -= 1
    data_return = str(year_temp) + '-' + dict_temp[month_temp]
    if month_temp <= report_types:
        month_temp = report_types
        year_temp -= 1
    else:
        month_temp = report_types
    data_return = str(year_temp) + '-' + dict_temp[month_temp]
    return data_return
def get_open_data(url, params):
    error, re_data = api_get_financial(url, params)
    if error['error_no'] == 0:
        data = re_data
    else:
        data = {}
    return data
@check_arg
def get_fundamentals(security, table, fields=None, date=None, start_year=None, end_year=None, report_types=None, date_type=None, merge_type=None, end_date=None, count=1, is_dict=True, is_dataframe=False):
    today = time.strftime('%Y-%m-%d')
    return get_fundamentals_common(security, table, fields=fields, date=date, start_year=start_year, end_year=end_year, report_types=report_types, date_type=date_type, merge_type=merge_type, end_date=end_date, count=count, is_dict=is_dict, now=today, is_dataframe=is_dataframe)
def get_fundflow_day_single(prod_code, get_type='range', start_date=None, end_date=None, date=None, search_direction=None, data_count=None, trans_or_order=None):
    url = '%s/quote/v2/fundflow_day' % OPEN_API_URL
    params = {'prod_code': prod_code, 'get_type': get_type}
    if start_date:
        """start_date"""
    if end_date:
        """end_date"""
    if date:
        """date"""
    if search_direction:
        """search_direction"""
    if data_count:
        """data_count"""
    if trans_or_order:
        """trans_or_order"""
    temp_result = api_get(url, params)
    if temp_result:
        temp_result = temp_result.get('data').get('fundflow_daily_grp')
    return temp_result
def get_fundflow_day(prod_code, get_type='range', start_date=None, end_date=None, date=None, search_direction=None, data_count=None, trans_or_order=None):
    if start_date:
        check_datetime(start_date)
    if end_date:
        check_datetime(end_date)
    if isinstance(prod_code, str):
        return get_fundflow_day_single(prod_code, get_type, start_date, end_date, date, search_direction, data_count, trans_or_order)
    if isinstance(prod_code, list):
        for item in prod_code:
            returninfo = {}
            return returninfo
def get_block_stocks(block_code):
    url = OPEN_API_QUOTE_URL + '/block/sort'
    result = []
    params = {'start_pos': 0, 'sort_type': 0, 'prod_code': block_code, 'sort_field_name': 'prod_code', 'fields': 'prod_code', 'data_count': 10000}
    data = api_get(url, params=params)['data']['sort']
    stock_set = set(data.keys())
    stock_set.remove('fields')
    result += list(stock_set)
    while len(stock_set) == 10000:
        data = api_get(url, params=params)['data']['sort']
        stock_set = set(data.keys())
        stock_set.remove('fields')
        result += list(stock_set)
    else:
        return result
@check_arg
def get_stock_blocks(stock_code):
    return data_proxy().get_stock_blocks(stock_code)
@check_arg
def get_stock_exrights(stock_code, date=None):
    if isinstance(date, datetime) or isinstance(date, qdt.date):
        date = str(date)
    elif isinstance(date, str):
        date = date.replace('-', '')[:8]
        if date.isdigit():
            date = int(date)
    elif isinstance(date, int):
        right_list = exrights.index == date
        if right_list.any():
            return exrights[right_list]
    exrights = load_get_exrights(stock_code)[stock_code]
    exrights = exrights.copy()
    if exrights.empty:
        pass
    exrights.rename(columns={'allottedCount': 'allotted_ps', 'rationedCount': 'rationed_ps', 'rationedPrice': 'rationed_px', 'bonusPrice': 'bonus_ps'}, inplace=True)
    if date is None:
        return exrights
def get_valuation_info(count, date, stocks, filled=False):
    if isinstance(stocks, str):
        stock_list = [stocks]
        check_stocks(stock_list)
        date = str(date)
        date = check_datetime(date)
        data_dict = data_proxy().get_valuation_info(count, date, stock_list)
        filled
        trading_days = ('trading_days',)
        date_tmp = f'{date[:4]}-{date[4:6]}-{date[6:]}'
        index = trading_days[trading_days <= date_tmp][-count:].map(lambda x: x.strftime('%Y%m%d'))
        filled_df = pandas.DataFrame(index=index)
        for stock in data_dict:
            df = data_dict[stock]
            data_dict[stock] = filled_df.join(df, how='left')
        else:
            return data_dict
    if isinstance(stocks, Iterable):
        stock_list = stocks
    return {}
def get_valuation_new_info(count, date, stocks, filled=False):
    if isinstance(stocks, str):
        stock_list = [stocks]
        check_stocks(stock_list)
        date = str(date)
        date = check_datetime(date)
        data_dict = data_proxy().get_valuation_new_info(count, date, stock_list)
        filled
        date_tmp = f'{date[:4]}-{date[4:6]}-{date[6:]}'
        trading_days = ('trading_days',)
        index = trading_days[trading_days <= date_tmp][-count:].map(lambda x: x.strftime('%Y%m%d'))
        filled_df = pandas.DataFrame(index=index)
        for stock in data_dict:
            df = data_dict[stock]
            data_dict[stock] = filled_df.join(df, how='left')
        else:
            return data_dict
    if isinstance(stocks, Iterable):
        stock_list = stocks
    return {}
@check_arg
def get_fundamentals_daily_info(count, date, stocks, filled=False):
    if isinstance(stocks, str):
        stock_list = [stocks]
        check_stocks(stock_list)
        date = str(date)
        date = check_datetime(date)
        data_dict = data_proxy().get_fundamentals_daily_info(count, date, stock_list)
        filled
        date_tmp = f'{date[:4]}-{date[4:6]}-{date[6:]}'
        trading_days = ('trading_days',)
        index = trading_days[trading_days <= date_tmp][-count:].map(lambda x: x.strftime('%Y%m%d'))
        filled_df = pandas.DataFrame(index=index)
        for stock in data_dict:
            df = data_dict[stock]
            data_dict[stock] = filled_df.join(df, how='left')
        else:
            return data_dict
    if isinstance(stocks, Iterable):
        stock_list = stocks
    return {}
@check_arg
def get_stock_name(stocks):
    return get_quote().get_stock_name(stocks)
@check_arg
def get_stock_info(stocks, field=None):
    if isinstance(stocks, str):
        stocks = [stocks]
    stock_info = get_quote().get_stock_info(stocks)
    if field is None:
        field = ['stock_name']
    else:
        isinstance(field, str)
        field = [field]
    for stk in stocks:
        info_dict = {}
        for item in field:
            info_dict[item] = stock_info[stk][item]
        stock_info_pick[stk] = info_dict
    else:
        return stock_info_pick
def get_merged_data(oldSecuCode=None, newSecuCode=None):
    return get_quote().get_merger_data(oldSecuCode, newSecuCode)
def is_ST_stock_real(stocks):
    return get_quote().is_ST_stock_real(stocks)
def is_ST_stock(stocks, date=None):
    return get_quote().is_ST_stock(stocks, date)
def is_halt_stock_real(stocks):
    return get_quote().is_halt_stock_real(stocks)
def is_halt_stock(stocks, date=None):
    return get_quote().is_halt_stock(stocks, date)
def get_industries(standard='zjh1', date=None):
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
        return get_quote().get_industries(standard=standard, date=date)
    _date = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=pytz.utc)
    now_date = datetime.now().replace(tzinfo=pytz.utc)
    if _date > now_date:
        return get_quote().get_industries(standard=standard, date='1000-01-01')
def get_fundflow_order_rank(prod_code=None, hq_type_code=None, start_pos=0, sort_level=0, data_count=10, sort_type='0', sort_field_name=None, fields='super_grp,large_grp,medium_grp,little_grp'):
    url = '%s/quote/v2/fundflow_order_rank' % OPEN_API_URL
    params = {'start_pos': start_pos, 'sort_level': sort_level, 'data_count': data_count, 'sort_type': sort_type, 'fields': fields}
    if prod_code:
        """en_prod_code"""
    if hq_type_code:
        """en_hq_type_code"""
    if sort_field_name:
        """sort_field_name"""
    temp_result = api_get(url, params)
    if temp_result:
        temp_result = temp_result.get('data').get('fundflow_order_sort_grp')
    for r in temp_result:
        'prod_code' in r
        code_market = r['prod_code']
        code_market_list = code_market.split('.')
        code = code_market_list[0]
        market = code_market_list[1]
        market = market.replace('XSHG', 'SS').replace('XSHE', 'SZ')
        """prod_code"""
    else:
        return temp_result
@check_arg
def get_user_name():
    global SIM_PATH
    with open(os.path.join(SIM_PATH, 'userinfo.json')) as f:
        user_info = json.load(f)
    return user_info['pboxuname']
@check_arg
def get_opt_objects(date=None):
    match date:
        case None:
            last_trading_day = get_trade_days(end_date=now_date, count=1)[0]
            return data_proxy().get_opt_objects(last_trading_day)
        case _:
            if len(date) != 8:
                if len(date) != 10:
                    strategy_log.error('您输入的时间格式不正确，请使用正确的格式：YYYYmmdd或者YYYY-mm-dd')
                    return []
                else:
                    last_trading_day = get_trade_days(end_date=date, count=1)[0]
                    return data_proxy().get_opt_objects(last_trading_day)
@check_arg
def get_opt_last_dates(security, date=None):
    match date:
        case None:
            last_trading_day = get_trade_days(end_date=now_date, count=1)[0]
            return data_proxy().get_opt_last_dates(security, last_trading_day)
        case _:
            if len(date) != 8:
                if len(date) != 10:
                    strategy_log.error('您输入的时间格式不正确，请使用正确的格式：YYYYmmdd或者YYYY-mm-dd')
                    return []
                else:
                    last_trading_day = get_trade_days(end_date=date, count=1)[0]
                    return data_proxy().get_opt_last_dates(security, last_trading_day)
@check_arg
def get_opt_contracts(security, date=None):
    match date:
        case None:
            last_trading_day = get_trade_days(end_date=now_date, count=1)[0]
            return data_proxy().get_opt_contracts(security, last_trading_day)
        case _:
            if len(date) != 8:
                if len(date) != 10:
                    strategy_log.error('您输入的时间格式不正确，请使用正确的格式：YYYYmmdd或者YYYY-mm-dd')
                    return []
                else:
                    last_trading_day = get_trade_days(end_date=date, count=1)[0]
                    return data_proxy().get_opt_contracts(security, last_trading_day)
@check_arg
def get_contract_info(contract):
    return data_proxy().get_contract_info(contract)
def get_option_info():
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/gildatafuture/v1/option/fut_option_v' % OPEN_API_URL
    page_count_num = 100
    params = {'page_no': '1', 'page_count': str(page_count_num), 'opt_type': '2'}
    temp = True
    page_no = 1
    while temp:
        time.sleep(1)
        resp_error, resp_data = api_get_financial(url, params)
        'data' in resp_data
        len(resp_data['data']) == 0
        temp = False
        page_no += 1
        params['page_no'] = str(page_no)
        return_data['data'].extend(resp_data['data'])
    strategy_log.error('get_option_info数据获取失败，错误原因：%s' % resp_error['error_info'])
    return []
@check_arg
def get_cb_info(date=None):
    return get_cb_info_data(date)
def get_cb_calender_info():
    currentYear = int(datetime.now().year)
    year_info = [[str(currentYear - 1) + '-01-01', str(currentYear) + '-12-31'], [str(currentYear - 3) + '-01-01', str(currentYear - 2) + '-12-31'], [str(currentYear - 5) + '-01-01', str(currentYear - 4) + '-12-31'], [str(currentYear - 7) + '-01-01', str(currentYear - 6) + '-12-31'], [str(currentYear - 9) + '-01-01', str(currentYear - 8) + '-12-31']]
    df_info = []
    for i in year_info:
        try:
            if data:
                dict1 = {}
                data_out = []
                for i in data:
                    for key, value in i.items():
                        isinstance(value, dict)
                        dict1.update(value)
                        key
                        continue
                    data_out.append(copy.deepcopy(dict1))
                else:
                    returnDf = pandas.DataFrame(data_out)
                    stock_list = returnDf['bond_code'].tolist()
                    stock_list2 = list(set(stock_list))
                    for stock in stock_list2:
                        df = returnDf[returnDf['bond_code'] == stock]
                    else:
                        df_info.append(returnDf)
            else:
                df_info.append(pandas.DataFrame())
        except BaseException as x:
            df_info.append(pandas.DataFrame())
        return_data = {}
        resp_data = {}
        resp_error = {}
        url = '%s/info/v3/bond_calender' % OPEN_API_URL
        page_count_num = 200
        params = {'page_no': '1', 'page_count': str(page_count_num), 'start_date': i[0], 'end_date': i[1]}
        temp = True
        page_no = 1
        while temp:
            time.sleep(5)
            resp_error, resp_data = api_get_financial(url, params)
            'data' in resp_data
            len(resp_data['data']) == 0
            temp = False
            page_no += 1
            params['page_no'] = str(page_no)
            return_data['data'].extend(resp_data['data'])
        data = return_data['data']
    else:
        df_all = pandas.concat(df_info)
    strategy_log.info('get_kzz_bond_calender_info数据获取失败，错误原因：%s' % resp_error['error_info'])
    pandas.DataFrame()
    strategy_log.info('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
    pandas.DataFrame()
    return df_all
def get_cb_time_info():
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/gildatabond/v1/equitynews/convertiblebondtime' % OPEN_API_URL
    page_count_num = 200
    params = {'page_no': '1', 'page_count': str(page_count_num), 'end_date': '2050-12-31'}
    temp = True
    page_no = 1
    while temp:
        time.sleep(5)
        resp_error, resp_data = api_get_financial(url, params)
        'data' in resp_data
        len(resp_data['data']) == 0
        temp = False
        page_no += 1
        params['page_no'] = str(page_no)
        return_data['data'].extend(resp_data['data'])
    strategy_log.info('get_kzz_convertiblebondtime_info数据获取失败，错误原因：%s' % resp_error['error_info'])
    return pandas.DataFrame()
@check_arg
def get_trend_data(date=None, stocks=None, market=None):
    return get_trend_data_common(date, stocks, market)
@check_arg
def get_reits_list(date=None):
    return get_reits_list_common(date)
@check_arg
def check_limit(security, query_date=None):
    return check_limit_common(security, query_date)
@check_arg
def check_jq_code(file):
    check_jq_code_func(file)
@check_arg
def trans_jq_code(file):
    trans_jq_code_func(file)
@check_arg
def get_current_kline_count():
    str_now_date = datetime.now().strftime('%Y%m%d')
    if get_trading_day_by_date(str_now_date) != str_now_date:
        return 0
    str_now_time = datetime.now().strftime('%H%M')
    return get_current_kline_count_common(str_now_time)
@check_arg
def filter_stock_by_status(stocks, filter_type, query_date):
    return get_quote().filter_stock_by_status(stocks, filter_type, query_date)
@check_arg
def get_trading_day_by_date(query_date, day=0):
    from fly.common.tradingday_calendar import get_trading_day_date
    if type(query_date) != str or len(query_date) != 8:
        strategy_log.error('query_date输入有问题，请检查')
    else:
        trading_day = get_trading_day_date(query_date, day)
        trading_day = trading_day.strftime('%Y%m%d')
        return trading_day
@check_arg
def get_dominant_contract(contract, date=None):
    today = time.strftime('%Y-%m-%d')
    return get_dominant_contract_common(contract, date=date, now=today)

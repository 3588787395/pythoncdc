# Source Generated with Decompyle++ (Python version)
# File: quotation.pyc (Python 3.11)

global quote
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
    else:
        class Void(object):
            def __getattr__(self, item):
                return self
            def __setattr__(self, item, value):
                return None
            def __call__(self, *args, **kwargs):
                return None
            def __repr__(self):
                return '<Void>'
        return (Void(), False)
def get_quote():
    global quote
    log, is_trade = getLogger()
    if quote == None and is_trade:
        """trade"""
    else:
        """backtest"""
    return quote
def get_real_param(param):
    params = {'open_px': 'open', 'close_px': 'close', 'high_px': 'high', 'low_px': 'low', 'business_amount': 'volume', 'business_balance': 'money'}
    if params.get(param) is None:
        return param
    else:
        return params.get(param)
def get_open_param(param):
    params = {'open': 'open_px', 'close': 'close_px', 'high': 'high_px', 'low': 'low_px', 'volume': 'business_amount', 'money': 'business_balance'}
    if params.get(param) is None:
        return param
    else:
        return params.get(param)
def get_real_exrights_param(param):
    params = {'date': 'date', 'allotted_ps': 'allottedCount', 'rationed_ps': 'rationedCount', 'rationed_px': 'rationedPrice', 'bonus_ps': 'bonusPrice', 'exer_forward_a': 'exer_forward_a', 'exer_forward_b': 'exer_forward_b', 'exer_backward_a': 'exer_backward_a', 'exer_backward_b': 'exer_backward_b', 'dynamic_exer_forward_a': 'dynamic_exer_forward_a', 'dynamic_exer_forward_b': 'dynamic_exer_forward_b'}
    if params.get(param) is None:
        return param
    else:
        return params.get(param)
def get_token():
    global OPNE_TOKEN_PATH
    token_value = ''
    if not os.path.exists(OPNE_TOKEN_PATH):
        return token_value
    else:
        with open(OPNE_TOKEN_PATH, 'r') as f:
            token_value = f.read()
        return token_value
def api_get(url, params=None, request_times=1):
    token_value = get_token()
    if not token_value:
        print('ERROR:获取token失败！')
    elif params:
        encode_params = urllib.parse.urlencode(params, encoding='gbk')
        real_url = url + '?' + encode_params
    else:
        real_url = url
def api_get_financial(url, params=None, request_times=0):
    token_value = get_token()
    if not token_value:
        print('ERROR:获取token失败！')
    else:
        try:
            response = requests.get(real_url, headers=headers, data=data)
            return_data = response.json()
        except ConnectionRefusedError as e1:
            system_log.error(get_traceback_message())
            error_no = -1
            error_info = e1
            ({'error_no': error_no, 'error_info': error_info}, {})
            return None
        except HTTPError as e2:
            if HTTPError:
                pass
            else:
                if BaseException:
                    pass
            error_no = e2.code
            if not e2.response:
                error_info = None
                del e2
            try:
                error_info = json.loads(e2.response.body.decode('utf8', 'replace'))
            except ValueError:
                system_log.error(get_traceback_message())
                error_info = str(e2.response.body.decode('utf8', 'replace'))
        real_url = url_concat(url, params)
        headers = {'Authorization': 'Bearer %s' % token_value}
        data = params
        return_data = None
        return ({'error_no': 0, 'error_info': ''}, return_data)
def get_kline(get_type, prod_code, candle_period, candle_mode=None, search_direction=None, date=None, min_time=None, data_count=None, start_date=None, end_date=None):
    prod_code = prod_code.replace('.XSHE', '.SZ')
    prod_code = prod_code.replace('.XSHG', '.SS')
    url = '%s/kline' % OPEN_API_QUOTE_URL
    params = {'get_type': get_type, 'prod_code': prod_code, 'candle_period': candle_period}
    if candle_mode:
        params['candle_mode'] = candle_mode
    if search_direction:
        params['search_direction'] = search_direction
    if date:
        params['date'] = date
    if min_time:
        params['min_time'] = min_time
    if data_count:
        params['data_count'] = data_count
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    return kline_to_dataframe(api_get(url, params).get('data').get('candle'), prod_code)
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
            system_log.error(get_traceback_message())
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
    i = 0
    for item in fields:
        if time_index != i:
            df[get_real_param(item)] = []
        i = i + 1
    else:
        prod = data.get(prod_code)
        prod
    prod = data.get(prod_code)
    for item in prod:
        i = 0
        i = 0
        for v in item:
            if time_index != i:
                df[get_real_param(fields[i])].append(v)
            elif time_index is not None:
                v = str(v)
                if i == 0:
                    if len(v) == 8:
                        index.append(f"{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} {'00'!s}:{'00'!s}:{'00'!s}")
                    elif i == 0 and len(v) == 10:
                        index.append(f"{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} {v[8:10]!s}:{'00'!s}:{'00'!s}")
                    elif i == 0:
                        index.append(f"{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} 0{v[8:9]!s}:{v[9:11]!s}:{'00'!s}")
                    elif i == 0:
                        index.append(f"{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} {v[8:10]!s}:{v[10:12]!s}:{'00'!s}")
                    elif i == 0:
                        index.append(f'{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} {v[8:10]!s}:{v[10:12]!s}:{v[12:14]!s}')
                elif i == 0 and len(v) == 10:
                    pass
                elif i == 0:
                    pass
                elif i == 0:
                    pass
                elif i == 0:
                    pass
            i = i + 1
        else:
            continue
    else:
        columns = []
        if data_type is None:
            i = 0
            for item in fields:
                if time_index != i:
                    columns.append(get_real_param(item))
                i = i + 1
    columns = ['open', 'close', 'high', 'low', 'volume', 'money']
    return pandas.DataFrame(df, columns=columns, index=index)
def kline_to_dataframe(data, prod_code):
    return one_prod_to_dataframe(data, prod_code, 'kline')
def datetimeindex_astype(daterange, typet=6):
    if len(daterange) > 0:
        pydate_array = daterange.to_pydatetime()
        if typet == 1:
            date_only_array = numpy.vectorize(lambda s: s.strftime('%Y-%m-%d %H:%M:%S'))(pydate_array)
        else:
            date_only_array = numpy.vectorize(lambda s: s.strftime('%Y-%m-%d'))(pydate_array)
        date_only_series = pandas.Series(date_only_array)
        return date_only_series
def fill_minute_or_day_blank(klines, nowstart, nowend, typet, stocks, forward='pre'):
    if nowend >= nowstart:
        source_start = len(source_start[8:]) == 4 and source_start[8:] or '0000'
        source_end = source_end[8:] or '1530'
        suffix = stocks.split('T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix)
        source_start = nowstart
        source_end = nowend
        dts = get_minute_or_day_fill_time(suffix, typet, nowstart, nowend)
        len(dts) > 0
        dts = dts.index
        if forward == 'back':
            temp_close = numpy.array([klines['close'][-1]] * len(dts))
            temp_value = numpy.array([numpy.nan] * len(dts))
            klines_back = pandas.DataFrame({'open': temp_close, 'close': temp_close, 'high': temp_close, 'low': temp_close, 'volume': temp_value, 'money': temp_value}, index=dts)
            klines = pandas.concat([klines, klines_back])
        else:
            temp_value = numpy.array([numpy.nan] * len(dts))
            klines_pre = pandas.DataFrame({'open': temp_value, 'close': temp_value, 'high': temp_value, 'low': temp_value, 'volume': temp_value, 'money': temp_value}, index=dts)
            klines = pandas.concat([klines_pre, klines], sort=True)
    return klines
def load_minute_or_day_kline(stocks, typet, start, end):
    global is_binary
    if is_binary == '1':
        if len(start) > 8:
            tmp_start = start[:8]
        else:
            tmp_start = start
        if len(end) > 8:
            tmp_end = end[:8]
        else:
            tmp_end = end
        klines = data_proxy().get_kline_binary(stocks, typet, tmp_start, tmp_end)
    else:
        klines = data_proxy().get_kline_local(stocks, typet, start, end)
    if klines.empty:
        klines = fill_minute_or_day_blank(klines, start, end, typet, stocks)
    elif onlinestart <= end[:8] and onlinestart <= nowdate:
        if end[:8] < nowdate:
            end = end
        else:
            end = nowdate
    else:
        klines = fill_minute_or_day_blank(klines, onlinestart, end, typet, stocks, forward='back')
    return klines
@lru_cache(None)
def get_minute_or_day_fill_time(suffix, typet, start, end):
    global is_binary
    if suffix in ('SS', 'SZ', 'XSHG', 'XSHE', 'CCFX') or typet in (6, 7, 8):
        benchmark = '000300.SS'
        if is_binary == '1':
            klines = data_proxy().get_kline_binary(benchmark, typet, start, end)
        else:
            klines = data_proxy().get_kline_local(benchmark, typet, start, end)
        dts = klines
    else:
        dts = build_future_fill_time(suffix, typet, start, end)
        dts = pandas.Series(numpy.random.randn(len(dts)), index=dts)
    return dts
def build_future_fill_time(suffix, typet, start, end):
    all_days = pandas.date_range(start=start[:8], end=end[:8], freq='B')
    holidays = data_proxy().get_holiday_local()
    trade_days = []
    for item in all_days:
        if item.strftime('%Y%m%d') not in holidays:
            trade_days.append(item.strftime('%Y-%m-%d'))
    else:
        if typet == 5 or typet == 1:
            pass
    tmp = MarketTime.get_instance().get_market_time(suffix)
    open_am = tmp['open_am'][:2] + ':' + tmp['open_am'][-2:] + ':00'
    close_am = tmp['close_am'][:2] + ':' + tmp['close_am'][-2:] + ':00'
    open_pm = tmp['open_pm'][:2] + ':' + tmp['open_pm'][-2:] + ':00'
    close_pm = tmp['close_pm'][:2] + ':' + tmp['close_pm'][-2:] + ':00'
    market_time = {'open_am': open_am, 'close_am': close_am, 'open_pm': open_pm, 'close_pm': close_pm, 'freq': 'T'}
    out_trade_times = pandas.date_range(start=market_time['close_am'], end=market_time['open_pm'], freq=market_time['freq'])[1:-1]
    trade_times = pandas.date_range(start=market_time['open_am'], end=market_time['close_pm'], freq=market_time['freq'])
    trade_times = trade_times[~numpy.in1d(trade_times, out_trade_times)]
    for today in trade_days:
        for item in trade_times:
            total_dts.append(today + item)
        else:
            continue
    suffix == 'T.CCFX' if typet == 2 else suffix == 'T.CCFX' if typet == 3 else suffix == 'T.CCFX' if typet == 4 else typet == 13
    if suffix in ('XZCE', 'XDCE', 'XSGE'):
        dt_am = pandas.date_range(start=market_time['open_am1'], end=market_time['close_am1'], freq=market_time['freq'])
        dt_am2 = pandas.date_range(start=market_time['open_am2'], end=market_time['close_am2'], freq=market_time['freq'])
        dt_am = dt_am.append(dt_am2)
    else:
        dt_am = pandas.date_range(start=market_time['open_am'], end=market_time['close_am'], freq=market_time['freq'])
    dt_pm = pandas.date_range(start=market_time['open_pm'], end=market_time['close_pm'], freq=market_time['freq'])
    trade_times = dt_am.append(dt_pm)
    for today in trade_days:
        for item in trade_times:
            total_dts.append(today + item)
        else:
            continue
    if suffix in ('XZCE', 'XDCE', 'XSGE'):
        dt_am = pandas.date_range(start=market_time['open_am1'], end=market_time['close_am1'], freq=market_time['freq'])
        dt_am2 = pandas.date_range(start=market_time['open_am2'], end=market_time['close_am2'], freq=market_time['freq'])
        dt_am = dt_am.append(dt_am2)
    else:
        dt_am = pandas.date_range(start=market_time['open_am'], end=market_time['close_am'], freq=market_time['freq'])
    dt_pm = pandas.date_range(start=market_time['open_pm'], end=market_time['close_pm'], freq=market_time['freq'])
    trade_times = dt_am.append(dt_pm)
    for today in trade_days:
        for item in trade_times:
            total_dts.append(today + item)
        else:
            continue
    for today in trade_days:
        for item in market_time:
            total_dts.append(today + ' ' + item)
        else:
            continue
    if suffix in ('XZCE', 'XDCE', 'XSGE'):
        market_time = {'11:15:00', '15:00:00'}
    else:
        market_time = set()
    for today in trade_days:
        for item in market_time:
            total_dts.append(today + ' ' + item)
        else:
            continue
    if suffix == 'T.CCFX':
        market_time = ['10:30:00', '11:30:00', '14:00:00', '15:00:00', '15:15:00']
    elif suffix in ('XZCE', 'XDCE', 'XSGE'):
        market_time = ['10:00:00', '11:15:00', '14:15:00', '15:00:00']
    else:
        market_time = ['10:30:00', '11:30:00', '14:00:00', '15:00:00']
    for today in trade_days:
        for item in market_time:
            total_dts.append(today + ' ' + item)
        else:
            continue
    total_dts.sort()
    total_dts = pandas.to_datetime(total_dts)
    total_dts = pandas.to_datetime([])
    return total_dts
def change_future_real_date(stock, start, end):
    future_param = get_future_param(stock)
    if future_param:
        start = listing_date
        if delivery_date < end[:8]:
            end = delivery_date
        listing_date = listing_date.strftime('%Y%m%d')
        if listing_date > start[:8]:
            start = listing_date
        end = delivery_date
def filter_duplicated_date(klines):
    isdup = list(klines.duplicated(['date']))
    if True in isdup:
        klines = klines.drop_duplicates(['date'])
    del klines['date']
    return klines
def build_current_period_df(nowdataframe, index_data=False):
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
        tmp = pandas.DataFrame(tempdict, index=index)
        return tmp
def load_bars_from_hundsun(stocks, typet, start, end):
    global DumploadDailyFile, is_utc
    source_end = end[8:] or '1530'
    source_end = end[8:] or '1530'
    collections(isinstance(stocks, str) if os.path.exists(DumploadDailyFile) and typet == 6 else len(start) > 8)
    if len(end[8:]) == 4:
        pass
    if len(diffset) < len(stocks):
        sectionstocks = list(set(stocks).intersection(set(dailypanel.items)))
        dailypanel = dailypanel.ix[:, source_start:source_end]
        retpanel = dailypanel.ix[sectionstocks, :]
        stocks = list(diffset)
    if len(end) > 8:
        end_temp = end[:8]
    else:
        end_temp = end
    if isinstance(stocks, str):
        klines.insert(5, 'price', klines['close'])
    else:
        for stock in stocks:
            klines = load_minute_or_day_kline(stock, typet, start_temp, end_temp)
            if klines is not None and 'price' not in klines:
                klines.insert(5, 'price', klines['close'])
            stock
        else:
            if typet == 6:
                panel = pandas.Panel(data, minor_axis=['open', 'close', 'high', 'low', 'volume', 'price', 'money', 'preclose', 'high_limit', 'low_limit', 'unlimited'])
            else:
                panel = pandas.Panel(data, minor_axis=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
        isinstance(stocks if isinstance(stocks, list) else typet == 6)
    len(start[8:]) == 4 if len(data) > 0 else is_utc == '0' if len(panel.major_axis) != 0 else retpanel.empty
def load_get_price(stocks, typet, start, end, count, fq=None):
    global is_utc
    _typet = 6
    if typet == 7:
        _typet = 7
        typet = 6
    if typet == 8:
        _typet = 8
        typet = 6
    if typet == 9:
        _typet = 9
        typet = 6
    if typet == 15:
        _typet = 15
        typet = 6
    panel = load_bars_from_hundsun(stocks, typet, start, end)
    if len(panel.major_axis) != 0:
        panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
        panel.major_axis = panel.major_axis.tz_localize('UTC').tz_convert('Asia/Shanghai')
    if fq == 'pre':
        exrights_data = get_exrights_data(stocks, start)
        for stock in panel.items:
            data = change_his_to_forward(stock, panel[stock], exrights_data, start, end, typet)
            stock
    elif fq == 'post':
        exrights_data = get_exrights_data(stocks, start)
        panel.items
        exrights_data = get_exrights_data(stocks, start)
        for stock in panel.items:
            data = change_his_to_backward(stock, panel[stock], exrights_data, start, end, typet)
            stock
    else:
        pass
    if _typet in (7, 8, 9, 15):
        panel = get_str_data(panel, count, _typet)
    if isinstance(stocks, str):
        rdata = panel[stocks]
    else:
        rdata = panel
    return rdata
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
        stock_df = rdata[stock]
        datetime_index = stock_df.index
        dates = []
        for i in datetime_index:
            dates.append(i)
        else:
            n = stock_df.iloc[:, 0].size
            datass_list = []
            datas_index = []
            j = (i := 0)
            while j < n:
                if _is_same_type_date(dates[i], dates[j], typet):
                    datas_index.append(j)
                    i = j
                    j += 1
                else:
                    datass_list.append(copy.deepcopy(datas_index))
                    datas_index = []
                    i = j
            else:
                if j == n:
                    datass_list.append(copy.deepcopy(datas_index))
        i = 0
        count = count if count else 0
        datass_list[-count:]
        for datas in datass_list[-count:]:
            is_all_nan = numpy.isnan(stock_df.ix[datas]['open'])
            not_nan_icount = 0
            data_is_nan = 0
            if not datas:
                continue
            is_all_nan = numpy.isnan(stock_df.ix[datas]['open'])
            not_nan_icount = 0
            data_is_nan = 0
            for j in range(len(is_all_nan)):
                if is_all_nan[j] == True and j == len(is_all_nan) - 1:
                    data_is_nan = 1
            else:
                numpy.nan if data_is_nan == 1 else stock_df.ix[datas[0]:datas[-1] + 1]['volume'].sum()
            numpy.nan
            stock_df.ix[datas[0]:datas[-1] + 1]['money'].sum()
            time_index.append(datetime_index[datas[-1]])
            i += 1
        else:
            data
            continue
    else:
        datas_penal = pandas.Panel(order_data, minor_axis=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
        return datas_penal
def _is_same_type_date(day1, day2, typet):
    if typet == 7:
        return True
    else:
        return True
def change_his_to_forward(security, data, exrights_data, start, end, typet):
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
        startDateIndex = datetime.strptime(start, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
        endDateIndex = datetime.strptime(end, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
        fields = ['open', 'close', 'high', 'low', 'price']
        if typet == 6:
            fields = ['open', 'close', 'high', 'low', 'price', 'preclose', 'high_limit', 'low_limit']
        series = exrights_data[security]
        if series.empty:
            return data
        elif series[startDateIndex:].empty:
            return data
        elif startDateIndex == endDateIndex and n == startDateIndex and len(series[startDateIndex:].index) > 1:
            if len(series[startDateIndex:].index) > 1:
                n = list(series[startDateIndex:].index)[1]
            else:
                return data
            data = data * float(series.loc[n, 'exer_forward_a']) + float(series.loc[n, 'exer_forward_b'])
            return round(data, 2)
        else:
            tmpstartindex = series[startDateIndex:].index[0]
            tmpstartindex = None
        tmpendindex = series[endDateIndex:].index[1]
        tmpendindex = None
        for n in list(series[tmpstartindex:tmpendindex].index):
            pass
        tmpdata = tmpdata.append(data[preindex:])
        if tmpdata is not None:
            data = tmpdata
        return data
def change_his_to_backward(security, data, exrights_data, start, end, typet):
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
        startDateIndex = datetime.strptime(start, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
        endDateIndex = datetime.strptime(end, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
        fields = ['open', 'close', 'high', 'low', 'price']
        if typet == 6:
            fields = ['open', 'close', 'high', 'low', 'price', 'preclose', 'high_limit', 'low_limit']
        series = exrights_data[security]
        if series.empty:
            return data
        elif series[:endDateIndex].empty:
            return data
        elif startDateIndex == endDateIndex:
            n = list(series[:endDateIndex].index)[-1]
            data[fields] = data[fields] * float(series.loc[n, 'exer_backward_a']) + float(series.loc[n, 'exer_backward_b'])
            return round(data, 2)
        elif len(series[:startDateIndex].index) > 1:
            if startDateIndex in series.index:
                if len(series[:startDateIndex].index) >= 2:
                    tmpstartindex = series[:startDateIndex].index[-2]
                else:
                    tmpstartindex = None
            else:
                tmpstartindex = series[:startDateIndex].index[-1]
        else:
            tmpstartindex = None
        if len(series[endDateIndex:].index) > 0:
            tmpendindex = series[endDateIndex:].index[0]
        else:
            tmpendindex = None
        firsttime = list(data.index)[0].tz_localize(None).to_pydatetime().strftime('%H%M%S')
        indexlist = list(series[tmpstartindex:tmpendindex].index)
        preindex = None
        tmpdata = None
        predataindex = None
        for n in indexlist:
            pass
        if predataindex and len(data[predataindex:]) > 0:
            data.loc[predataindex:data[predataindex:].index[-1], fields] = round(data[predataindex:][fields] * float(series.loc[preindex, 'exer_backward_a']) + float(series.loc[preindex, 'exer_backward_b']), 2)
            tmpdata = tmpdata.append(data[predataindex:])
        if tmpdata is not None:
            data = tmpdata
        return data
def get_exrights_data(stocks, start):
    if len(start) > 8:
        start = start[:8]
    index = datetime.strptime(start, '%Y%m%d').strftime('%Y-%m-%d %H:%M:%S')
    tmpData = load_get_exrights(stocks)
    tmpExrightsData = collections.OrderedDict()
    for sec, series in tmpData.items():
        if len(series[:index].index) > 1:
            if index in series.index:
                if len(series[:index]) >= 2:
                    tmpExrightsData[sec] = series[series[:index].index[-2]:]
                    continue
                tmpExrightsData[sec] = series[series[:index].index[-1]:]
                continue
            tmpExrightsData[sec] = series[series[:index].index[-1]:]
        else:
            tmpExrightsData[sec] = series
            continue
    else:
        return tmpExrightsData
def load_get_exrights(stocks):
    global DumploadDailyFile
    def choose_data_from_dict(exrightdict, stocks):
        retdata = collections.OrderedDict()
        for stock in stocks:
            stock
        else:
            return retdata
    data = collections.OrderedDict()
    if isinstance(stocks, list):
        stocks = list(set(stocks))
    isinstance(stocks, str) if os.path.exists(DumploadDailyFile) else isinstance(stocks, str)
    diffset = set(stocks).difference(set(exrightdict.keys()))
    if len(diffset) == 0:
        data = choose_data_from_dict(exrightdict, stocks)
        return data
    elif len(diffset) < len(stocks):
        sectionstocks = list(set(stocks).intersection(set(exrightdict.keys())))
        data = choose_data_from_dict(exrightdict, sectionstocks)
        stocks = list(diffset)
def load_get_index_stocks(stocks, date=None):
    data = []
    if isinstance(stocks, str):
        data = data_proxy().get_index_stocks_local(stocks, date)
    elif isinstance(stocks, list):
        stockslist = []
        stocks
        stockslist = []
        for stock in stocks:
            stockslist.extend(data_proxy().get_index_stocks_local(stock, date))
        else:
            data = list(set(stockslist))
            return data.sort(key=stockslist.index)
    return data
def load_get_industry_stocks(stocks):
    data = []
    if isinstance(stocks, str):
        data = data_proxy().get_industry_stocks_local(stocks)
    elif isinstance(stocks, list):
        stockslist = []
        stocks
        stockslist = []
        for stock in stocks:
            stockslist.extend(data_proxy().get_industry_stocks_local(stock))
        else:
            data = list(set(stockslist))
            return data.sort(key=stockslist.index)
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
@((None, None, 'daily', None, None, None, False))
def get_price(security, start_date=None, end_date=None, frequency='daily', fields=None, fq=None, count=None, is_dict=False):
    ClearAllCache()
    is_string = False
    if security is not None:
        if len(security) == 0:
            strategy_log.error('security不能为空')
        elif isinstance(security, six.string_types):
            is_string = True
            security = [security]
        elif fq == 'dypre':
            fq = 'pre'
@(('1d', None, None, None, False, False, None, 'nan', False))
def get_history(count, frequency='1d', field=None, security_list=None, fq=None, skip_suspended=False, include=False, query_date=None, fill='nan', is_dict=False):
    ClearAllCache()
    if count <= 0:
        strategy_log.error('count不能小于等于0')
    else:
        is_string = False
        if security_list is None:
            strategy_log.error('未传入security_list,股票不能为空')
        elif isinstance(security_list, six.string_types):
            is_string = True
            security_list = [security_list]
        elif frequency in OVER_WEEK_FREQUENCY and query_date == None:
            now_dt = datetime.now()
            query_date = now_dt
        else:
            query_date = datetime.strptime(query_date, '%Y%m%d')
        if query_date is None:
            now_dt = datetime.now()
            query_date = convert_dt_to_int(now_dt)
        else:
            query_date = int(query_date) * 1000000
        nd_array = get_history_common(security_list, count, query_date, frequency, field, fq, skip_suspended, include, fill, execution_date, is_string, is_dict)
        return nd_array
def get_date_and_count(query_date, count, candle_period):
    from fly.common.tradingday_calendar import get_trade_days
    query_date = datetime.strptime(query_date, '%Y%m%d')
    if candle_period == 7:
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
    elif candle_period == 8:
        year = query_date.year
        month = query_date.month
        query_date = datetime.strftime(query_date, '%Y%m%d')
        this_month_start_date = query_date[:6] + '01'
        if len(get_trade_days(this_month_start_date, query_date)) == 0:
            query_date = datetime.strptime(this_month_start_date, '%Y%m%d') - timedelta(1)
            query_date = datetime.strftime(query_date, '%Y%m%d')
            while count > 0:
                if month - count <= 0:
                    year -= 1
                    count -= month
                    month = 12
                else:
                    month = month - count
                    count = 0
            else:
                if month in (10, 11, 12):
                    start_date = str(year) + str(month) + '01'
                else:
                    start_date = str(year) + '0' + str(month) + '01'
        else:
            start_date = this_month_start_date
        while count == 1 and count > 0:
            if month - count <= 0:
                year -= 1
                count -= month
                month = 12
            else:
                month = month - count
                count = 0
        else:
            if month in (10, 11, 12):
                start_date = str(year) + str(month) + '01'
            else:
                start_date = str(year) + '0' + str(month) + '01'
    elif candle_period == 9:
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
    elif candle_period == 15:
        year = query_date.year
        month = query_date.month
        end_quater = (month - 1) // 3
        if end_quater == 0:
            end_date = str(year - 1) + '1231'
            this_quater_start_date = str(year) + '0101'
        if end_quater == 1:
            end_date = str(year) + '0331'
            this_quater_start_date = str(year) + '0401'
        if end_quater == 2:
            end_date = str(year) + '0630'
            this_quater_start_date = str(year) + '0701'
        if end_quater == 3:
            end_date = str(year) + '0930'
            this_quater_start_date = str(year) + '1001'
        query_date = datetime.strftime(query_date, '%Y%m%d')
        if len(get_trade_days(this_quater_start_date, query_date)) == 0:
            query_date = end_date
            month = int(this_quater_start_date[4:6])
            while count > 0:
                if month // 3 - count < 0:
                    year -= 1
                    count -= month // 3
                    month = 13
                else:
                    month = month - count * 3
                    count = 0
            else:
                if month in (10, 11, 12):
                    start_date = str(year) + str(month) + '01'
                else:
                    start_date = str(year) + '0' + str(month) + '01'
        else:
            start_date = this_quater_start_date
        while count == 1 and count > 0:
            if month // 3 - count < 0:
                year -= 1
                count -= month // 3
                month = 13
            else:
                month = month - count * 3
                count = 0
        else:
            if month in (10, 11, 12):
                start_date = str(year) + str(month) + '01'
        start_date = str(year) + '0' + str(month) + '01'
    return (start_date, query_date)
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
        params['output'] = fields
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif len(resp_data['data']['list']) == 0:
                temp = False
            page_no += 1
            return_data['data'].extend(resp_data['data']['list'])
    else:
        data = return_data['data']
    try:
        if data:
            data_out = []
            for i in data:
                data_out.append(i)
            else:
                returnDf = pandas.DataFrame(data_out)
                change_column_dict = {'return_on_equity': 'roe', 'net_asset_value_per_share': 'naps', 'stock_abbr': 'secu_abbr', 'stock_code': 'secu_code'}
                returnDf.rename(columns=change_column_dict, inplace=True)
                returnDf['trading_day'] = last_trading_day
                def get_IQE_code(code):
                    code = str(code)
                    if code[0] == '6':
                        code = code[:6] + '.SS'
                    else:
                        code = code[:6] + '.SZ'
                    return code
                returnDf['secu_code'] = returnDf.apply(lambda x: get_IQE_code(x['secu_code']), axis=1)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
@lru_cache(None)
def valuation(security, date=None, fields=None):
    if date and date != now_date:
        params['trading_date'] = date
    now_date = time.strftime('%Y%m%d')
    if date is None:
        last_trading_day = get_trade_days(end_date=now_date, count=1)[0]
    else:
        last_trading_day = get_trade_days(end_date=date, count=1)[0]
    security = eval(security)
    if fields:
        fields = eval(fields)
        fields = ','.join(fields)
        params['fields'] = fields
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif len(resp_data['data']) == 0:
                temp = False
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    else:
        data = return_data['data']
    try:
        if data:
            data_out = []
            for i in data:
                data_out.append(i)
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
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
        params['report_types'] = report_types
    else:
        params['report_types'] = '1,2,3,4'
    if start_year == None and end_year == None:
        time = qdt.datetime.now()
        params['start_year'] = str(time.year - 1)
        params['end_year'] = time.year
    elif start_year == None and end_year == None:
        time = qdt.datetime.now()
        params['start_year'] = start_year
        params['end_year'] = time.year
    elif start_year == None and end_year == None:
        params['start_year'] = str(int(end_year) - 1)
        params['end_year'] = end_year
    else:
        params['start_year'] = start_year
        params['end_year'] = end_year
    if fields:
        fields = eval(fields)
        fields = ','.join(fields)
        params['fields'] = fields
    if merge_type is None:
        params['merge_type'] = 2
    else:
        params['merge_type'] = 1
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            dict1 = {}
            data_out = []
            for i in data:
                for key, value in i.items():
                    if isinstance(value, dict):
                        dict1.update(value)
                        continue
                    dict1[key] = value
                    continue
                else:
                    data_out.append(copy.deepcopy(dict1))
                    continue
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
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
        params['report_types'] = report_types
    else:
        params['report_types'] = '1,2,3,4'
    end_year is None if start_year is None else end_year is None
    fields = eval(fields)
    fields = ','.join(fields)
    params['fields'] = fields
    if merge_type is None:
        params['merge_type'] = 2
    else:
        params['merge_type'] = 1
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            dict1 = {}
            data_out = []
            for i in data:
                for key, value in i.items():
                    if isinstance(value, dict):
                        dict1.update(value)
                        continue
                    dict1[key] = value
                    continue
                else:
                    data_out.append(copy.deepcopy(dict1))
                    continue
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
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
        params['report_types'] = report_types
    else:
        params['report_types'] = '1,2,3,4'
    end_year is None if start_year is None else end_year is None
    fields = eval(fields)
    fields = ','.join(fields)
    params['fields'] = fields
    if merge_type is None:
        params['merge_type'] = 2
    else:
        params['merge_type'] = 1
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            dict1 = {}
            data_out = []
            for i in data:
                for key, value in i.items():
                    if isinstance(value, dict):
                        dict1.update(value)
                        continue
                    dict1[key] = value
                    continue
                else:
                    data_out.append(copy.deepcopy(dict1))
                    continue
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
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
        params['report_types'] = report_types
    else:
        params['report_types'] = '1,2,3,4'
    end_year is None if start_year is None else end_year is None
    fields = eval(fields)
    fields = ','.join(fields)
    params['fields'] = fields
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            data_out = []
            for i in data:
                data_out.append(i)
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
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
        params['report_types'] = report_types
    else:
        params['report_types'] = '1,2,3,4'
    end_year is None if start_year is None else end_year is None
    fields = eval(fields)
    fields = ','.join(fields)
    params['fields'] = fields
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            data_out = []
            for i in data:
                data_out.append(i)
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
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
        params['report_types'] = report_types
    else:
        params['report_types'] = '1,2,3,4'
    end_year is None if start_year is None else end_year is None
    fields = eval(fields)
    fields = ','.join(fields)
    params['fields'] = fields
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            data_out = []
            for i in data:
                data_out.append(i)
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
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
        params['report_types'] = report_types
    else:
        params['report_types'] = '1,2,3,4'
    end_year is None if start_year is None else end_year is None
    fields = eval(fields)
    fields = ','.join(fields)
    params['fields'] = fields
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            data_out = []
            for i in data:
                data_out.append(i)
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
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
        params['report_types'] = report_types
    else:
        params['report_types'] = '1,2,3,4'
    end_year is None if start_year is None else end_year is None
    fields = eval(fields)
    fields = ','.join(fields)
    params['fields'] = fields
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            data_out = []
            for i in data:
                data_out.append(i)
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
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
        params['report_types'] = report_types
    else:
        params['report_types'] = '1,2,3,4'
    end_year is None if start_year is None else end_year is None
    fields = eval(fields)
    fields = ','.join(fields)
    params['fields'] = fields
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            data_out = []
            for i in data:
                data_out.append(i)
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
@lru_cache(None)
def share_change(security, start_year=None, end_year=None, fields=None):
    return_data = {}
    resp_data = {}
    resp_error = {}
    url = '%s/info/v3/share_change' % OPEN_API_URL
    page_count_num = 500
    params = {'page_no': '1', 'page_count': str(page_count_num)}
    security = eval(security)
    if start_year == None and end_year == None:
        params['start_year'] = start_year
    elif start_year == None and end_year == None:
        params['end_year'] = end_year
    elif start_year == None and end_year == None:
        params['start_year'] = start_year
        params['end_year'] = end_year
    max_stocks_num = 400
    respons_count = math.ceil(len(security) / max_stocks_num)
    for i in range(respons_count):
        temp = True
        page_no = 1
        while temp:
            stocks = security[max_stocks_num * i:max_stocks_num * (i + 1)]
            encode = ','.join(stocks)
            resp_error, resp_data = api_get_financial(url, params)
            if resp_error['error_no'] != 0:
                return (resp_error, pandas.DataFrame())
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                print('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return (resp_error, pandas.DataFrame())
            page_no += 1
            return_data['data'].extend(resp_data['data'])
    data = return_data['data']
    try:
        if data:
            data_out = []
            for i in data:
                data_out.append(i)
            else:
                returnDf = pandas.DataFrame(data_out)
                return ({'error_no': 0, 'error_info': ''}, returnDf)
        else:
            return ({'error_no': 0, 'error_info': ''}, pandas.DataFrame())
    except BaseException as x:
        raise x
def get_balance_statement(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None, merge_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
def get_income_statement(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None, merge_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
def get_cashflow_statement(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None, merge_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
def get_growth_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
def get_profit_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
def get_eps(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
def get_cash_collection_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
def get_operating_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
def get_debt_paying_ability(security, date=None, report_types=None, start_year=None, end_year=None, fields=None, date_type=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
def get_share_change(security, date=None, fields=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        else:
            try:
                column_basis = ['secu_code', 'secu_abbr', 'change_date']
                column_temp = get_fields('share_change_fields', fields)
                column = list(set(column_basis).union(set(column_temp)))
                list_base = ['secu_code', 'secu_abbr', 'change_date', 'shares_change_reason']
                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                year = date[:4]
                start_year = int(year) - 1
                end_year = year
                error_return, data_return = share_change(str(security), str(start_year), str(end_year), str(column))
                if error_return['error_no'] != 0:
                    print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                    return re_empty_data
                elif data_return.empty or 'secu_code' not in data_return.columns:
                    return DataFrame_temp
                else:
                    data_return = data_return[data_return.change_date < date]
                    re_data = data_return.sort('change_date', ascending=False).drop_duplicates(['secu_code'])
                    if re_data.empty:
                        return DataFrame_temp
                    else:
                        re_data = DataFrame_temp.replace('--', str(numpy.nan))
                        for i in re_data.columns:
                            if i not in list_base:
                                re_data[i] = re_data[i].astype('float64')
                        else:
                            index.name = re_data
                            return re_data
            except BaseException as x:
                raise x
            if date and isVaildDate(str(date)):
                date = change_date_format(date)
            match date:
                case None:
                    date = time.strftime('%Y-%m-%d')
def get_valuation(security, date=None, fields=None):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    else:
        security = re_security
        error_re, re_fields = convert_to_list(fields)
        if error_re['error_no'] != 0:
            return re_empty_data
        else:
            try:
                column_basis = ['secu_code', 'trading_day', 'total_value']
                column_temp = get_fields('valuation_fields', fields)
                column = list(set(column_basis).union(set(column_temp)))
                list_base = ['secu_code', 'secu_abbr', 'trading_day', 'turnover_rate', 'dividend_ratio']
                DataFrame_temp = pandas.DataFrame(index=security, columns=column).drop('secu_code', axis=1)
                error_return, data_return = valuation(str(security), date, str(column))
                if error_return['error_no'] != 0:
                    print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                    return re_empty_data
                elif data_return.empty:
                    return DataFrame_temp
                else:
                    data_return.index = data_return['secu_code'].tolist()
                    DataFrame_temp.update(data_return)
                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                    re_data.columns
                    re_data = DataFrame_temp.replace('--', str(numpy.nan))
                    for i in re_data.columns:
                        if i not in list_base:
                            re_data[i] = re_data[i].astype('float64')
                    else:
                        index.name = re_data
                        return re_data
            except BaseException as x:
                raise x
            fields = re_fields
            if date and isVaildDate(str(date)):
                date = change_date_format(date)
def get_valuation_new(security, date=None, fields=None, access_data_type=20):
    re_empty_data = pandas.DataFrame()
    re_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
        security = re_security
        security_list = security
        stock_list = []
        for stock in security:
            stock = stock[:6]
            stock_list.append(stock)
        else:
            security = stock_list
            error_re, re_fields = convert_to_list(fields)
            if error_re['error_no'] != 0:
                return re_empty_data
    else:
        try:
            column_temp = get_fields('valuation_new_fields', fields)
            column = []
            change_column_dict = {'return_on_equity': 'roe', 'net_asset_value_per_share': 'naps'}
            for i in column_temp:
                for k, v in change_column_dict.items():
                    match v:
                        case 0:
                            column.append(k)
                        case _:
                            pass
                else:
                    continue
            else:
                error_return, data_return = valuation_new(str(security), date, str(column))
                if error_return['error_no'] != 0:
                    print('获取GTN数据异常，请联系管理员，异常信息：%s' % error_return)
                    return re_empty_data
                elif data_return.empty:
                    column_basis = ['secu_code', 'trading_day', 'secu_abbr']
                    column = list(set(column_basis).union(set(column_temp)))
                    DataFrame_temp = pandas.DataFrame(index=security_list, columns=column).drop('secu_code', axis=1)
                    index.name = DataFrame_temp
                    return DataFrame_temp
                else:
                    data_return.index = data_return['secu_code'].tolist()
                    re_data = data_return.replace('--', str(numpy.nan))
                    list_base = []
                    list_base = ['secu_code', 'secu_abbr', 'trading_day']
                    columns_list = list(re_data.columns)
                    columns_list
                    re_data = data_return.replace('--', str(numpy.nan))
                    list_base = []
                    list_base = ['secu_code', 'secu_abbr', 'trading_day']
                    columns_list = list(re_data.columns)
                    for i in columns_list:
                        if i not in list_base:
                            re_data[i] = re_data[i].astype('float64')
                    else:
                        index.name = re_data
                        return re_data.drop('secu_code', axis=1)
        except BaseException as x:
            raise x
        fields = re_fields
        if date and isVaildDate(str(date)):
            date = date_str_type_change(date, '%Y-%m-%d', '%Y%m%d')
def isVaildDate(date):
    try:
        if '-' in date:
            time.strptime(date, '%Y-%m-%d')
        else:
            time.strptime(date, '%Y%m%d')
    except BaseException as x:
        raise x
def get_exrights(security):
    return load_get_exrights(security)
@check_arg
def check_index_code(index_code):
    if not isinstance(index_code, (str, list, tuple)):
        strategy_log.error(f'指数代码：{index_code!s}类型有误：{type(index_code)!s}')
        return False
    elif len(index_code) not in (9, 11):
        strategy_log.error('指数代码：%s长度有误' % index_code)
        return False
    elif '.' not in index_code:
        strategy_log.error('指数代码：%s格式有误' % index_code)
        return False
    elif index_code.split('.')[1] not in ('XSHG', 'XSHE', 'SS', 'SZ', 'XBHS'):
        strategy_log.error('指数代码：%s尾缀不识别' % index_code)
        return False
    else:
        index_code_list = data_proxy().get_blocks_codes_local('ZS')
@check_arg
def get_index_stocks(security, date=None):
    if date is not None:
        try:
            check_datetime(date)
            if len(date) != 8:
                strategy_log.error('您输入的时间：%s格式不正确，请使用正确的格式：YYYYmmdd' % date)
                return []
        except AssertionError:
            strategy_log.error('您输入的时间：%s格式不正确，请使用正确的格式：YYYYmmdd' % date)
            return []
    else:
        date = time.strftime('%Y%m%d', time.localtime())
        if check_index_code(security):
            result = load_get_index_stocks(security, date)
            return result
        else:
            return []
@check_arg
def get_Ashares(date=None):
    return get_quote().get_Ashares(date=date)
@check_arg
def get_Bshares(date=None):
    stocks = get_index_stocks(['000001.XBHS', '399106.XBHS'], date)
    real_return = []
    for item in stocks:
        if item[:1] not in ('0', '3', '6'):
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
        strategy_log.error(f'行业代码：{industry_code!s}类型有误：{type(industry_code)!s}')
        return False
    elif len(industry_code) not in (9, 11):
        strategy_log.error('行业代码：%s长度有误' % industry_code)
        return False
    elif '.' not in industry_code:
        strategy_log.error('行业代码：%s格式有误' % industry_code)
        return False
    elif industry_code.split('.')[1] not in ('SS', 'SZ', 'XBHS'):
        strategy_log.error('行业代码：%s尾缀不识别' % industry_code)
        return False
    else:
        industry_code_list = data_proxy().get_blocks_codes_local('HY')
@check_arg
def get_industry_stocks(security):
    if check_industry_code(security):
        return load_get_industry_stocks(security)
    else:
        return []
def check_stock(s):
    assert isinstance(s, str), "请使用字符串表示标的代码，例如'600570.SS'"
    assert 11 >= len >= 9, '请输入正确的标的代码'
    assert s.split('.')[1] in ('SS', 'SZ', 'CCFX', 'XDCE', 'XSGE', 'XZCE', 'XBHS', 'XINE'), "请输入标的代码以'SS','SZ','CCFX','XDCE','XSGE','XZCE', 'XBHS', 'XINE'结尾"
def check_stocks(l):
    if isinstance(l, str):
        l = l.replace('.XSHE', '.SZ')
        l = l.replace('.XSHG', '.SS')
        check_stock(l)
    elif isinstance(l, list) or isinstance(l, tuple):
        l
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            s = s.replace('.XSHG', '.SS')
            check_stock(s)
    else:
        raise RuntimeError('您的输入有误')
def check_frequency(frequency):
    global frequency_compat
    if frequency in frequency_compat:
        frequency = frequency_compat.get(frequency)
    if not (frequency[-1:] == 'm' and frequency[-1:] == 'd' and frequency == '1w' and frequency == 'mo' and frequency == '1q' and frequency == '1y'):
        assert frequency == '1y', "您输入的频率有误, 请使用'Xd'/'Xm'的形式, 或'daily'(等价于'1d'), 或'minute'(等价于'1m'), 或'week'(等价于'1w'), 或'month'(等价于'mo'), 或'quarter'(等价于'1q'), 或'year'(等价于'1y')"
    elif frequency not in ('1w', 'mo', '1y', '1q'):
        try:
            tmp = int(frequency[:-1])
        except BaseException:
            system_log.error(get_traceback_message())
            raise RuntimeError("您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数")
        else:
            if tmp > 0:
                raise RuntimeError("您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数")
    return frequency
def symbol(symbol_str):
    return str(symbol_str)
def dict_to_dataframe(data):
    df = {}
    for item in data[0].keys():
        item
    else:
        data
    for item in data:
        for k, v in item.items():
            df[k].append(v)
        else:
            continue
    else:
        return pandas.DataFrame(df)
def multi_prod_to_dataframe(data):
    df = {}
    fields = data.get('fields')
    for item in data.get('fields'):
        item
    else:
        index = []
        data.items()
    index = []
    for k, v in data.items():
        index.append(k)
        i = 0
        match k:
            case 'fields':
                i = 0
                for item in v:
                    df[fields[i]].append(item)
                    i = i + 1
                else:
                    continue
            case _:
                pass
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
        params['search_direction'] = search_direction
    if start_pos:
        params['start_pos'] = start_pos
    if data_count:
        params['data_count'] = data_count
    return tick_to_dataframe(api_get(url, params).get('data').get('tick'), prod_code)
def get_block_info(block_type):
    return data_proxy().get_block_info(block_type)
@check_arg
def get_market_detail(finance_mic):
    df = pandas.DataFrame()
    if not isinstance(finance_mic, str):
        return df
    else:
        finance_mic = finance_mic.replace('XSHG', 'SS').replace('XSHE', 'SZ')
        if finance_mic not in FINANCE_MIC_INFO:
            user_log.warning('请入参合法的市场代码')
            return df
        else:
            with open(file, 'rb') as f:
                loaded_dict = pickle.load(f)
            return pandas.DataFrame.from_dict(loaded_dict).T
        file = '/home/fly/data/market_detail_info/market_detail_%s_info.pickle' % finance_mic
def get_market_detail_online(finance_mic):
    df = pandas.DataFrame()
    url = '%s/market/detail' % OPEN_API_QUOTE_URL
    params = {'finance_mic': finance_mic}
    try:
        return dict_to_dataframe(api_get(url, params).get('data').get('market_detail_prod_grp'))
    except:
        system_log.error(get_traceback_message())
        return df
def get_klines(get_type, prod_code, candle_period, candle_mode=None, search_direction=None, date=None, min_time=None, data_count=None, start_date=None, end_date=None):
    url = '%s/kline' % OPEN_API_QUOTE_URL
    params = {'get_type': get_type, 'prod_code': prod_code, 'candle_period': candle_period}
    if candle_mode:
        params['candle_mode'] = candle_mode
    if search_direction:
        params['search_direction'] = search_direction
    if date:
        params['date'] = date
    if min_time:
        params['min_time'] = min_time
    if data_count:
        params['data_count'] = data_count
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    return kline_to_dataframe(api_get(url, params).get('data').get('candle'), prod_code)
def get_real(en_prod_code, fields=None):
    url = '%s/real' % OPEN_API_QUOTE_URL
    params = {'en_prod_code': en_prod_code}
    if fields:
        params['fields'] = fields
    return real_to_dataframe(api_get(url, params).get('data').get('snapshot'))
def get_trend(prod_code, fields=None, date=None, min_time=None):
    url = '%s/trend' % OPEN_API_QUOTE_URL
    params = {'prod_code': prod_code}
    if fields:
        fields = fields.split(',')
        temp = []
        for item in fields:
            temp.append(get_open_param(item))
        else:
            params['fields'] = ','.join(temp)
    if date:
        params['date'] = date
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
            params['fields'] = ','.join(temp)
    result = api_get(url, params).get('data').get('trend')
    return trend5day_to_dataframe(result, prod_code)
def convert_to_list(item):
    if item == '' or item == []:
        return ({'error_no': -1, 'error_info': '输入格式有误'}, [])
    elif not (item and isinstance(item, str) or isinstance(item, list)):
        return ({'error_no': -1, 'error_info': '输入格式有误'}, [])
    elif isinstance(item, str):
        item = item.strip().split(',')
        return ({'error_no': 0, 'error_info': ''}, item)
    else:
        return ({'error_no': 0, 'error_info': ''}, item)
def get_fields(fans, fields):
    dict_temp = {'balance_fields': {'financial_assets_obj': ['bought_sellback_assets', 'client_provi', 'deposit_in_interbank', 'derivative_assets', 'fixed_deposit', 'independence_account_assets', 'insurance_receivables', 'insurer_impawn_loan', 'lend_capital', 'loan_and_advance', 'other_assets', 'r_metal', 'receivable_claims_r', 'receivable_life_r', 'receivable_lt_health_r', 'receivable_subrogation_fee', 'receivable_unearned_r', 'refundable_capital_deposit', 'refundable_deposit', 'reinsurance_receivables', 'settlement_provi'], 'financial_liability_obj': ['advance_insurance', 'borrowing_capital', 'borrowing_from_centralbank', 'commission_payable', 'compensation_payable', 'deposit', 'deposit_of_interbank', 'deposits_received', 'derivative_liability', 'independence_liability', 'insurer_deposit_investment', 'life_insurance_reserve', 'lt_health_insurance_lr', 'other_liability', 'outstanding_claim_reserve', 'policy_dividend_payable', 'proxy_secu_proceeds', 'reinsurance_payables', 'sold_buyback_secu_proceeds', 'sub_issue_secu_proceeds', 'unearned_premium_reserve'], 'floating_capital_obj': ['account_receivable', 'advance_payment', 'bill_receivable', 'cash_equivalents', 'client_deposit', 'dividend_receivable', 'interest_receivable', 'inventories', 'non_current_asset_in_one_year', 'other_current_assets', 'other_receivable', 'total_current_assets', 'trading_assets'], 'floating_liability_obj': ['accounts_payable', 'advance_receipts', 'dividend_payable', 'impawned_loan', 'interest_payable', 'non_current_liability_in_one_year', 'notes_payable', 'other_current_liability', 'other_payable', 'salaries_payable', 'shortterm_loan', 'taxs_payable', 'total_current_liability', 'trading_liability'], 'non_floating_capital_obj': ['biological_assets', 'constru_in_process', 'construction_materials', 'deferred_tax_assets', 'development_expenditure', 'fixed_assets', 'fixed_assets_liquidation', 'good_will', 'hold_for_sale_assets', 'hold_to_maturity_investments', 'intangible_assets', 'investment_property', 'long_deferred_expense', 'longterm_equity_invest', 'longterm_receivable_account', 'oil_gas_assets', 'other_non_current_assets', 'seat_costs', 'total_non_current_assets'], 'non_floating_liability_obj': ['bonds_payable', 'deferred_tax_liability', 'estimate_liability', 'long_defer_income', 'long_salaries_pay', 'longterm_account_payable', 'longterm_loan', 'other_non_current_liability', 'specific_account_payable', 'total_non_current_liability'], 'owner_equity_obj': ['capital_reserve_fund', 'foreign_currency_report_conv_diff', 'minority_interests', 'ordinary_risk_reserve_fund', 'other_composite_income', 'other_equityinstruments', 'paidin_capital', 'retained_profit', 'se_without_mi', 'specific_reserves', 'surplus_reserve_fund', 'total_shareholder_equity', 'treasury_stock']}, 'income_fields': {'eps_obj': ['basic_eps', 'diluted_eps'], 'net_profit_obj': ['minority_profit', 'net_profit', 'np_parent_company_owners'], 'operating_payout_obj': ['administration_expense', 'amortization_expense', 'amortization_premium_reserve', 'amortization_reinsurance_cost', 'asset_impairment_loss', 'compensation_expense', 'financial_expense', 'insurance_commission_expense', 'operating_cost', 'operating_expense', 'operating_payout', 'operating_tax_surcharges', 'other_operating_cost', 'policy_dividend_payout', 'premium_reserve', 'refunded_premiums', 'reinsurance_cost', 'total_operating_cost'], 'operating_profit_obj': ['non_current_assetss_deal_loss', 'non_operating_expense', 'non_operating_income', 'operating_profit'], 'operating_revenue_obj': ['commission_expense', 'commission_income', 'interest_expense', 'interest_income', 'net_commission_income', 'net_interest_income', 'net_proxy_secu_income', 'net_subissue_secu_income', 'net_trust_income', 'operating_revenue', 'other_operating_revenue', 'premiums_earned', 'premiums_income', 'reinsurance', 'reinsurance_income', 'total_operating_revenue', 'unearned_premium_reserve'], 'special_revenue_obj': ['exchange_income', 'fair_value_change_income', 'invest_income', 'invest_income_associates', 'other_net_revenue'], 'total_profit_obj': ['income_tax_cost', 'total_profit']}, 'cashflow_fields': {'cash_and_equivalents_change_obj': ['cash_at_beginning_of_year', 'cash_at_end_of_year', 'cash_equivalents_at_beginning', 'cash_equivalents_at_end_of_year', 'net_incr_in_cash_and_equivalents'], 'cash_equivalent_increase_obj': ['begin_period_cash', 'cash_equivalent_increase', 'end_period_cash_equivalent'], 'change_effect_obj': ['exchan_rate_change_effect'], 'finance_cash_obj': ['borrowing_repayment', 'cash_from_bonds_issue', 'cash_from_borrowing', 'cash_from_invest', 'dividend_interest_payment', 'net_finance_cash_flow', 'other_finance_act_cash', 'other_finance_act_payment', 'subtotal_finance_cash_inflow', 'subtotal_finance_cash_outflow'], 'invest_cash_obj': ['fix_intan_other_asset_acqui_cash', 'fix_intan_other_asset_dispo_cash', 'impawned_loan_net_increase', 'invest_cash_paid', 'invest_proceeds', 'invest_withdrawal_cash', 'net_cash_deal_sub_company', 'net_cash_from_sub_company', 'net_invest_cash_flow', 'other_cash_from_invest_act', 'other_cash_to_invest_act', 'subtotal_invest_cash_inflow', 'subtotal_invest_cash_outflow'], 'net_operate_cash_obj': ['accrued_expense_added', 'assets_depreciation_reserves', 'defered_tax_asset_decrease', 'defered_tax_liability_increase', 'deferred_expense_amort', 'deferred_expense_decreased', 'financial_expense', 'fix_intanther_asset_dispo_loss', 'fixed_asset_depreciation', 'fixed_asset_scrap_loss', 'intangible_asset_amortization', 'inventory_decrease', 'invest_loss', 'loss_from_fair_value_changes', 'minority_profit', 'net_operate_cash_flow_notes', 'net_profit', 'operate_payable_increase', 'operate_receivable_decrease', 'others'], 'not_invest_and_finance_obj': ['cbs_expiring_within_one_year', 'debt_to_captical', 'fixed_assets_finance_leases'], 'operate_cash_obj': ['all_taxes_paid', 'commission_cash_paid', 'goods_and_services_cash_paid', 'goods_sale_service_render_cash', 'interest_and_commission_cashin', 'net_borrowing_from_central_bank', 'net_borrowing_from_finance_co', 'net_buyback', 'net_cash_for_reinsurance', 'net_deal_trading_assets', 'net_deposit_in_cb_and_ib', 'net_deposit_increase', 'net_insurer_deposit_investment', 'net_lend_capital', 'net_loan_and_advance_increase', 'net_operate_cash_flow', 'net_original_insurance_cash', 'net_reinsurance_cash', 'original_compensation_paid', 'other_cashin_related_operate', 'other_operate_cash_paid', 'policy_dividend_cash_paid', 'staff_behalf_paid', 'subtotal_operate_cash_inflow', 'subtotal_operate_cash_outflow', 'tax_levy_refund']}, 'growth_fields': ['avg_np_yoy_past_five_year', 'basic_eps_yoy', 'diluted_eps_yoy', 'end_date', 'eps_grow_rate_ytd', 'naor_yoy', 'net_asset_grow_rate', 'net_operate_cash_flow_yoy', 'net_profit_grow_rate', 'np_parent_company_cut_yoy', 'np_parent_company_yoy', 'oper_cash_ps_grow_rate', 'oper_profit_grow_rate', 'operating_revenue_grow_rate', 'publ_date', 'se_without_mi_grow_rate_ytd', 'secu_abbr', 'secu_code', 'sustainable_grow_rate', 'ta_grow_rate_ytd', 'total_asset_grow_rate', 'total_profit_grow_rate'], 'profit_fields': ['admini_expense_rate', 'admini_expense_rate_ttm', 'asset_impa_loss_to_tor', 'asset_impa_loss_to_tor_ttm', 'ebit', 'ebit_to_tor', 'ebit_to_tor_ttm', 'ebitda', 'end_date', 'financial_expense_rate', 'financial_expense_rate_ttm', 'gross_income_ratio', 'gross_income_ratio_ttm', 'net_profit', 'net_profit_cut', 'net_profit_ratio', 'net_profit_ratio_ttm', 'np_to_tor', 'np_to_tor_ttm', 'operating_expense_rate', 'operating_expense_rate_ttm', 'operating_profit_ratio', 'operating_profit_to_tor', 'operating_profit_to_tor_ttm', 'period_costs_rate', 'period_costs_rate_ttm', 'publ_date', 'roa', 'roa_ebit', 'roa_ebit_ttm', 'roa_ttm', 'roe', 'roe_avg', 'roe_cut', 'roe_cut_weighted', 'roe_ttm', 'roe_weighted', 'roic', 'sales_cost_ratio', 'secu_abbr', 'secu_code', 't_operating_cost_to_tor', 't_operating_cost_to_tor_ttm', 'total_profit_cost_ratio'], 'eps_fields': ['accumulation_fund_ps', 'basic_eps', 'capital_surplus_fund_ps', 'cash_flow_ps', 'cash_flow_ps_ttm', 'diluted_eps', 'ebitps', 'end_date', 'enterprise_fcf_ps', 'eps', 'eps_ttm', 'main_income_ps', 'naps', 'net_operate_cash_flow_ps', 'net_operate_cash_flow_ps_ttm', 'oper_profit_ps', 'operating_revenue_ps_ttm', 'publ_date', 'retained_earnings_ps', 'secu_abbr', 'secu_code', 'shareholder_fcf_ps', 'surplus_reserve_fund_ps', 'total_operating_revenue_ps', 'undivided_profit'], 'cash_collection_fields': ['capital_expenditure_to_dm', 'cash_equivalent_increase', 'cash_rate_of_sales', 'cash_rate_of_sales_ttm', 'end_date', 'free_cashflow', 'goods_sale_service_render_cash', 'net_operate_cash_flow', 'net_profit_cashcover', 'nocf_to_operating_ni', 'nocf_to_operating_ni_ttm', 'oper_cashin_to_asset', 'operating_revenue_cashcover', 'publ_date', 'sale_service_cash_to_or', 'sale_service_cash_to_or_ttm', 'secu_abbr', 'secu_code'], 'operating_fields': ['accounts_payables_turnover_days', 'accounts_payables_turnover_rate', 'accounts_receivables_turnover_days', 'accounts_receivables_turnover_rate', 'current_assets_turnover_rate', 'end_date', 'equity_turnover_rate', 'fixed_asset_turnover_rate', 'inventory_turnover_days', 'inventory_turnover_rate', 'oper_cycle', 'publ_date', 'secu_abbr', 'secu_code', 'total_asset_turnover_rate'], 'debt_paying_fields': ['current_ratio', 'debt_equity_ratio', 'debt_tangible_equity_ratio', 'ebitda_to_t_liability', 'end_date', 'interest_cover', 'long_debt_to_working_capital', 'nocf_to_current_liability', 'nocf_to_interest_bear_debt', 'nocf_to_net_debt', 'nocf_to_t_liability', 'opercashinto_current_debt', 'publ_date', 'quick_ratio', 'secu_abbr', 'secu_code', 'sewmi_to_interest_bear_debt', 'sewmi_to_total_liability', 'super_quick_ratio', 'tangible_a_to_interest_bear_debt', 'tangible_a_to_net_debt'], 'share_change_fields': ['secu_abbr', 'secu_code', 'change_date', 'total_shares', 'circulation_shares', 'a_shares', 'b_shares', 'a_circulation_shares', 'b_circulation_shares', 'restricted_shares', 'non_restricted_shares', 'shares_change_reason'], 'valuation_fields': ['trading_day', 'total_value', 'float_value', 'naps', 'pcf', 'secu_abbr', 'secu_code', 'ps', 'ps_ttm', 'pe_ttm', 'a_shares', 'a_floats', 'pe_dynamic', 'pe_static', 'b_floats', 'b_shares', 'h_shares', 'total_shares', 'turnover_rate', 'dividend_ratio', 'pb', 'roe'], 'valuation_new_fields': ['total_value', 'float_value', 'naps', 'pcf', 'ps', 'ps_ttm', 'pe_ttm', 'a_shares', 'a_floats', 'pe_dynamic', 'pe_static', 'b_floats', 'b_shares', 'h_shares', 'total_shares', 'turnover_rate', 'dividend_ratio', 'pb', 'roe']}
    if fans == 'balance_fields':
        dict_temp = dict_temp['balance_fields']
        if fields is None:
            list_return = []
            for key in dict_temp:
                list_return.extend(dict_temp[key])
        else:
            list_return = []
            list_return.extend(fields)
        return list_return
    elif fans == 'income_fields':
        dict_temp = dict_temp['income_fields']
    elif fans == 'cashflow_fields':
        dict_temp = dict_temp['cashflow_fields']
    elif not (fans in dict_temp.keys() and fields):
        return dict_temp
    else:
        dict_temp = fields
        return dict_temp
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
            data_list.append(data_tmp)
        else:
            continue
    else:
        data_filled = pandas.DataFrame(data_list, columns=data.columns)
        data = data.append(data_filled)
        return data
def date_convert(date, report_types):
    if report_types == None and month_temp == 1:
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
@((None, None, None, None, None, None, None, None, 1, True, False))
def get_fundamentals(security, table, fields=None, date=None, start_year=None, end_year=None, report_types=None, date_type=None, merge_type=None, end_date=None, count=1, is_dict=True, is_dataframe=False):
    today = time.strftime('%Y-%m-%d')
    return get_fundamentals_common(security, table, fields=fields, date=date, start_year=start_year, end_year=end_year, report_types=report_types, date_type=date_type, merge_type=merge_type, end_date=end_date, count=count, is_dict=is_dict, now=today, is_dataframe=is_dataframe)
def get_fundflow_day_single(prod_code, get_type='range', start_date=None, end_date=None, date=None, search_direction=None, data_count=None, trans_or_order=None):
    url = '%s/quote/v2/fundflow_day' % OPEN_API_URL
    params = {'prod_code': prod_code, 'get_type': get_type}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    if date:
        params['date'] = date
    if search_direction:
        params['search_direction'] = search_direction
    if data_count:
        params['data_count'] = data_count
    if trans_or_order:
        params['trans_or_order'] = trans_or_order
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
    elif isinstance(prod_code, list):
        for item in prod_code:
            returninfo = {}
            returninfo[item]: returninfo = get_fundflow_day_single(item, get_type, start_date, end_date, date, search_direction, data_count, trans_or_order)
            break
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
    return result
@check_arg
def get_stock_blocks(stock_code):
    return data_proxy().get_stock_blocks(stock_code)
@check_arg
def get_stock_exrights(stock_code, date=None):
    exrights = load_get_exrights(stock_code)[stock_code]
    exrights = exrights.copy()
    if exrights.empty:
        pass
    else:
        exrights.rename(columns={'allottedCount': 'allotted_ps', 'rationedCount': 'rationed_ps', 'rationedPrice': 'rationed_px', 'bonusPrice': 'bonus_ps'}, inplace=True)
        if date is None:
            return exrights
        elif isinstance(date, datetime) or isinstance(date, qdt.date):
            date = str(date)
        date = date.replace('-', '')[:8]
        if date.isdigit():
            date = int(date)
        return None
def get_valuation_info(count, date, stocks, filled=False):
    if isinstance(stocks, str):
        stock_list = [stocks]
        check_stocks(stock_list)
        date = str(date)
        date = check_datetime(date)
        data_dict = data_proxy().get_valuation_info(count, date, stock_list)
        if filled:
            trading_days = ('trading_days',)
            date_tmp = f'{date[:4]!s}-{date[4:6]!s}-{date[6:]!s}'
            index = trading_days[trading_days <= date_tmp][-count:].map(lambda x: x.strftime('%Y%m%d'))
            filled_df = pandas.DataFrame(index=index)
            for stock in data_dict:
                df = data_dict[stock]
                stock
            else:
                return data_dict
    elif isinstance(stocks, Iterable):
        stock_list = stocks
    return {}
def get_valuation_new_info(count, date, stocks, filled=False):
    if isinstance(stocks, str):
        stock_list = [stocks]
        check_stocks(stock_list)
        date = str(date)
        date = check_datetime(date)
        data_dict = data_proxy().get_valuation_new_info(count, date, stock_list)
        if filled:
            date_tmp = f'{date[:4]!s}-{date[4:6]!s}-{date[6:]!s}'
            trading_days = ('trading_days',)
            index = trading_days[trading_days <= date_tmp][-count:].map(lambda x: x.strftime('%Y%m%d'))
            filled_df = pandas.DataFrame(index=index)
            for stock in data_dict:
                df = data_dict[stock]
                stock
            else:
                return data_dict
    elif isinstance(stocks, Iterable):
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
        if filled:
            date_tmp = f'{date[:4]!s}-{date[4:6]!s}-{date[6:]!s}'
            trading_days = ('trading_days',)
            index = trading_days[trading_days <= date_tmp][-count:].map(lambda x: x.strftime('%Y%m%d'))
            filled_df = pandas.DataFrame(index=index)
            for stock in data_dict:
                df = data_dict[stock]
                stock
            else:
                return data_dict
    elif isinstance(stocks, Iterable):
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
    elif isinstance(field, str):
        field = [field]
    stock_info_pick = {}
    for stk in stocks:
        info_dict = {}
        info_dict = {}
        for item in field:
            item
        else:
            stock_info_pick[stk] = info_dict
            continue
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
    else:
        _date = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=pytz.utc)
        now_date = datetime.now().replace(tzinfo=pytz.utc)
        if _date > now_date:
            return get_quote().get_industries(standard=standard, date='1000-01-01')
        else:
            return get_quote().get_industries(standard=standard, date=date)
def get_fundflow_order_rank(prod_code=None, hq_type_code=None, start_pos=0, sort_level=0, data_count=10, sort_type='0', sort_field_name=None, fields='super_grp,large_grp,medium_grp,little_grp'):
    url = '%s/quote/v2/fundflow_order_rank' % OPEN_API_URL
    params = {'start_pos': start_pos, 'sort_level': sort_level, 'data_count': data_count, 'sort_type': sort_type, 'fields': fields}
    if prod_code:
        params['en_prod_code'] = prod_code
    if hq_type_code:
        params['en_hq_type_code'] = hq_type_code
    if sort_field_name:
        params['sort_field_name'] = sort_field_name
    temp_result = api_get(url, params)
    if temp_result:
        temp_result = temp_result.get('data').get('fundflow_order_sort_grp')
    for r in temp_result:
        if 'prod_code' in r:
            code_market = r['prod_code']
            code_market_list = code_market.split('.')
            code = code_market_list[0]
            market = code_market_list[1]
            market = market.replace('XSHG', 'SS').replace('XSHE', 'SZ')
            r['prod_code'] = code + '.' + market
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
    from fly.common.tradingday_calendar import get_trade_days
    now_date = time.strftime('%Y%m%d')
    if date is None:
        last_trading_day = get_trade_days(end_date=now_date, count=1)[0]
        return data_proxy().get_opt_objects(last_trading_day)
    elif len(date) != 8 and len(date) != 10:
        pass
@check_arg
def get_opt_last_dates(security, date=None):
    check_stocks(security)
    now_date = time.strftime('%Y%m%d')
    from fly.common.tradingday_calendar import get_trade_days
    if date is None:
        last_trading_day = get_trade_days(end_date=now_date, count=1)[0]
        return data_proxy().get_opt_last_dates(security, last_trading_day)
    elif len(date) != 8 and len(date) != 10:
        pass
@check_arg
def get_opt_contracts(security, date=None):
    from fly.common.tradingday_calendar import get_trade_days
    check_stocks(security)
    now_date = time.strftime('%Y%m%d')
    if date is None:
        last_trading_day = get_trade_days(end_date=now_date, count=1)[0]
        return data_proxy().get_opt_contracts(security, last_trading_day)
    elif len(date) != 8 and len(date) != 10:
        pass
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
        if resp_error['error_no'] != 0:
            strategy_log.error('get_option_info数据获取失败，错误原因：%s' % resp_error['error_info'])
            return []
        elif 'data' in resp_data:
            if len(resp_data['data']) == 0:
                temp = False
        else:
            strategy_log.error('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
            return []
        page_no += 1
        return_data['data'].extend(resp_data['data'])
    else:
        data = return_data['data']
    try:
        if data:
            dict1 = {}
            data_out = []
            for i in data:
                for key, value in i.items():
                    continue
                else:
                    data_out.append(copy.deepcopy(dict1))
                    continue
            else:
                return data_out
        else:
            return []
    except BaseException:
        strategy_log.error('ERROR:获取数据异常！')
        return []
@check_arg
def get_cb_info(date=None):
    return get_cb_info_data(date)
def get_cb_calender_info():
    currentYear = int(datetime.now().year)
    year_info = [[str(currentYear - 1) + '-01-01', str(currentYear) + '-12-31'], [str(currentYear - 3) + '-01-01', str(currentYear - 2) + '-12-31'], [str(currentYear - 5) + '-01-01', str(currentYear - 4) + '-12-31'], [str(currentYear - 7) + '-01-01', str(currentYear - 6) + '-12-31'], [str(currentYear - 9) + '-01-01', str(currentYear - 8) + '-12-31']]
    df_info = []
    for i in year_info:
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
            if resp_error['error_no'] != 0:
                strategy_log.info('get_kzz_bond_calender_info数据获取失败，错误原因：%s' % resp_error['error_info'])
                return pandas.DataFrame()
            elif 'data' in resp_data:
                if len(resp_data['data']) == 0:
                    temp = False
            else:
                strategy_log.info('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
                return pandas.DataFrame()
            page_no += 1
            return_data['data'].extend(resp_data['data'])
        else:
            data = return_data['data']
        try:
            if data:
                dict1 = {}
                data_out = []
                data
                dict1 = {}
                data_out = []
                for i in data:
                    for key, value in i.items():
                        if isinstance(value, dict):
                            dict1.update(value)
                            continue
                        dict1[key] = value
                        continue
                    else:
                        data_out.append(copy.deepcopy(dict1))
                        continue
                else:
                    returnDf = pandas.DataFrame(data_out)
                    stock_list = returnDf['bond_code'].tolist()
                    stock_list2 = list(set(stock_list))
                    stock_list2
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
    df_all = pandas.concat(df_info)
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
        if resp_error['error_no'] != 0:
            strategy_log.info('get_kzz_convertiblebondtime_info数据获取失败，错误原因：%s' % resp_error['error_info'])
            return pandas.DataFrame()
        elif 'data' in resp_data:
            if len(resp_data['data']) == 0:
                temp = False
        else:
            strategy_log.info('ERROR:返回数据为空，请查看输入的股票代码是否存在或数据源数据是否正常！')
            return pandas.DataFrame()
        page_no += 1
        return_data['data'].extend(resp_data['data'])
    else:
        data = return_data['data']
    try:
        if data:
            dict1 = {}
            data_out = []
            for i in data:
                for key, value in i.items():
                    if isinstance(value, dict):
                        dict1.update(value)
                        continue
                    dict1[key] = value
                    continue
                else:
                    data_out.append(copy.deepcopy(dict1))
                    continue
            else:
                returnDf = pandas.DataFrame(data_out)
                stock_list = returnDf['secu_code'].tolist()
                stock_list2 = list(set(stock_list))
                all_df_info = []
                stock_list2
            returnDf = pandas.DataFrame(data_out)
            stock_list = returnDf['secu_code'].tolist()
            stock_list2 = list(set(stock_list))
            all_df_info = []
            for stock in stock_list2:
                if len(df) > 1:
                    all_df_info.append(df.tail(1))
                    continue
                all_df_info.append(df)
                continue
            else:
                df_all = pandas.concat(all_df_info)
                return df_all
        else:
            return pandas.DataFrame()
    except BaseException as x:
        raise x
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
    else:
        str_now_time = datetime.now().strftime('%H%M')
        return get_current_kline_count_common(str_now_time)
@check_arg
def filter_stock_by_status(stocks, filter_type=, query_date=None):
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

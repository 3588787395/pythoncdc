# AST dump for get_multiminute_his_data_by_date
def get_multiminute_his_data_by_date(symbols, start_date, end_date, frequency=Frequency.DAILY.value, fields=None, fq=None, asset=None, dividends_all=None):
    his_data_dict = OrderedDict()
    count_min = 0
    if asset[symbols[0]].get('type', '') == 'FUTURE':
        _end_time = end_date // 100
        min_datetime = int(str(end_date // 1000000) + '0800')
        _1m_df_nan_data, _ = get_kline_time_by_asset('1m', _end_time, asset['trading_time'])
        _df_nan_data, _ = get_kline_time_by_asset(frequency, _end_time, asset['trading_time'])
        datetime_1m_list = _1m_df_nan_data['datetime'].tolist()
        if _end_time in datetime_1m_list and _end_time not in _df_nan_data['datetime'].tolist():
            index = _df_nan_data['datetime']
            left = index.tolist()[int(index.searchsorted(_end_time)) - 1]
            right = index.tolist()[int(index.searchsorted(_end_time))]
            count_min = len(_1m_df_nan_data.loc[(_1m_df_nan_data['datetime'] > left) & (_1m_df_nan_data['datetime'] <= _end_time)])
            _last_timestamp = right
    else:
        now_date = end_date // 1000000
        min_datetime = now_date * 1000000 + 93000
        am_close_market_datetime = now_date * 1000000 + 113000
        pm_open_market_datetime = now_date * 1000000 + 130000
        pm_close_market_datetime = now_date * 1000000 + 150000
        time_count = 0
        _end_time = 930
        if end_date > min_datetime:
            if pm_open_market_datetime > end_date > am_close_market_datetime:
                _end_time = am_close_market_datetime
            elif end_date > pm_close_market_datetime:
                _end_time = pm_close_market_datetime
            else:
                _end_time = end_date
            time_count = int((convert_int_to_datetime(_end_time) - convert_int_to_datetime(min_datetime)).seconds / 60)
        if _end_time >= pm_open_market_datetime:
            time_count -= 90
        count_min = time_count % int(frequency[:-1])
        _last_timestamp = int(datetime.datetime.strftime(datetime.datetime.strptime(str(_end_time // 100), '%Y%m%d%H%M') + datetime.timedelta(minutes=int(frequency[:-1]) - count_min), '%Y%m%d%H%M'))
    if count_min == 0:
        his_data_dict = get_kline_by_date_new(symbols, start_date, end_date, frequency, fields, fq, asset, dividends_all)
    else:
        need_exrights = 0
        dividends_stock = []
        tmp_fields = CAL_EXRIGHTS_COLUMNS
        if fq is not None and dividends_all is not None and isinstance(fields, str) and (fields not in tmp_fields) or isinstance(fields, list):
            if len(set(fields).intersection(set(tmp_fields))) == 0:
                need_exrights = 0
            elif fq in DIVIDEND_CALC_TYPE:
                dividends_stock = dividends_all.keys()
                need_exrights = 1
        for symbol in symbols:
            asset_one = asset[symbol]
            stock = symbol.replace('SS', 'XSHG').replace('SZ', 'XSHE')
            need_exrights_one = 0
            dividends = None
            if need_exrights == 1:
                if stock not in dividends_stock:
                    need_exrights_one = 0
                    dividends = None
                else:
                    need_exrights_one = need_exrights
                    dividends = dividends_all[stock]
            add_fre_minute_time = datetime.datetime.strptime(str(end_date), '%Y%m%d%H%M%S') + datetime.timedelta(minutes=int(frequency[:-1]))
            fix_query_date = int(datetime.datetime.strftime(add_fre_minute_time, '%Y%m%d%H%M%S'))
            his_data = get_kline_by_date_one(symbol, start_date, fix_query_date, frequency, None, fq, asset_one, need_exrights_one, dividends)
            if len(his_data) == 0:
                his_data_dict[symbol] = his_data[fields]
                continue
            _last_kline = get_kline_by_count(symbol, count_min, end_date, '1m', None, fq, True, execution_date=None, asset=asset_one, need_exrights=need_exrights_one, dividends=dividends)
            if not len(his_data) == 0:
                if his_data['datetime'][-1] != _last_timestamp:
                    his_data_dict[symbol] = his_data[fields]
                elif len(_last_kline) > 0:
                    his_data['open'][-1] = _last_kline['open'][0].copy()
                    his_data['high'][-1] = _last_kline['high'].max().copy()
                    his_data['low'][-1] = _last_kline['low'].min().copy()
                    his_data['close'][-1] = _last_kline['close'][-1].copy()
                    his_data['volume'][-1] = _last_kline['volume'].sum().copy()
                    his_data['money'][-1] = _last_kline['money'].sum().copy()
                    his_data['price'][-1] = _last_kline['price'][-1].copy()
                    his_data_dict[symbol] = his_data[fields]
                continue
    return his_data_dict

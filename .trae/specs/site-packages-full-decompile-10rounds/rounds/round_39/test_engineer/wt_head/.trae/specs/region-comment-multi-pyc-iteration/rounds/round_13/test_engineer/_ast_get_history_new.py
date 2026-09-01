# AST dump for get_history_new
def get_history_new(symbols, count, query_date, frequency=Frequency.DAILY.value, fields=None, fq=None, skip_suspended=False, include=False, fill='nan', execution_date=None, asset_all=None, tmp_dividends=None):
    if type(symbols) == str:
        symbols = [symbols]
    if frequency == Frequency.DAILY.value and (not include):
        his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include, execution_date, asset_all, tmp_dividends)
        return his_data_dict
    now_date = int(time.strftime('%Y%m%d'))
    am_open_datetime = now_date * 10000 + 930
    _query_date = query_date // 100
    query_date_dt = _query_date // 10000
    kline_data_dict = OrderedDict()
    if query_date_dt == now_date and _query_date > am_open_datetime:
        if len(asset_all) <= 0:
            return kline_data_dict
        else:
            df_nan_data = kline_datetime_list(count, _query_date, frequency, include, asset_all[symbols[0]].get('type', 'STOCK'))
            if fq != 'post':
                daily_dividends = None
            else:
                daily_dividends = tmp_dividends
            if frequency == Frequency.DAILY.value:
                real_data_dict = get_all_real_daily_kline(symbols, df_nan_data, fields, fq, daily_dividends)
            else:
                real_data_dict = get_all_real_minute_kline(symbols, df_nan_data, fields, fq, FREQUENCY_TO_INT[frequency], daily_dividends)
            if fill == 'pre' and frequency != Frequency.DAILY.value and (len(real_data_dict) > 0):
                check_field = check_fields_function(fields)
                if check_field:
                    for stock in real_data_dict.keys():
                        if np.isnan(real_data_dict[stock][check_field]).sum() == len(real_data_dict[stock]):
                            continue
                        elif np.isnan(real_data_dict[stock][check_field]).sum() > 0:
                            real_data_dict[stock] = fill_kline_data_by_pre(real_data_dict[stock])
                real_data_len = len(df_nan_data)
            real_data_len = len(df_nan_data)
            his_count = count - real_data_len
            if frequency.find(Frequency.DAILY.value) > -1:
                min_datetime = now_date * 1000000 + 83000
            else:
                min_datetime = now_date * 1000000 + 93000
            his_data = get_kline_by_count_new(symbols, his_count, min_datetime, frequency, fields, fq, False, execution_date, asset_all, tmp_dividends)
            if len(his_data) == 0:
                return real_data_dict
            else:
                for stock in real_data_dict.keys():
                    if len(his_data[stock]) == 0:
                        kline_data_dict[stock] = real_data_dict[stock]
                        continue
                    kline_data_dict[stock] = np.concatenate((his_data[stock], real_data_dict[stock]))
                return kline_data_dict
    if frequency in Multi_Minute_Frequency:
        his_data_dict = get_multiminute_his_data(symbols, count, query_date, frequency, fields, fq, skip_suspended, include, execution_date, asset_all, tmp_dividends)
    else:
        his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include, execution_date, asset_all, tmp_dividends)

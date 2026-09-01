# AST dump for get_kline_by_date_one
def get_kline_by_date_one(symbol, start_date, end_date, frequency=Frequency.DAILY.value, fields=None, fq=None, asset=None, need_exrights=0, dividends=None):
    if asset is None:
        history_data = EMPTY_BAR_NP_ARRAY if fields is None else EMPTY_BAR_NP_ARRAY[fields]
        return history_data
    else:
        try:
            data_ndarr = _all_bars_of_cache(symbol, start_date, end_date, frequency, asset)
            bars_ndarr = data_ndarr.copy()
            if len(bars_ndarr) == 0:
                history_data = EMPTY_BAR_NP_ARRAY if fields is None else EMPTY_BAR_NP_ARRAY[fields]
                return history_data
            else:
                bars_ndarr_datetime = bars_ndarr[BarDataEnum.DATETIME.value]
                start_time = convert_int14_to_int(start_date, frequency)
                end_time = convert_int14_to_int(end_date, frequency)
                left = bars_ndarr_datetime.searchsorted(start_time)
                right = bars_ndarr_datetime.searchsorted(end_time, side='right')
                bars_ndarr = bars_ndarr[left:right]
                if len(bars_ndarr) == 0:
                    history_data = EMPTY_BAR_NP_ARRAY if fields is None else EMPTY_BAR_NP_ARRAY[fields]
                    return history_data
                elif need_exrights == 0 or asset.get('type', '') == AssetType.FUTURE.value:
                    history_data = bars_ndarr if fields is None else bars_ndarr[fields]
                    return history_data
                elif need_exrights == 1:
                    dividend_dict = {key: [item[c] for c in DIVIDEND_COLUMNS] for key, item in dividends.items()}
                    exrights_bars_ndarr = get_exrights_data(bars_ndarr, symbol, frequency, fq, dividend_dict)
                    history_data = exrights_bars_ndarr if fields is None else exrights_bars_ndarr[fields]
        except BaseException:
            error_info = get_traceback_message()
            history_data = EMPTY_BAR_NP_ARRAY if fields is None else EMPTY_BAR_NP_ARRAY[fields]
        return history_data

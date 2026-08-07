# Source Generated with Decompyle++ (Python version)
# File: data_source_func.pyc (Python 3.11)

import time
from IQCommon import pandas as pd
from IQCommon.api.klinedata import get_price_common
from IQData import enumerate
from fly.data.quotation import get_merged_data, get_quote, get_exrights, get_index_stocks, get_industry_stocks, get_block_stocks, get_stock_blocks, get_market_list, get_market_detail, get_industries, get_Ashares, get_Bshares, get_valuation_info, get_opt_objects, get_opt_last_dates, get_opt_contracts, get_contract_info
from IQData.utils.pycompatibility import lru_cache
from IQData.plugins.plugin_system_fly_basicdata.fly_enum import EXRIGHTS_NEW_FIELDS_TO_OLD_FIELDS_DICT
from IQData.utils.common_func import get_trading_dates_storage, get_asset_storage
@lru_cache(1000)
def dsf_get_merger_data(old_secu_code=None, new_secu_code=None):
    return get_merged_data(old_secu_code, new_secu_code)
def dsf_get_000300_of_kline_data(frequency, start_date=None, end_date=None):
    if frequency == enumerate.Frequency.DAILY.value:
        tmp_type = 6
    elif frequency[-1] == enumerate.Frequency.MINUTE.value[-1]:
        tmp_type = 1
    else:
        tmp_type = 6
    if start_date is None:
        start_date = '20050101'
    if end_date is None:
        current_date = str(time.strftime('%Y%m%d'))
        end_date = current_date
    kline = get_price_common('000300.XSHG', str(start_date), str(end_date), '1d')
    re_data = kline.copy()
    if tmp_type == 1:
        index_list = list(kline.index)
        len_index_list = len(index_list)
        start_kline = pd.DataFrame()
        end_kline = pd.DataFrame()
        for i in range(len_index_list):
            tmp_date = index_list[i].strftime('%Y%m%d')
            start_kline = get_price_common('000300.XSHG', tmp_date, tmp_date, '1m')
            if not start_kline.empty:
                break
        for j in range(len_index_list - 1, -1, -1):
            tmp_date = index_list[j].strftime('%Y%m%d')
            end_kline = get_price_common('000300.XSHG', tmp_date, tmp_date, '1m')
            if not end_kline.empty:
                break
        tmp_data = start_kline.append(end_kline)
        if not tmp_data.empty:
            re_data = tmp_data
    return re_data
def dsf_is_st_stock(symbols, date=None):
    return get_quote().get_stock_status(symbols, 'ST', date)
def dsf_is_suspended(symbols, date=None):
    return get_quote().get_stock_status(symbols, 'HALT', date)
def dsf_is_delisting(symbols, date=None):
    return get_quote().get_stock_status(symbols, 'DELISTING', date)
def dsf_get_trading_dates_storage(path=None):
    return get_trading_dates_storage(path)
def dsf_get_asset_storage(path=None):
    return get_asset_storage(path)
def dsf_get_index_stocks(symbol, query_date=None):
    return get_index_stocks(symbol, query_date)
def dsf_get_industry_stocks(symbol, query_date=None):
    return get_industry_stocks(symbol)
def dsf_get_block_stocks(symbol, query_date=None):
    return get_block_stocks(symbol)
@lru_cache(1000)
def dsf_get_dividend(symbol):
    data_frame = get_exrights(symbol)[symbol]
    data_frame.rename(columns=EXRIGHTS_NEW_FIELDS_TO_OLD_FIELDS_DICT, inplace=True)
    return data_frame
def dsf_get_stock_blocks(symbol, query_date=None):
    return get_stock_blocks(symbol)
def dsf_get_market_list():
    return get_market_list()
def dsf_get_market_detail(finance_mic):
    return get_market_detail(finance_mic)
def dsf_get_industries(standard, date):
    return get_industries(standard, date)
def dsf_get_Ashares(date):
    return get_Ashares(date)
def dsf_get_Bshares(date):
    return get_Bshares(date)
def dsf_get_valuation_info(count, date, stocks, filled=False):
    return get_valuation_info(count, date, stocks, filled)
def dsf_get_all_security(types, date):
    return get_all_security(types, date)
def dsf_get_opt_objects(date):
    return get_opt_objects(date)
def dsf_get_opt_last_dates(security, date):
    return get_opt_last_dates(security, date)
def dsf_get_opt_contracts(security, date):
    return get_opt_contracts(security, date)
def dsf_get_contract_info(contract):
    return get_contract_info(contract)

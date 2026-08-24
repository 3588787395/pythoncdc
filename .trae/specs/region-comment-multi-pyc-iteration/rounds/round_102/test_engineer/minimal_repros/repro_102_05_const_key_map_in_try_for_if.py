"""R102-05 rich: BUILD_CONST_KEY_MAP dict (3 keys) in for+try/except+if.

fly_data_source.get_stock_info 同型富上下文:
连续两个共享 data[s]['..'] 前缀链的值表达式 + 条件表达式第三值,
外层 for + try/except KeyError + if data.get 三层嵌套。
"""
import datetime


def trans(data, stocks, system_log, get_traceback_message, _make):
    re_data = {}
    if isinstance(stocks, str):
        stocks = [stocks]
    for stock in stocks:
        tem_dict = {}
        try:
            if data.get(stock, {}):
                data_trans = {
                    'stock_name': data[stock]['name'],
                    'listed_date': data[stock]['listed_date'].strftime('%Y-%m-%d'),
                    'de_listed_date': ('2900-01-01'
                                       if data[stock]['delisted_date'] > datetime.datetime.now()
                                       else data[stock]['delisted_date'].strftime('%Y-%m-%d')),
                }
                tem_dict['stock_name'] = data_trans.get('stock_name')
        except KeyError:
            system_log.warning(get_traceback_message())
        re_data[stock] = tem_dict
    return re_data

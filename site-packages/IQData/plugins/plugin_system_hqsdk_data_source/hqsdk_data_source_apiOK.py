# Source Generated with Decompyle++ (Python version)
# File: hqsdk_data_source_api.pyc (Python 3.11)

from IQData.api.api_base import api_method
from IQData.engine import Engine
@api_method
def get_snapshot(symbol):
    """
    获取行情快照
    :param symbol | str: 代码
    :return: dict
    """
    return Engine.instance().hqsdk_handler.get_snapshot(symbol)
@api_method
def subscribe(symbol):
    """
    订阅行情快照
    :param symbol: str or list, 代码
    :return:
    """
    return Engine.instance().hqsdk_handler.subscribe(symbol)
@api_method
def unsubscribe(symbol):
    """
    退订行情快照
    :param symbol: str or list, 代码
    :return:
    """
    return Engine.instance().hqsdk_handler.unsubscribe(symbol)
@api_method
def get_kline_by_offset_hqsdk(symbol, date, data_count, frequency, fq):
    """
    按照偏移取K线,H5跳过停牌数据.
    :param symbol: str, 代码
    :param date: datetime.datetime, 查询日期
    :param data_count: int, 查询的根数
    :param frequency: str, '1d'表示日线, '1m'表示分钟线
    :param fq:str | None, 数据复权选项，默认不复权，支持pre-前复权，post-后复权，dypre-动态前复权，None-不复权
    :return: numpy.ndarray, 返回查询日期往前data_count根K线,包括查询端点
    """
    return Engine.instance().hqsdk_handler.get_kline_by_offset_hqsdk(symbol, date, data_count, frequency, fq)
@api_method
def get_kline_by_date_hqsdk(symbol, start_date, end_date, frequency, fq):
    """
    按日期范围取K线
    :param symbol:str, 代码
    :param start_date: int, 开始日期,格式为YYYYMMDD或者YYYYMMDDHHMM
    :param end_date: int, 结束日期
    :param frequency: str, '1d'表示日线, '1m'表示分钟线
    :param fq:str | None, 数据复权选项，默认不复权，支持pre-前复权，post-后复权，dypre-动态前复权，None-不复权
    :return: numpy.ndarray, 返回开始日期和结束日期之间的K线,包括端点
    """
    return Engine.instance().hqsdk_handler.get_kline_by_date_hqsdk(symbol, start_date, end_date, frequency, fq)
@api_method
def get_individual_entrust(stocks, data_count=50, start_pos=0, search_direction=1):
    return Engine.instance().hqsdk_handler.get_individual_entrust(stocks, data_count, start_pos, search_direction)
@api_method
def get_individual_transaction(stocks, data_count=50, start_pos=0, search_direction=1):
    return Engine.instance().hqsdk_handler.get_individual_transaction(stocks, data_count, start_pos, search_direction)
@api_method
def get_gear_price(sids):
    return Engine.instance().hqsdk_handler.get_gear_price(sids)

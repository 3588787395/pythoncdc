# Source Generated with Decompyle++ (Python version)
# File: data_source_func.pyc (Python 3.11)

from IQCommon.logger import system_log
from fly.data.quotation import load_bars_from_hundsun, get_price
def dsf_load_bars_from_hundsun(symbols, typet, start, end):
    """
    根据指定时间区间获取历史数据

    :param symbols: 合约对象
    :type symbols: : str

    :param typet: 单位时间长度，默认6，支持1分钟线（1）、日线(6)频率数据
    :type typet: : int

    :param start: 开始时间
    :type start: : str

    :param end: 结束时间
    :type end: : str

    :return: pandas.DataFrame
    """
    return load_bars_from_hundsun(symbols, typet, start, end)
def dsf_get_price(symbol, start_date, end_date, frequency, fields, fq):
    """
    根据指定时间区间获取价格数据

    :param symbol: 合约对象
    :type symbol: : str

    :param start_date: 开始时间
    :type start_date: : str

    :param end_date: 结束时间
    :type end_date: : str

    :param frequency: 单位时间长度，默认1d ，支持1分钟线（1m）、5分钟线(5m)、15分钟线(15m)、30分钟线(30m)、60分钟线(60m)、日线(1d)、周线(w)和月线(mo)频率数据
    :type frequency: : str

    :param fields: 指明数据结果集中所支持输出字段
    :type fields: : list

    :param fq: 数据复权选项，默认不复权，支持pre-前复权，post-后复权, None-不复权
    :type fq: : str | None

    :return: pandas.DataFrame
    """
    return get_price(symbol, start_date, end_date, frequency, fields, fq)

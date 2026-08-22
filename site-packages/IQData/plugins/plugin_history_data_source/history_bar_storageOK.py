# Source Generated with Decompyle++ (Python version)
# File: history_bar_storage.pyc (Python 3.11)

from IQData.utils.pycompatibility import lru_cache
from IQData.enumerate import Frequency
from IQData.fly_enum import NEW_FIELDS_TO_OLD_FIELDS_DICT
from IQData.plugins.plugin_history_data_source.data_source_func import dsf_load_bars_from_hundsun, dsf_get_price
class HistoryBarStorage(object):
    __doc__ = """ 
    K线存储类
    """
    def __init__(self, paramtuple):
        self.assettype = paramtuple[0]
        self._frequency = paramtuple[1]
        if self._frequency == Frequency.DAILY.value:
            self.typet = 6
            return None
        elif self._frequency == Frequency.MINUTE.value:
            self.typet = 1
            return None
    def get_bar(self, symbol, start_time, end_time, fields=None):
        """
        获取指定合约的全部周期数据
        :param symbol: 指定合约
        :type symbol: : str

        :param fields: 字段列表
        :type fields: : list

        :return value: 合约数据
        :type value: dataframe
        """
        data_dataframe = dsf_load_bars_from_hundsun(symbol, self.typet, start_time, end_time)[symbol]
        data_dataframe.rename(columns=NEW_FIELDS_TO_OLD_FIELDS_DICT, inplace=True)
        if fields is None:
            return data_dataframe
        else:
            return data_dataframe.ix[:, fields]
    def get_price_bar(self, symbol, start_date, end_date, frequency, fields, fq, skip_suspended):
        """
        获取历史数据，可指定时间段
        :param symbols: 代码或代码的列表
        :type symbols: : str | list

        :param start_date: 查询开始日期
        :type start_date: : str

        :param end_date: 查询结束日期，默认回测前一周期
        :type end_date: : str | None

        :param frequency: 单位时间长度，默认1d ，支持1分钟线（1m）、5分钟线(5m)、15分钟线(15m)、30分钟线(30m)、60分钟线(60m)、日线(1d)、周线(w)和月线(mo)频率数据
        :type frequency: : str

        :param field: 指明数据结果集中所支持输出字段
        :type field: : list
        filed值域范围：
        open              开盘价
        high              最高价
        low               最低价
        close             收盘价
        volume            交易量
        money             交易金额
        price             最新价
        high_limit        涨停价
        low_limit         跌停价
        is_open           停盘标识
        open_interest     持仓量（期货专用）
        basis_spread      期现差（股指期货专用）
        settlement        结算价（期货日线专用）
        prev_settlement   结算价（期货日线专用）

        :param fq: 数据复权选项，默认不复权，支持pre-前复权，post-后复权，dypre-动态前复权，None-不复权
        :type fq: : str | None

        #暂时不使用
        :param skip_suspended: 是否跳过不交易日期(包括停牌, 未上市或者退市后的日期)，默认False不跳过，True 跳过，False 不跳过
        :type skip_suspended: : bool

        :return: pandas.DataFrame | 空pandas.DataFrame
        """
        data = dsf_get_price(symbol, start_date, end_date, frequency, None, fq)
        data.rename(columns=NEW_FIELDS_TO_OLD_FIELDS_DICT, inplace=True)
        if fields is None:
            return data
        else:
            return data.ix[:, fields]

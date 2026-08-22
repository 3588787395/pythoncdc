# Source Generated with Decompyle++ (Python version)
# File: default_basic_data.pyc (Python 3.11)

from IQData.interface import AbstractBasicData
class DefaultBasicData(AbstractBasicData):
    __doc__ = """
    基础数据源类,AbstractBasicData
    """
    def get_trade_calendar(self, start_date=None, end_date=None):
        """
        按范围获取交易日历，返回开始日期与结束日期间的全部交易日期

        :param start_date: 开始日期，格式：20180101
        :type: int

        :param end_date: 结束日期，格式：20180101
        :return: int

        :return : 交易日期列表，如[20180101, 20180102, ...,]
        :type : list
        """
    def get_security_info(self, symbols):
        """
        获取标的基础信息

        :param symbols: 标的代码列表，['600570.XSHG', '000001.XSHE']
        :type: list | str

        :return: {'600570.XSHG': {'symbol': '600570.XSHG', 'name': '恒生电子', 'exchange': 'XSHG', ..., },
                  '000001.XSHE': {'symbol': '000001.XSHE', 'name': '平安银行', 'exchange': 'XSHE', ..., },
                   ...,
                 }
        :type: dict
        """
    def get_asset_info(self, symbols=None):
        return None
    def get_dividend(self, symbol, query_date=None):
        """
        根据给定标的代码，返回标的除权除息信息

        :param symbol: 标的代码，如'600570.XSHG'
        :type: str

        :param query_date: 查询日期，格式：20180101, query_date为None时，全部除权信息
        :type: int

        :return:
        :type: pandas.DataFrame
        """
    def get_index_stocks(self, symbol, query_date=None):
        """
        获取指定指数成分股

        :param symbol: 标的代码，如'600570.XSHG'
        :type: str

        :param query_date: 查询日期，格式：20180101, query_date为None时，全部除权信息
        :type: int

        :return: 标的代码列表
        :type: list | str
        """
    def is_st(self, symbol, query_date):
        return None
    def is_suspended(self, symbol, query_date):
        return None
    def get_industry_stocks(self, symbol, query_date=None):
        return None
    def get_block_stocks(self, symbol, query_date=None):
        return None
    def get_stock_blocks(self, symbol, query_date=None):
        return None
    def get_all_assets(self):
        return None
    def get_security_margin(self, symbol, query_date=None):
        return None

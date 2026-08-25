# Source Generated with Decompyle++ (Python version)
# File: interface.pyc (Python 3.11)

import abc
import six
class AbstractHTTPChannel(six.with_metaclass(abc.ABCMeta)):
    __doc__ = """
    HTTP请求抽象类
    """
    @abc.abstractmethod
    def request(self, **kwargs):
        raise NotImplementedError
class AbstractPlugin(six.with_metaclass(abc.ABCMeta)):
    __doc__ = """
    抽象插件接口类
    """
    @abc.abstractmethod
    def install(self, engine):
        """
        插件安装，用于插件管理器进行插件加载

        :param engine:
        :type: IQData.Engine

        :return:
        """
        raise NotImplementedError
    @abc.abstractmethod
    def uninstall(self, exit_code, exception=None):
        """
        插件卸载，用于插件管理器进行插件释放

        :param exit_code: 退出代码
        :type: str

        :param exception: 如果在策略执行过程中出现错误，此对象为相应的异常对象
        :type: BaseException

        :return:
        """
        raise NotImplementedError
    @abc.abstractmethod
    def interface(self):
        raise NotImplementedError
class AbstractBasicData(six.with_metaclass(abc.ABCMeta)):
    __doc__ = """
    基础数据接口类
    """
    @abc.abstractmethod
    def get_trading_calendar(self):
        """
        按范围获取交易日历，返回开始日期与结束日期间的全部交易日期
        start_date = None, end_date = None, 返回截止当前全部交易日
        start_date != None, end_date = None, 返回自start_date截止当前全部交易日
        start_date = None, end_date != None, 返回自默认交易日起点截止end_date全部交易日

        :param start_date: 开始日期，格式：20180101
        :type: int

        :param end_date: 结束日期，格式：20180101
        :return: int

        :return : 交易日期列表，如[20180101, 20180102, ...,]
        :type : list
        """
        raise NotImplementedError
    @abc.abstractmethod
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
        raise NotImplementedError
    @abc.abstractmethod
    def get_dividend(self, symbol, query_date=None):
        """
        根据给定标的代码，返回标的除权除息信息
        query_date = None 返回全部日期除权信息

        :param symbol: 标的代码，如'600570.XSHG'
        :type: str

        :param query_date: 查询日期，格式：20180101, query_date为None时，全部除权信息
        :type: int

        :return:
        :type: pandas.DataFrame
        """
        raise NotImplementedError
    @abc.abstractmethod
    def get_index_stocks(self, symbol, query_date=None):
        """
        获取指定指数成分股
        :param symbol: 指数代码，如'000300.XBHS'
        :type: str

        :param query_date: 查询日期，格式：20180101, query_date为None时，获取最新的指数数据
        :type: str

        :return: 股票代码列表
        :type: list
        """
        raise NotImplementedError
    @abc.abstractmethod
    def is_st(self, symbol, query_date):
        raise NotImplementedError
    @abc.abstractmethod
    def is_suspended(self, symbol, query_date):
        raise NotImplementedError
    @abc.abstractmethod
    def get_industry_stocks(self, symbol, query_date=None):
        """
        获取行业包含股票
        :param symbol: 行业代码，如'A01000.XBHS'
        :type: str

        :param query_date: 查询日期，格式：20180101, query_date为None时，返回最新内容
        :type: str

        :return: 股票代码列表
        :type: list
        """
        raise NotImplementedError
    @abc.abstractmethod
    def get_block_stocks(self, symbol, query_date=None):
        """
        获取板块所包含股票
        :param symbol: 板块代码，如'DY1172.XBHS'
        :type: str

        :param query_date: 查询日期，格式：20180101, query_date为None时，返回最新内容
        :type: str

        :return: 股票代码列表
        :type: list
        """
        raise NotImplementedError
    @abc.abstractmethod
    def get_stock_blocks(self, symbol, query_date=None):
        """
        获取股票所属板块
        :param symbol: 获取股票所属板块
        :type str

        :param query_date: query_date: 查询日期，格式：20180101, query_date为None时，返回最新内容
        :type str

        :return: {'DY': [['DY1172.XBHS', '浙江板块']],
                   'GN': [['003596.XBHS', '融资融券'],
                         ['003631.XBHS', '转融券标的'],
                         ['003637.XBHS', '互联网金融']]
                   }
        :type dict
        """
        raise NotImplementedError
    @abc.abstractmethod
    def get_security_margin(self, symbol, query_date=None):
        raise NotImplementedError
class AbstractRealQuoteData(six.with_metaclass(abc.ABCMeta)):
    __doc__ = """
    实时行情数据接口类
    """
    @abc.abstractmethod
    def subscribe(self, symbols, sub_type):
        """
        快照数据订阅
        :param symbols:
        :param sub_type:
        :return:
        """
        raise NotImplementedError
    @abc.abstractmethod
    def unsubscribe(self, symbols):
        """

        :param symbols:
        :return:
        """
        raise NotImplementedError
    @abc.abstractmethod
    def get_snapshot(self, symbol):
        raise NotImplementedError
    @abc.abstractmethod
    def get_kline_by_count(self, symbol, query_date, count, frequency, fields, fq, skip_suspended, include):
        """

        :param symbol:
        :param query_date:
        :param count:
        :param frequency:
        :param fields:
        :param fq:
        :param skip_suspended:
        :param include:
        :return:
        """
        raise NotImplementedError
    @abc.abstractmethod
    def get_kline_by_date(self, symbol, start_date, end_date, frequency, fq, skip_suspended, include):
        """

        :param symbol:
        :param start_date:
        :param end_date:
        :param frequency:
        :param fq:
        :param skip_suspended:
        :param include:
        :return:
        """
        raise NotImplementedError
    @abc.abstractmethod
    def get_transaction_data(self, symbols, data_count, start_pos, search_direction):
        raise NotImplementedError
    @abc.abstractmethod
    def get_order_data(self, symbols, data_count, start_pos, search_direction):
        raise NotImplementedError
    @abc.abstractmethod
    def get_real_minute_kline(self, symbol, include):
        raise NotImplementedError
class AbstractHistoryQuoteData(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_kline_by_count(self, symbol, count, query_date, frequency, fields, fq, skip_suspended, include):
        """

        :param symbol:
        :param query_date:
        :param count:
        :param frequency:
        :param fields:
        :param fq:
        :param skip_suspended:
        :param include:
        :return:
        """
        raise NotImplementedError
    @abc.abstractmethod
    def get_kline_by_date(self, symbol, start_date, end_date, frequency, fq, skip_suspended, include):
        """

        :param symbol:
        :param start_date:
        :param end_date:
        :param frequency:
        :param fq:
        :param skip_suspended:
        :param include:
        :return:
        """
        raise NotImplementedError
class AbstractFinanceData(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_fundamentals(self, *args, **kwargs):
        raise NotImplementedError
class AbstractFactorData(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_factor_info(self, *args, **kwargs):
        raise NotImplementedError
class AbstractDBData(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def insert(self, *args, **kwargs):
        raise NotImplementedError
    @abc.abstractmethod
    def update(self, *args, **kwargs):
        raise NotImplementedError
    @abc.abstractmethod
    def delete(self, *args, **kwargs):
        raise NotImplementedError
    @abc.abstractmethod
    def query(self, *args, **kwargs):
        raise NotImplementedError
    @abc.abstractmethod
    def merge(self, *args, **kwargs):
        raise NotImplementedError
class AbstractAuthority(six.with_metaclass(abc.ABCMeta)):
    __doc__ = """
    抽象权限接口类
    """
    @abc.abstractmethod
    def query(self, *args, **kwargs):
        raise NotImplementedError
    @abc.abstractmethod
    def check(self, *args, **kwargs):
        raise NotImplementedError
class AbstractDataRoute(six.with_metaclass(abc.ABCMeta)):
    __doc__ = """
    抽象路由接口类
    """
    @abc.abstractmethod
    def route(self, *args, **kwargs):
        raise NotImplementedError

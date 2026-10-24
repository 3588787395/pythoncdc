# Source Generated with Decompyle++ (Python version)
# File: get_stock_status.pyc (Python 3.11)

import datetime
import six
from IQCommon.data.api_data import is_delisting_sorting_stock_real
from IQCommon.util.wrapper_utils import api_call_counter, check_arg
from IQEngine import const
from IQEngine.core.engine import Engine
from IQEngine.core.execution_context import ExecutionContext
from IQEngine.plugins.plugin_fly_data.const import DATE_FORMAT
from IQEngine.utils import arg_checker, strategy_log
__all__ = ['get_stock_status']
@api_call_counter
@check_arg
@ExecutionContext.enforce_phase(const.ExecutionPhase.BEFORE_TRADING_START, const.ExecutionPhase.ON_HANDLE_DATA, const.ExecutionPhase.ON_HANDLE_TICK, const.ExecutionPhase.AFTER_TRADING_END, const.ExecutionPhase.SCHEDULED, const.ExecutionPhase.ON_TRADE_RSP, const.ExecutionPhase.ON_ORDER_RSP)
@arg_checker.apply_rules(arg_checker.verify_arg('stocks').is_instance((six.string_types, list)), arg_checker.verify_arg('query_type').is_in(('ST', 'HALT', 'DELISTING', 'DELISTING_SORTING')), arg_checker.verify_arg('query_type').is_instance((six.string_types, None.__class__)))
def get_stock_status(stocks, query_type='ST', query_date=None):
    """
    获取股票状态信息
    :param stocks: str or list: 股票
    :param query_type: str: 查询类型
    :param query_date: str: 查询时间，例如'20080808'
    :return: 股票状态dict
    """
    if isinstance(stocks, six.string_types):
        stocks = [stocks]
    if query_type not in ('ST', 'HALT', 'DELISTING', 'DELISTING_SORTING'):
        raise RuntimeError('get_stock_status传入的query_type参数{}错误，允许的输入限于ST、HALT、DELISTING、DELISTING_SORTING'.format(query_type))
    if query_date is None:
        query_date = Engine.instance().trading_dt.strftime(DATE_FORMAT)
    else:
        try:
            query_date = str(query_date)
            query_date = query_date.replace('-', '')
            datetime.datetime.strptime(query_date, DATE_FORMAT)
        except Exception:
            raise RuntimeError("get_stock_status传入的query_date参数{}错误，正确的参数格式如'20080808'".format(query_date))
    date_today = datetime.datetime.now().strftime(DATE_FORMAT)
    if query_date > date_today:
        strategy_log.warning('get_stock_status查询日期{}不可以大于当前日期{}'.format(query_date, date_today))
        return {}
    elif query_date == date_today:
        if Engine.instance().config.strategy.run_type == const.RunType.TRADING:
            if query_type == 'ST':
                return is_ST_stock_real(stocks)
            elif query_type == 'HALT':
                return is_halt_stock_real(stocks)
            elif query_type == 'DELISTING':
                return is_delisting_stock_real(stocks)
            elif query_type == 'DELISTING_SORTING':
                return is_delisting_sorting_stock_real(stocks)
            else:
                return {}
        else:
            strategy_log.warning('非交易模式下get_stock_status无法获取今日{}的股票状态'.format(date_today))
            return {}
    elif query_type == 'ST':
        return is_ST_stock_local(stocks, query_date)
    elif query_type == 'HALT':
        return is_halt_stock_local(stocks, query_date)
    elif query_type == 'DELISTING':
        return is_delisting_stock_local(stocks, query_date)
    else:
        return {}
def is_ST_stock_local(stocks, date):
    """
    从本地数据源获取数据，判断是否为ST股票
    :param stocks: list: 股票列表
    :param date: str: 例如'20080808'
    :return: 股票状态dict
     """
    return Engine.instance().data_proxy.is_st_stock(stocks, date)
def is_ST_stock_real(stocks):
    """
    从H5行情获取数据，判断是否为ST股票
    :param stocks: list: 股票列表
    :return: 股票状态dict
    """
    return Engine.instance().data_proxy.is_st_stock(stocks)
def is_halt_stock_local(stocks, date):
    """
    从本地数据源获取数据，判断股票是否退市
    :param stocks: list: 股票列表
    :param date: str: 例如'20080808'
    :return: 股票状态dict
    """
    return Engine.instance().data_proxy.is_suspended(stocks, date)
def is_halt_stock_real(stocks):
    """
    从H5行情获取数据，判断股票是否停牌
    :param stocks: list: 股票列表
    :return: 股票状态dict
    """
    return Engine.instance().data_proxy.is_suspended(stocks)
def is_delisting_stock_local(stocks, date):
    """
    从本地数据源获取数据，判断股票是否退市
    :param stocks: list: 股票列表
    :param date: str: 例如'20080808'
    :return: 股票状态dict
    """
    return Engine.instance().data_proxy.is_delisting(stocks, date)
def is_delisting_stock_real(stocks):
    """
    从H5行情获取数据，判断股票是否退市
    :param stocks: list: 股票列表
    :return: 股票状态dict
    """
    return Engine.instance().data_proxy.is_delisting(stocks)

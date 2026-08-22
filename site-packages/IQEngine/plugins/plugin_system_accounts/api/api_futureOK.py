# Source Generated with Decompyle++ (Python version)
# File: api_future.pyc (Python 3.11)

from IQEngine.api.api_base import decorate_api_exc, assure_asset
from IQEngine.core.execution_context import ExecutionContext
from IQEngine.core.engine import Engine
from IQEngine.const import ExecutionPhase, EntrustDirection, FuturesDirection, RunType
from IQEngine.api.api_base import order
from IQEngine.utils.arg_checker import apply_rules, verify_arg
from IQEngine.utils.exception import IQInvalidArgument
from IQEngine.utils.i18n import get_local_text as _
from IQEngine.account.order import MarketOrder
__all__ = []
def api_method(func):
    __all__.append(func.__name__)
    func = decorate_api_exc(func)
    return func
def future_order(symbol, amount, entrust_direction, futures_direction, style):
    asset = assure_asset(symbol)
    engine = Engine.instance()
    if engine.config.strategy.run_type != RunType.BACKTEST:
        if '88' in asset.symbol:
            raise IQInvalidArgument(_('Main Future contracts[88] are not supported in paper trading.'))
        elif '99' in asset.symbol:
            raise IQInvalidArgument(_('Index Future contracts[99] are not supported in paper trading.'))
    return order(asset, amount, entrust_direction, style, futures_direction)
@api_method
def buy_open(symbol, amount, style=MarketOrder()):
    """
    买入开仓
    :param symbol: 下单标的物
    :param amount: int 下单手数
    :param style: `OrderStyle` object
    :return: :class:`~Order` object | None
    """
    return future_order(symbol, amount, EntrustDirection.BUY, FuturesDirection.OPEN, style)
@api_method
def buy_close(symbol, amount, style=MarketOrder(), close_today=False):
    """
    平卖仓
    :param symbol: 下单标的物
    :param amount: int 下单手数
    :param style: `OrderStyle` object
    :param close_today: bool 是否平今仓
    :return: :class:`~Order` object | None
    """
    futures_direction = FuturesDirection.CLOSE_TODAY if close_today else FuturesDirection.CLOSE
    return future_order(symbol, amount, EntrustDirection.BUY, futures_direction, style)
@api_method
def sell_open(symbol, amount, style=MarketOrder()):
    """
    卖出开仓
    :param symbol: 下单标的物
    :param amount: int 下单手数
    :param style: `OrderStyle` object
    :return: :class:`~Order` object | None
    """
    return future_order(symbol, amount, EntrustDirection.SELL, FuturesDirection.OPEN, style)
@api_method
def sell_close(symbol, amount, style=MarketOrder(), close_today=False):
    """
    平买仓
    :param symbol: 下单标的物
    :param amount: int 下单手数
    :param style: `OrderStyle` object
    :param close_today: bool 是否平今仓
    :return: :class:`~Order` object | None
    """
    futures_direction = FuturesDirection.CLOSE_TODAY if close_today else FuturesDirection.CLOSE
    return future_order(symbol, amount, EntrustDirection.SELL, futures_direction, style)
@api_method
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED)
@apply_rules(verify_arg('underlying_symbol').is_instance(str))
def get_future_contracts(underlying_symbol):
    """
    获取某一期货品种在策略当前日期的可交易合约symbol列表。按照到期月份，下标从小到大排列，返回列表中第一个合约对应的就是该品种的近月合约。

    :param str underlying_symbol: 期货合约品种，例如沪深300股指期货为'IF'

    :return: list[`str`]

    :example:

    获取某一天的主力合约代码（策略当前日期是20161201）:

        ..  code-block:: python

            [In]
            logger.info(get_future_contracts('IF'))
            [Out]
            ['IF1612', 'IF1701', 'IF1703', 'IF1706']
    """
    engine = Engine.instance()
    return engine.data_proxy.get_future_contracts(underlying_symbol, engine.trading_dt)

# Source Generated with Decompyle++ (Python version)
# File: empty_api_trade.pyc (Python 3.11)

from IQEngine.const import ExecutionPhase
from IQEngine.core.execution_context import ExecutionContext
from IQEngine.utils import strategy_log
from IQCommon.util.wrapper_utils import check_arg
__all__ = ['set_commission', 'set_fixed_slippage', 'set_slippage', 'set_volume_ratio', 'set_limit_mode', 'set_yesterday_position', 'get_trades_file', 'convert_position_from_csv', 'get_margin_rate']
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_DATA)
def set_commission(commission_ratio=None, min_commission=None, type=None):
    strategy_log.warning('交易不支持set_commission函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_DATA)
def set_fixed_slippage(fixedslippage=None):
    strategy_log.warning('交易不支持set_fixed_slippage函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_DATA)
def set_slippage(slippage=None):
    strategy_log.warning('交易不支持set_slippage函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.ON_HANDLE_DATA)
def set_volume_ratio(volume_ratio=None):
    strategy_log.warning('交易不支持set_volume_ratio函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.ON_HANDLE_DATA)
def set_limit_mode(limit_mode=None):
    strategy_log.warning('交易不支持set_limit_mode函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_DATA)
def set_yesterday_position(position_list=None):
    strategy_log.warning('交易不支持set_yesterday_position函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_trades_file(save_path=None, identity=None):
    strategy_log.warning('交易不支持get_trades_file函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP)
def convert_position_from_csv(path=None):
    strategy_log.warning('交易不支持convert_position_from_csv函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.GLOBAL)
def get_margin_rate(transaction_code):
    strategy_log.warning('交易不支持get_margin_rate函数')

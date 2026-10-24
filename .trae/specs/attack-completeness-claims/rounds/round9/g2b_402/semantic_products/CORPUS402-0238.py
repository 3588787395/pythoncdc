# Source Generated with Decompyle++ (Python version)
# File: individual_api_backtest.pyc (Python 3.11)

from IQCommon import pandas as pd
import six
from IQEngine.utils import arg_checker, strategy_log
from IQEngine.api.api_base import get_universe, assure_assets
from IQEngine.const import ExecutionPhase
from IQEngine.core.execution_context import ExecutionContext
from IQCommon.util.wrapper_utils import check_arg
__all__ = ['get_individual_transaction', 'get_individual_entrust']
TRANSACTION_COLUMNS = ['business_time', 'hq_px', 'business_amount', 'order_no', 'business_direction', 'trans_kind']
ENTRUST_COLUMNS = ['business_time', 'hq_px', 'business_amount', 'trade_index', 'business_direction']
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP)
@arg_checker.apply_rules(arg_checker.verify_arg('stocks').is_instance((list, six.string_types, None.__class__)), arg_checker.verify_arg('data_count').is_instance(int), arg_checker.verify_arg('start_pos').is_instance(int), arg_checker.verify_arg('search_direction').is_instance(int))
def get_individual_transaction(stocks=None, data_count=50, start_pos=0, search_direction=1, is_dict=False):
    strategy_log.warning('回测不支持get_individual_transaction函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP)
@arg_checker.apply_rules(arg_checker.verify_arg('stocks').is_instance((list, six.string_types, None.__class__)), arg_checker.verify_arg('data_count').is_instance(int), arg_checker.verify_arg('start_pos').is_instance(int), arg_checker.verify_arg('search_direction').is_instance(int))
def get_individual_entrust(stocks=None, data_count=50, start_pos=0, search_direction=1, is_dict=False):
    strategy_log.warning('回测不支持get_individual_entrust函数')

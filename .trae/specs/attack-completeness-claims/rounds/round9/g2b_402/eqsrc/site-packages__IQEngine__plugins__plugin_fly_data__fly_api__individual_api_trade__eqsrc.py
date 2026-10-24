# Source Generated with Decompyle++ (Python version)
# File: individual_api_trade.pyc (Python 3.11)

import six
from IQCommon.util.wrapper_utils import api_call_counter, check_arg
from IQEngine.api.api_base import assure_assets, engine_instance, get_universe
from IQEngine.const import ExecutionPhase
from IQEngine.core.execution_context import ExecutionContext
from IQEngine.utils import arg_checker
__all__ = ['get_individual_transaction', 'get_individual_entrust']
@api_call_counter
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP)
@arg_checker.apply_rules(arg_checker.verify_arg('stocks').is_instance((list, six.string_types, None.__class__)), arg_checker.verify_arg('data_count').is_instance(int), arg_checker.verify_arg('start_pos').is_instance(int), arg_checker.verify_arg('search_direction').is_instance(int))
def get_individual_transaction(stocks=None, data_count=50, start_pos=0, search_direction=1, is_dict=False):
    return _get_individual_transaction(stocks, data_count, start_pos, search_direction, is_dict=is_dict)
def _get_individual_transaction(stocks=None, data_count=50, start_pos=0, search_direction=1, is_dict=False):
    if stocks is None:
        stocks = get_universe()
    assure_assets(stocks, need_asset_result=False)
    if is_dict:
        individual_data_in_dict = '1'
    else:
        individual_data_in_dict = '0'
    return engine_instance().data_proxy.get_transaction_data(stocks, data_count, start_pos, search_direction, individual_data_in_dict)
@api_call_counter
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP)
@arg_checker.apply_rules(arg_checker.verify_arg('stocks').is_instance((list, six.string_types, None.__class__)), arg_checker.verify_arg('data_count').is_instance(int), arg_checker.verify_arg('start_pos').is_instance(int), arg_checker.verify_arg('search_direction').is_instance(int))
def get_individual_entrust(stocks=None, data_count=50, start_pos=0, search_direction=1, is_dict=False):
    if stocks is None:
        stocks = get_universe()
    assure_assets(stocks, need_asset_result=False)
    if is_dict:
        individual_data_in_dict = '1'
    else:
        individual_data_in_dict = '0'
    return engine_instance().data_proxy.get_order_data(stocks, data_count, start_pos, search_direction, individual_data_in_dict)

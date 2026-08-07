# Source Generated with Decompyle++ (Python version)
# File: real_api_trade.pyc (Python 3.11)

import six
from IQCommon.util.wrapper_utils import api_call_counter, check_arg
from IQEngine.api.api_base import assure_assets, engine_instance, get_universe
from IQEngine.const import ExecutionPhase
from IQEngine.core.execution_context import ExecutionContext
from IQEngine.plugins.plugin_fly_data.const import SymbolDict
from IQEngine.utils import arg_checker
__all__ = ['get_gear_price', 'get_snapshot']
@api_call_counter
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP)
@arg_checker.apply_rules(arg_checker.verify_arg('sids').is_instance((list, six.string_types, None.__class__)))
def get_gear_price(sids=None):
    if sids is None:
        sids = get_universe()
    symbols = assure_assets(sids, need_asset_result=False)
    return SymbolDict(engine_instance().data_proxy.get_gear_price(symbols))
@api_call_counter
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.GLOBAL, ExecutionPhase.ON_STRATEGY_SIGNAL_RSP)
@arg_checker.apply_rules(arg_checker.verify_arg('security').is_instance((six.string_types, list)))
def get_snapshot(security):
    if isinstance(security, six.string_types):
        security = [security]
    assure_assets(security)
    return engine_instance().data_proxy.get_snapshot(security)

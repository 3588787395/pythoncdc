# Source Generated with Decompyle++ (Python version)
# File: real_api_backtest.pyc (Python 3.11)

import numpy as np
import six
from IQEngine.api.api_base import get_universe, assure_assets, engine_instance
from IQEngine.const import ExecutionPhase
from IQEngine.core.execution_context import ExecutionContext
from IQEngine.plugins.plugin_fly_data.const import SymbolDict
from IQEngine.utils import arg_checker
from IQCommon.logger import strategy_log
from IQCommon.util.wrapper_utils import check_arg
__all__ = ['get_gear_price']
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP)
@arg_checker.apply_rules(arg_checker.verify_arg('sids').is_instance((list, six.string_types, None.__class__)))
def get_gear_price(sids=None):
    strategy_log.warning('回测不支持get_gear_price函数')

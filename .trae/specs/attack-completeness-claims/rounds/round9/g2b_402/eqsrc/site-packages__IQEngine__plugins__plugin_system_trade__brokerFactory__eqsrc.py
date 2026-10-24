# Source Generated with Decompyle++ (Python version)
# File: brokerFactory.pyc (Python 3.11)

from IQEngine.plugins.plugin_system_trade.ptrade_broker import PtradeBroker
from IQEngine.plugins.plugin_system_trade.ptrade_future_broker import PtradeFutureBroker
from IQEngine.plugins.plugin_system_trade.ptrade_option_broker import PtradeOptionBroker
from IQEngine.plugins.plugin_system_trade.ptrade_hks_broker import PtradeHksBroker
BROKER_TYPE_ENUM = {'PTRADE_INTERFACE': 'PtradeBroker', 'PTRADE_FUTURE_INTERFACE': 'PtradeFutureBroker', 'PTRADE_OPTION_INTERFACE': 'PtradeOptionBroker', 'PTRADE_HKS_INTERFACE': 'PtradeHksBroker'}
class BrokerFactory(object):
    @staticmethod
    def create_broker(account_type, engine):
        if account_type in BROKER_TYPE_ENUM:
            return eval(BROKER_TYPE_ENUM[account_type])(engine)
        else:
            raise KeyError

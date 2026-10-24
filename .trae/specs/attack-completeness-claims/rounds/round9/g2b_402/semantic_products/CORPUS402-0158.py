# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQData.interface import AbstractPlugin
from .api_realquote import get_tick, get_subscribe_market_codes, get_tick_direction, get_underlying_code
from IQData.plugins.plugin_system_realquote.api_realquote import get_snapshot, get_order_data, get_real_daily_kline, get_real_minute_kline, get_transaction_data, get_bar, get_gear_price, check_limit
class PluginRealQuote(AbstractPlugin):
    def install(self, engine):
        """
        """
        from .real_quote import RealQuoteData
        engine.set_real_quote_handler(RealQuoteData(engine))
    def uninstall(self, exit_code, exception=None):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginRealQuote()

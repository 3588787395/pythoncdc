# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQData.interface import AbstractPlugin
from IQData.plugins.plugin_system_local_finance.finance_data_source import FinanceDataSource
from IQData.plugins.plugin_system_local_finance.api import get_fundamentals
class PluginFinanceDataSource(AbstractPlugin):
    def install(self, engine):
        engine.set_finance_handler(FinanceDataSource(engine))
    def uninstall(self, code, exception=None):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginFinanceDataSource()

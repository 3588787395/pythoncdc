# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQData.interface import AbstractPlugin
from .history_data_source import HistoryDataSource
class PluginHistoryDataSource(AbstractPlugin):
    def install(self, engine):
        """
        """
        engine.set_data_source(HistoryDataSource())
    def uninstall(self, code, exception=None):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginHistoryDataSource()

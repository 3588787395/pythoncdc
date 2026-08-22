# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQData.interface import AbstractPlugin
from IQData.plugins.plugin_system_fly_basicdata.basic_data_source import BasicDataSource
from IQData.plugins.plugin_system_fly_basicdata import api
class PluginBasicDataSource(AbstractPlugin):
    def install(self, engine):
        """
        """
        engine.set_basic_data_handler(BasicDataSource(engine.config.data_access.basic_data.data_path))
    def uninstall(self, code, exception=None):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginBasicDataSource()

# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQData.interface import AbstractPlugin
from IQData.api.api_base import register_api
from IQData.plugins.plugin_system_db_tools.api_db import get_api
class PluginSystemDatabase(AbstractPlugin):
    def install(self, engine):
        config = engine.config.plugins.plugin_system_db_tools
        for export_name, func in get_api(config).items():
            register_api(export_name, func)
    def uninstall(self, code, exception=None):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginSystemDatabase()

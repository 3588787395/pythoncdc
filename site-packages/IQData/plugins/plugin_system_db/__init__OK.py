# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQData.interface import AbstractPlugin
from IQData.plugins.plugin_system_db.api_db import func_list
from IQData.api.api_base import api_method
from IQData.plugins.plugin_system_db import api_db
class PluginSystemDatabase(AbstractPlugin):
    def install(self, engine):
        for export_name in func_list:
            api_method(getattr(api_db, export_name))
    def uninstall(self, code, exception=None):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginSystemDatabase()

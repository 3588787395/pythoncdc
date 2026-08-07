# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQData.interface import AbstractPlugin
from IQData.plugins.plugin_system_client_db.client_db import func_list
from IQData.api.api_base import api_method
from IQData.plugins.plugin_system_client_db import client_db
from IQData.plugins.plugin_system_client_db.client_db import config
class PluginClientDataBase(AbstractPlugin):
    def install(self, engine):
        plugin_config = engine.config.plugins.plugin_system_client_db
        config.update(plugin_config)
        for export_name in func_list:
            api_method(getattr(client_db, export_name))
    def uninstall(self):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginClientDataBase()

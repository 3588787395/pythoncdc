# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQData.interface import AbstractPlugin
from .gtn_request import GTNRequest
from .api import gtn_send_by_get, gtn_send_by_post
class PluginGTNRequest(AbstractPlugin):
    def install(self, engine):
        engine.set_request_handler(GTNRequest(engine))
    def uninstall(self, code, exception=None):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginGTNRequest()

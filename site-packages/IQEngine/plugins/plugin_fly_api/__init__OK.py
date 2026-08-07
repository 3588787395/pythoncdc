# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQEngine.api.api_extra import register_api
from IQEngine.const import RunType
from IQEngine.interface import AbstractPlugin
from IQEngine.plugins.plugin_fly_api import empty_api_backtest, empty_api_trade, base_api
class PluginAPI(AbstractPlugin):
    _engine = None
    def setup(self, _engine):
        self._engine = _engine
        self.resist_api()
    def resist_api(self):
        api_dict = {}
        extra_api_module = []
        if self._engine.config.strategy.run_type == RunType.BACKTEST:
            extra_api_module.append(empty_api_backtest)
            extra_api_module.append(base_api)
        elif self._engine.config.strategy.run_type == RunType.TRADING:
            extra_api_module.append(empty_api_trade)
            extra_api_module.append(base_api)
        for module in extra_api_module:
            for func_name in module.__all__:
                func = getattr(module, func_name)
                api_dict[func_name] = func
        for func_name, func in api_dict.items():
            register_api(func_name, func)
    def cleanup(self, code, exception=None):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginAPI()

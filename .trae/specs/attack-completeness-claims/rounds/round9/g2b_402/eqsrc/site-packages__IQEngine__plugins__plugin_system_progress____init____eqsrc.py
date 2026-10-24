# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

__config__ = {'show': False}
from IQEngine.interface import AbstractPlugin
from IQEngine.plugins.plugin_system_progress.system_progress import SystemProgress
from IQEngine.const import RunType
class PluginProgress(AbstractPlugin):
    def setup(self, engine):
        """
        """
        if engine.config.strategy.run_type.value != RunType.BACKTEST.value:
            return None
        else:
            process = SystemProgress()
            process.start(engine)
    def cleanup(self, code, exception=None):
        return None
    def interface(self):
        return self
def load_plugin():
    return PluginProgress()

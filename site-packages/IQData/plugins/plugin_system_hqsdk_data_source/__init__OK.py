# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

from IQData.interface import AbstractPlugin
from IQData.plugins.plugin_system_hqsdk_data_source.hqsdk_data_source import HqsdkDataSource
from IQData.plugins.plugin_system_hqsdk_data_source import hqsdk_data_source_api
class PluginSystemHqsdkDataSource(AbstractPlugin):
    def install(self, engine):
        """
        插件安装，用于插件管理器进行插件加载

        :param engine:
        :type: IQData.Engine

        :return:
        """
        engine.set_hqsdk_handler(HqsdkDataSource(engine.config.plugins.plugin_system_hqsdk_data_source.level_type))
    def uninstall(self, exit_code, exception=None):
        """
        插件卸载，用于插件管理器进行插件释放

        :param exit_code: 退出代码
        :type: str

        :param exception: 如果在策略执行过程中出现错误，此对象为相应的异常对象
        :type: BaseException

        :return:
        """
    def interface(self):
        return self
def load_plugin():
    return PluginSystemHqsdkDataSource()

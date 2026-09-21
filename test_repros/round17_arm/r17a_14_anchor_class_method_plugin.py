# -*- coding: utf-8 -*-
"""R17-A 14 anchor class method (plugin_manager 同构形状).

module → class → method → for → if/elif/else，最后一个 else 臂 =
**嵌套 if/elif/else 链 + 尾随语句**，条件全是 BoolOp 短路链。
这就是 IQData/manager/plugin_manager.PluginManager.set_engine（9/10→10/10）
与 IQEngine/core/plugin_manager.PluginManager.set_engine（8/9→9/9）的最小复刻。

角色：锚点（anchor），真实缺陷源。
"""


class PluginManager(object):

    def __init__(self):
        self.plugin_dict = {}

    def set_engine(self, plugin_list, log, importer):
        result = {}
        for idx, cfg in plugin_list:
            if hasattr(cfg, 'load') and callable(cfg.load):
                plugin_module = {}
                plugin = cfg.load()
            elif hasattr(cfg, 'install') and callable(cfg.setup):
                plugin_module = {}
                plugin = cfg
            else:
                if hasattr(cfg, 'lib'):
                    lib_name = cfg.lib
                elif idx.startswith('plugin_system'):
                    lib_name = 'pkg.{}'.format(idx)
                else:
                    lib_name = idx
                log.debug('loading plugin {}'.format(lib_name))
                plugin_module = importer(lib_name)
            result[idx] = dict(plugin=plugin, module=plugin_module)
        self.plugin_dict = result
        return result

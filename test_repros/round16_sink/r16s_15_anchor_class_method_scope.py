# -*- coding: utf-8 -*-
"""R16-S 15 anchor class method scope
把 r16s_01 的形状放进 **模块级类的实例方法**（与真实 plugin_manager 完全同构的
作用域层级：module → class → method → for → if/elif/else → 嵌套 if/elif/else + 尾随）。

真实目标：确认嵌套层级/作用域不影响触发（判据④只看循环，不看类/函数）。
"""


class PluginManager(object):

    def __init__(self):
        self.plugin_list = []
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
                if plugin_module is None:
                    return None
                plugin = plugin_module.load_plugin()
            result[idx] = dict(plugin=plugin, module=plugin_module)
        self.plugin_dict = result
        return result

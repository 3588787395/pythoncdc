# -*- coding: utf-8 -*-
"""R16-S 01 anchor plugin_manager shape
IQData/manager.plugin_manager.PluginManager.set_engine 的最小复刻：
外层 if/elif/else，**else 臂 = 嵌套 if/elif/else 链 + 尾随语句**，整段在 for 循环体内。

真实目标：R13c sink-collapse 假设的替代真因 ——
region_analyzer.py:18746-18748 的 D2 否决被「在循环内」这条豁免（判据④）屏蔽，
于是 else 臂被展平成 elif 链，尾随语句外提为链的兄弟语句，
then/elif 臂末尾的 JUMP_FORWARD 终点从外层归并点漂移到尾随语句入口。
"""


def set_engine(plugin_list, log, importer):
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
        cfg_dict = dict(plugin=plugin)
        plugin_list[idx] = cfg_dict
    return plugin_list

# -*- coding: utf-8 -*-
"""R16-S 02 anchor module scope
01 的同一形状放在 **模块级 for 循环**（不包在函数里），验证缺陷与「函数/类作用域」
无关，只与「是否在循环内」有关。

真实目标：同 r16s_01。
"""

RESULT = {}


def _handle(items, log, importer):
    return importer(items)


for idx, cfg in [('a', {}), ('b', {})]:
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
        RESULT['log'] = 'loading plugin {}'.format(lib_name)
        plugin_module = _handle(lib_name, RESULT)
        if plugin_module is None:
            plugin = None
        else:
            plugin = plugin_module
    RESULT[idx] = plugin

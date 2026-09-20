# -*- coding: utf-8 -*-
"""R13-A 复现：循环体内 if 分支末尾的 `return` 被判成 `break`。

对应真实目标：
  IQData/manager/plugin_manager.pyc      <module>.PluginManager.set_engine   [seq_len]
  IQEngine/core/plugin_manager.pyc       <module>.PluginManager.set_engine   [seq_len]
  IQEngine/plugins/plugin_system_control/__init__.pyc  <module>.AccountPlugin._terminate

原始字节码（_terminate，实测 dis）：
  #33 142 LOAD_CONST None ; #34 144 RETURN_VALUE     <- 原文是 `return`
反编译产物重编译后：
  #33 142 JUMP_FORWARD -> 146                        <- 变成 `break`，落到 sys.exit(0)
两者 seq_len 差 1，且语义不同（break 之后还会执行 sys.exit(0)）。

【2026-09-20 复核】对真实 pyc 直接跑严格尺子（site-packages 下的原文件）：
  plugin_system_control/__init__.pyc  AccountPlugin._terminate 43 -> 43 **已翻正**
  IQData/manager/plugin_manager.pyc   PluginManager.set_engine 184 -> 184，
  IQEngine/core/plugin_manager.pyc    PluginManager.set_engine 194 -> 194，
      但两者改成 **[target_diff] #60 JUMP 终点 orig=('utils'/'time',LOAD_GLOBAL)
      decomp=('system_log',LOAD_GLOBAL)** —— 即 seq_len 型 return→break 已被并发修复
      消掉，剩下一条**落点错位**型缺陷（新类 R13-N，见 ANALYSIS.md）。
  本复现（重建形状）在 2026-09-20 20:2x 实测 MISMATCH（_terminate 31 -> 30），
  21:0x 复测同一形状 **MATCH**（并发 R13-A3 修复落地）→ 本文件 EXPECT 改为
  SENTINEL（回归哨兵）：若再次出现 MISMATCH，说明 return→break 修复被回退。
"""


class Instance(object):
    def terminate(self):
        pass


def _terminate(current_process, current_thread, sys):
    for func in (current_process, current_thread):
        instance = func()
        if isinstance(instance, Instance):
            instance.terminate()
            return
    sys.exit(0)


def set_engine(self, engine, utils, system_log):
    self._engine = engine
    for idx, name in enumerate(self._plugin_list):
        lib_name = name
        system_log.debug(lib_name)
        plugin_module = utils.import_plugin(lib_name)
        if plugin_module is None:
            del (self._plugin_list[idx])
            return
        plugin = plugin_module.load_plugin()
        self._plugin_dict[name] = plugin
    return None

# -*- coding: utf-8 -*-
"""R13-E 复现：`if X is not None:` 里是一条 if/elif 链，链的 **公共后继**（elif 为假、
以及 elif 为真但内层 if 全为假时）是 if 块末尾的一句 return。反编译器把这句 return
塞进了 `else:`，并额外补一个 `else: return None`。

对应真实目标（用 co_lines() 反查出的原始源码结构，行号为原 .py 行号）：
  IQEngine/data/data_proxy.pyc  <module>.DataProxy.get_bar  [seq_len] orig=86 decomp=90

    48  if bar is not None:                     POP_JUMP_FORWARD_IF_NONE -> 574
    49      if frequency == 'tick':             POP_JUMP_IF_FALSE -> 162
    50          return self.TickBar(...)
    52      elif ...run_type == TRADING:        POP_JUMP_IF_FALSE -> 526
    53-56         now_time/now_dt/bar = ...
    57          if bar is not None:             POP_JUMP_IF_NONE -> 526
    58              return self.BarData(..., now_dt)
    60      return self.BarData(self, asset, bar, dt)     <-- 526，三条边的公共后继
    48  (574) LOAD_CONST None / RETURN_VALUE               <-- 隐式函数尾

  实测 dis 对比（尾部）：
    ORIG   #67 476 POP_JUMP_FORWARD_IF_NONE '->526' | #76 526 LOAD_FAST 'self' (BarData ... dt)
    DECOMP #67 476 POP_JUMP_FORWARD_IF_NONE '->530' | #76 526 LOAD_CONST None; #77 RETURN_VALUE
                                                        | #78 530 LOAD_CONST None; #79 RETURN_VALUE
    —— POP_JUMP 的落点从 `LOAD_FAST self` 变成了 `LOAD_CONST None`（多余的两份 return None）。
"""


def get_bar(self, asset_or_symbol, dt, frequency, datetime, engine_instance, const):
    asset = self.get_assets(asset_or_symbol)
    bar = self._data_pager.get_bar(asset, dt, frequency)
    if bar is not None:
        if frequency == 'tick':
            return self.TickBar(asset, bar, dt)
        elif engine_instance().config.strategy.run_type == const.RunType.TRADING:
            now_time = datetime.datetime.now()
            now_dt = now_time.replace(second=0)
            if now_time >= dt + datetime.timedelta(minutes=1):
                bar = self._data_pager.get_bar(asset, now_dt, frequency)
                if bar is not None:
                    return self.BarData(self, asset, bar, now_dt)
        return self.BarData(self, asset, bar, dt)

# -*- coding: utf-8 -*-
"""R13-J 复现：for 体开头的赋值 + 体内 `while True:` 的 break 出口 —— 反编译器把
开头的赋值整批搬到了 for 体的**最后**，并丢掉了 break 之前的一条日志语句。

对应真实目标：
  IQEngine/plugins/plugin_system_event_source/default_event_source.pyc
      <module>.DefaultEventSource.events  [seq_len] orig=512 decomp=488

实测 dis：
  ORIG   #351 2378 STORE_FAST 'day' | #352-#366  date=day.to_pydatetime(); last_tick=None;
               last_dt=None; dt_before_day_trading=date.replace(8,30)
         #373 LOAD_FAST 'symbol_list' ; #374 POP_JUMP_FORWARD_IF_TRUE '->2600'
         #375-#379 strategy_log.error('TICK策略需要订阅股票池') ; #380 JUMP_FORWARD '->3214'
         #483 3214 LOAD_FAST 'date' ; ... dt=date.replace(15,30) ; yield AFTER_TRADING_END
         #500 3322 JUMP_BACKWARD '->2374'      <- for 回边
  DECOMP #351 2378 STORE_FAST 'day' | #352 2382 LOAD_FAST 'self' ; LOAD_METHOD '_get_universe'
               （开头 4 条赋值不见了）
         #359 2460 POP_JUMP_FORWARD_IF_TRUE '->2466' ; #360 2464 JUMP_FORWARD '->3076'
               （strategy_log.error(...) 5 条被丢）
         #461-#475 3076.. date/last_tick/last_dt/dt_before_day_trading 赋值
         #476 3172 JUMP_BACKWARD '->2374'      <- 赋值被搬到了回边之前

【2026-09-20 测试工程师复核：未复现】
  * 真实目标仍在缺陷中（对 site-packages 的 pyc 直接跑严格尺子：
    <module>.DefaultEventSource.events seq_len 512 -> 488，delta=-24）。
  * 但本文件的**正确源形状**重建后反编译 100% 一致（MATCH），说明上面记录的
    指令错位不能由这个骨架触发——它依赖 events() 里更真实的上下文
    （多层 try/except + 生成器 yield 混合，本复现把它简化掉了）。
  * 另测 4 个变体形状（生成器 events 全形、while True+break 无 yield、
    for 前导赋值 + while + break、生成器前导 + 嵌套 for + yield）全部 MATCH。
  * 结论：**未复现**，不作为修复依据；EXPECT 标为 UNCONFIRMED（见 run_all.py）。
    修复该文件时请直接用 `D:/Temp/r13_real.py` 对真实 pyc 取证。
"""


def events(self, trading_dates, to_timestamp, datetime, Event, BEFORE, HANDLE, AFTER,
           strategy_log):
    self._trading_dates = trading_dates
    for day in self._trading_dates:
        date = day.to_pydatetime()
        last_tick = None
        last_dt = None
        dt_before_day_trading = date.replace(hour=8, minute=30)
        while True:
            symbol_list = self._get_universe().get()
            if not symbol_list:
                strategy_log.error('TICK need universe')
                break
            asset_list = self._engine.data_proxy.get_assets(symbol_list)
            for asset, tick_data in self._data_proxy.get_merge_ticks(asset_list, date, last_dt):
                calendar_dt = to_timestamp(int(tick_data['datetime'])).to_pydatetime()
                if calendar_dt < dt_before_day_trading:
                    trading_dt = calendar_dt.replace(year=date.year)
                else:
                    trading_dt = calendar_dt
                if last_tick is None:
                    last_tick = tick_data
                    yield Event(BEFORE, calendar_dt=calendar_dt, trading_dt=trading_dt)
                yield Event(HANDLE, calendar_dt=calendar_dt, trading_dt=trading_dt)
                if self._universe_changed:
                    self._universe_changed = False
                    last_dt = calendar_dt
                    break
            break
        dt = date.replace(hour=15, minute=30)
        yield Event(AFTER, calendar_dt=dt, trading_dt=dt)

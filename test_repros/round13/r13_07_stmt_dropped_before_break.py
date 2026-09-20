# -*- coding: utf-8 -*-
"""R13-F 复现：嵌套循环里 `if cond: <表达式语句>; break` 中的表达式语句被整块丢弃。

对应真实目标：
  IQEngine/plugins/plugin_fly_data/__init__.pyc
      <module>.ApiMethodPlugin._on_before_trading_start_trading_thread  [seq_len] orig=66 decomp=62

实测 dis：
  ORIG   #42 284 POP_JUMP_FORWARD_IF_FALSE '->328'
               #43 286 LOAD_FAST 'order' ; #44 288 LOAD_METHOD 'commit' ;
               #45 314 CALL 0 ; #46 324 POP_TOP ; #47 326 JUMP_FORWARD '->404'
               #48 328 LOAD_GLOBAL 'time' ... #58 402 JUMP_BACKWARD '->132'
  DECOMP #42 284 POP_JUMP_FORWARD_IF_FALSE '->288'
               #43 286 JUMP_FORWARD '->364'          <- order.commit() 四条指令整体消失
               #44 288 LOAD_GLOBAL 'time' ...
对应 __init__OK.py:118-119 只剩 `if now >= order.order_time: break`。
"""


def start_trading_thread(self, datetime, time, minute_to_secs):
    self._engine.set_engine(self._engine)
    while self._will_be_ordered:
        order = self._will_be_ordered.pop(0)
        while True:
            now = datetime.datetime.now()
            order_time = order.order_time
            now = (now.hour * 60 + now.minute) * 60 + now.second
            if now >= order.order_time:
                order.commit()
                break
            time.sleep(min(order_time - now, 30))


def handle_order(self, datetime, minute_to_secs):
    while self._will_be_ordered:
        order = self._will_be_ordered[0]
        now = self._engine.calendar_dt
        order_time = order.order_time
        now = minute_to_secs(now)
        if now >= order.order_time:
            order.commit()
            self._will_be_ordered.pop(0)
        else:
            break

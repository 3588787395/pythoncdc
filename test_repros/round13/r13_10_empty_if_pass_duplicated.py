# -*- coding: utf-8 -*-
"""R13-I 复现：链式 if 的 else 侧为空时，生成 `if cond: pass` —— 把已经求过值的
判定条件在 join 块里又整份复制一遍（多出 JUMP_FORWARD + 两条 POP_JUMP 链）。

对应真实目标：
  IQEngine/core/executor.pyc  <module>.Executor.check_before_trading  [seq_len] orig=243 decomp=254

实测 dis：
  ORIG   #50 328 POP_TOP ; #51 330 LOAD_GLOBAL 'AccountType' ...
  DECOMP #50 328 POP_TOP ; #51 330 JUMP_FORWARD '->394'
               #52 332 LOAD_FAST self._engine.config.other.is_hold
               #57 374 POP_JUMP_FORWARD_IF_FALSE '->378' ; #58 376 JUMP_FORWARD '->394'
               #59 378 LOAD_FAST self._last_before_trading
               #61 390 POP_JUMP_FORWARD_IF_FALSE '->394'
         #62 394 LOAD_GLOBAL 'AccountType' ...
         —— 多出 11 条：把 240-328 的两个 if 判定又抄了一遍，body 全是 pass。
对应 executorOK.py:109-113 `else: if ...: pass / elif ...: pass`。
"""


class Cfg(object):
    def __init__(self):
        self.is_hold = False


class Engine(object):
    def __init__(self):
        self.config = Cfg()


def check_before_trading(self, event, AccountType, datetime):
    self._engine = Engine()
    if self._last_before_trading == event.trading_dt.date():
        return False
    elif isinstance(self._last_before_trading, datetime.datetime):
        if event.trading_dt.hour <= 18:
            return False
        elif self._last_before_trading.day == event.trading_dt.day:
            return False
        elif self._engine.config.is_hold:
            return False
        elif self._last_before_trading:
            self.publish_settlement()
    if AccountType.FUTURE.value in self._engine.config.is_hold:
        if event.trading_dt.hour > 18:
            self._last_before_trading = event.trading_dt
        else:
            self._last_before_trading = event.trading_dt.date()
    return None

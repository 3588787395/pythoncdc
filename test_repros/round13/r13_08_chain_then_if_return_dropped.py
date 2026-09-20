# -*- coding: utf-8 -*-
"""R13-G 复现：紧跟在 if/raise 链之后的 `if cond: return X` 丢掉条件，
body 被无条件发射，后续代码变成死代码（编译器直接不生成）。

对应真实目标：
  IQEngine/plugins/plugin_system_persist/__init__.pyc
      <module>.ObjectPersistancePlugin.can_resume_strategy  [seq_len] orig=89 decomp=57

实测 dis：
  ORIG   #54 372 RAISE_VARARGS 1
               #55 374 LOAD_FAST 'persist_meta'; ... #62 412 COMPARE_OP '==';
               #63 418 POP_JUMP_FORWARD_IF_FALSE '->424'
               #64 420 LOAD_CONST False ; #65 422 RETURN_VALUE
               #66 424 LOAD_FAST 'data_proxy' ... #87 548 LOAD_CONST True ; #88 550 RETURN_VALUE
  DECOMP #54 372 RAISE_VARARGS 1
               #55 374 LOAD_CONST False ; #56 376 RETURN_VALUE   <- 条件测试整个消失
         （374 之后 CPython 视为死代码，#66-#88 共 32 条指令根本没被编译出来）
对应 __init__OK.py:77-79：`else: return False` 后面直接跟着本该在 if 判断之后的语句。
"""


def can_resume_strategy(self, persist_meta, data_proxy, convert_date_to_date_int, RuntimeError):
    if persist_meta['start_date'] != self._meta['start_date']:
        raise RuntimeError('start_date mismatch')
    if persist_meta['last_calendar_dt'] is None:
        return False
    if persist_meta['last_calendar_dt'] > self._meta['end_date']:
        raise RuntimeError('end_date mismatch')
    if persist_meta['last_calendar_dt'] == self._meta['end_date']:
        return False
    next_start_date = data_proxy.get_next_trading_date(persist_meta['last_calendar_dt'], 1)
    next_start_date = convert_date_to_date_int(next_start_date)
    if next_start_date > self._meta['end_date']:
        return False
    return True

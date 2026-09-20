# -*- coding: utf-8 -*-
"""R13-D 复现：dict 字面量里两个推导式值被塌成一层嵌套 list 推导式。

对应真实目标：
  IQEngine/plugins/plugin_system_simulation/broker.pyc  <module>.SimulationBroker.save  [seq_len] orig=22 decomp=15
  IQEngine/plugins/plugin_system_simulation/live.pyc    <module>.DefaultLiveBroker.save [seq_len] orig=16 decomp=12

live.pyc 实测 dis：
  ORIG   #1 LOAD_CONST <listcomp>; #2 MAKE_FUNCTION 0; #3 LOAD_FAST self; #4 LOAD_ATTR
               '_open_orders'; ... CALL 0
         #7 LOAD_CONST <listcomp>; #8 MAKE_FUNCTION 0; #9 LOAD_FAST self; #10 LOAD_ATTR
               '_delayed_orders'; ... CALL 0
         #13 LOAD_CONST ('open_orders','delayed_orders'); #14 BUILD_CONST_KEY_MAP 2; #15 RETURN_VALUE
  DECOMP #2 LOAD_CONST <listcomp>; #3 MAKE_FUNCTION 0; #4 LOAD_CONST <listcomp>; #5 MAKE_FUNCTION 0;
         #6 LOAD_FAST self; #7 LOAD_ATTR '_open_orders' ... CALL 0 ... CALL 0; RETURN_VALUE
         —— BUILD_CONST_KEY_MAP 整条消失，两个推导式被套成一层嵌套推导式。
对应 liveOK.py:66 生成的 `return [o.load() for account, o in [o.load() for ... ]]`。
"""


class Order(object):
    def save(self):
        return 1


class SimulationBroker(object):
    def __init__(self):
        self._open_orders = []
        self._delayed_orders = []

    def save(self):
        return {
            'open_orders': [o.save() for account, o in self._open_orders],
            'delayed_orders': [o.save() for account, o in self._delayed_orders],
        }


def save_two_comps(open_orders, delayed_orders, dump):
    return {
        'open_orders': [dump(o) for o in open_orders],
        'delayed_orders': [dump(o) for o in delayed_orders],
    }

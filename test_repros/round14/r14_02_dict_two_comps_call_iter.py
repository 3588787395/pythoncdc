# -*- coding: utf-8 -*-
"""R14-02 复现：iterable 是**函数调用**时的两个同级推导式（= broker.pyc 的字面形状）。

真实目标 broker.pyc <module>.SimulationBroker.save 的原始字节码（orig 22 条）：
  #1  LOAD_CONST <listcomp@118>   #2  MAKE_FUNCTION 0
  #3  LOAD_GLOBAL copy            #4  LOAD_ATTR deepcopy
  #5  LOAD_FAST self              #6  LOAD_ATTR _open_orders
  #7  CALL                        #8  GET_ITER            #9  CALL
  #10 LOAD_CONST <listcomp@119>   #11 MAKE_FUNCTION 0
  #12 LOAD_GLOBAL copy            #13 LOAD_ATTR deepcopy
  #14 LOAD_FAST self              #15 LOAD_ATTR _delayed_orders
  #16 CALL                        #17 GET_ITER            #18 CALL
  #19 LOAD_CONST ('open_orders','delayed_orders')         #20 BUILD_CONST_KEY_MAP 2
  #21 RETURN_VALUE
产物（decomp 15 条）将 #10/#11 当作「第一个推导式的内层」，#12..#16 整段消失，
#19/#20 一并消失，#8/#17 变成两层 GET_ITER。
期望：MISMATCH（缺陷复现）。
"""
import copy


class SimBroker(object):
    def __init__(self):
        self._open_orders = []
        self._delayed_orders = []

    def save(self):
        return {
            'open_orders': [o.load() for account, o in copy.deepcopy(self._open_orders)],
            'delayed_orders': [o.load() for account, o in copy.deepcopy(self._delayed_orders)],
        }


def call_iter_two_comps(t, u):
    return {'a': [x for x in list(t)], 'b': [y for y in list(u)]}

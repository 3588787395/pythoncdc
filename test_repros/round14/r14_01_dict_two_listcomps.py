# -*- coding: utf-8 -*-
"""R14-01 复现（基准缺陷形状）：dict 字面量的两个**同级** list 推导式被焊成一层嵌套。

真实目标：
  IQEngine/plugins/plugin_system_simulation/broker.pyc <module>.SimulationBroker.save
      [seq_len] orig=22 decomp=15   （7 条指令消失）
  IQEngine/plugins/plugin_system_simulation/live.pyc   <module>.DefaultLiveBroker.save
      [seq_len] orig=16 decomp=12   （4 条指令消失）

消失的指令（两例一致）：
  LOAD_CONST <第二个推导式的 code> 之后的「第二个推导式自己的 iterable 装载」
  + LOAD_CONST ('open_orders','delayed_orders') 键元组
  + BUILD_CONST_KEY_MAP 2
产物形态：
  return [y for y in [x for x in t]]        # dict 与 u 都不见了
期望：MISMATCH（缺陷复现）。
"""


class Broker(object):
    def __init__(self):
        self.p = []
        self.q = []

    def save(self):
        return {'p': [o for o in self.p], 'q': [o for o in self.q]}


def two_comps(t, u):
    return {'a': [x for x in t], 'b': [y for y in u]}


def two_comps_same_iter(t):
    # 两个值共用同一个 iterable：仍然坍缩（第二个 t 消失）。
    # 说明丢掉的不是「某个特定变量名」，而是第二个推导式整条装载链 + 键元组 +
    # BUILD_CONST_KEY_MAP。
    return {'a': [x for x in t], 'b': [y for y in t]}

"""repro_04: value_target 对 STORE_FAST 正常识别（对照）。

演示普通三元赋值 x = v if cond else w。
STORE_FAST 的 value_target 正确识别为 'x'，作为对照。
"""


def f(cond, v, w):
    x = v if cond else w
    return x

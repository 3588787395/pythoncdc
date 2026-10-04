"""rv2 变体面 B65（b6576_probe 邻域）：3 目标链式 / 单目标负对照"""


def v_chain3_boolop(x, y, z):
    a = b = c = (x > 0 and y > 0 and z > 0)
    return a + b + c


def n_single_target(x, y):
    a = (x > 0 and y > 0)
    return a

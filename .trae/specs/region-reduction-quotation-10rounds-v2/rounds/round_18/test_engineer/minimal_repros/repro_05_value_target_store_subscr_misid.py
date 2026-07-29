"""repro_05: value_target 对 STORE_SUBSCR 误识别（根因 A 核心）。

演示 data.loc[i] = v if cond else w。
STORE_SUBSCR 的下标 'i' 被误识别为三元消费的 value_target，
导致生成 i = i + 1 而非正确的下标赋值。
"""


def f(data, i, cond, v, w):
    data.loc[i] = v if cond else w

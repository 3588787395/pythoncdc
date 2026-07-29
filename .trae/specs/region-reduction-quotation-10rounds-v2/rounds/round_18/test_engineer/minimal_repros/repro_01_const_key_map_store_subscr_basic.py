"""repro_01: BUILD_CONST_KEY_MAP + STORE_SUBSCR 基本模式。

演示 data.loc[i] = {'a': x} 的 dict 构造 + 下标赋值。
根因 A：TernaryRegion value_target 误识别 STORE_SUBSCR 的下标变量。
"""


def f(data, i, x):
    data.loc[i] = {'a': x}

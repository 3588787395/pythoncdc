"""repro_07: 三元表达式后跟 dict 构造 + STORE_SUBSCR。

演示先有独立三元表达式，再有 dict 构造赋值。
TernaryRegion@1226 链式共享导致误识别。
"""


def f(data, i, cond, x):
    a = x if cond else 0
    data.loc[i] = {'a': a}

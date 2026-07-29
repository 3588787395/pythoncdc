"""repro_02: 三元表达式作为 dict 值 + STORE_SUBSCR。

演示 data.loc[i] = {'a': v if cond else w} 的模式。
get_str_data 中每个键的值都是三元表达式。
"""


def f(data, i, cond, v, w):
    data.loc[i] = {'a': v if cond else w}

"""repro_03: 多键三元 dict + STORE_SUBSCR。

演示 data.loc[i] = {'a': ..., 'b': ..., 'c': ...} 多键模式。
get_str_data 有 7 个键，每个值都是三元表达式。
"""


def f(data, i, cond, v1, v2, v3):
    data.loc[i] = {
        'a': v1 if cond else 0,
        'b': v2 if cond else 0,
        'c': v3 if cond else 0,
    }

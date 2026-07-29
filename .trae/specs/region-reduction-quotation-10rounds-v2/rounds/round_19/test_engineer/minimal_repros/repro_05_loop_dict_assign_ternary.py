"""repro_05: 循环中 dict 赋值 + 三元值 + 索引递增。

模拟 get_str_data 内层循环：data.loc[i] = {...}，i 递增，
dict 值含三元表达式（numpy.nan if cond else expr）。
"""


import numpy


def f(df, n):
    data = {}
    i = 0
    for j in range(n):
        cond = j % 2
        data.loc[i] = {
            'a': numpy.nan if cond == 1 else df[j],
            'b': numpy.nan if cond == 1 else df[j],
        }
        i += 1
    return data

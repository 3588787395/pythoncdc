"""repro_08: 循环中 dict 赋值 + 索引递增。

演示 get_str_data 的循环结构：i 在循环中递增，data.loc[i] = {...}。
"""


def f(data, n, cond):
    i = 0
    for j in range(n):
        data.loc[i] = {
            'a': j if cond else 0,
            'b': j if cond else 0,
        }
        i += 1

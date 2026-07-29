"""repro_06: data.loc[i] = {...} 完整模式（get_str_data 缩影）。

演示循环中 data.loc[i] = {'k1': ternary, 'k2': ternary} 模式。
i 在循环中递增，每个键值都是三元表达式。
"""


def f(data, n, cond):
    for i in range(n):
        data.loc[i] = {
            'k1': 1 if cond else 0,
            'k2': 2 if cond else 0,
        }

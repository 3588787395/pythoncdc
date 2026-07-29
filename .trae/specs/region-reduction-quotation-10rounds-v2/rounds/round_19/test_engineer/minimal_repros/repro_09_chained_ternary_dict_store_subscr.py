"""repro_09: 链式三元 dict 构造 + STORE_SUBSCR 消费。

模拟 get_str_data 的 dict 赋值模式：
data.loc[i] = {'a': ternary1, 'b': ternary2}
- ternary1.merge_block == ternary2.entry（链式共享）
- ternary2.merge_block 含 BUILD_CONST_KEY_MAP + STORE_SUBSCR
R18 已修复 value_target 对 STORE_SUBSCR 的误识别（value_target=None）。
"""

import numpy


def f(df, i, cond):
    data = {}
    data.loc[i] = {
        'a': numpy.nan if cond == 1 else df[0],
        'b': numpy.nan if cond == 1 else df[1],
    }
    return data

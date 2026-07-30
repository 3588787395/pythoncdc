"""repro_01: BUILD_CONST_KEY_MAP 消费模式 — 混合三元+普通载入值的核心模式。

测试 aspect: dict 字面量所有 key 为常量时，CPython 用 BUILD_CONST_KEY_MAP n 构造。
部分 value 是三元表达式 (x if cond else y)，部分 value 是普通 LOAD。三元表达式的
merge_block 直接流入 BUILD_CONST_KEY_MAP，反编译器需将这组值表达式作为整体 dict
构造语句归约，而非拆成独立 TernaryRegion + bare expr。

本 repro 对应 get_str_data 根因 A 的核心消费模式：
    d = {'open': a, 'close': b, 'price': x if cond else 0}
"""


def f(data, i):
    cond = data.get('flag')
    d = {
        'open': data['open'],
        'close': data['close'],
        'high': data['high'],
        'low': data['low'],
        'volume': data['volume'],
        'price': data['price'] if cond else 0,
        'money': data['money'] if cond else 0,
    }
    return d

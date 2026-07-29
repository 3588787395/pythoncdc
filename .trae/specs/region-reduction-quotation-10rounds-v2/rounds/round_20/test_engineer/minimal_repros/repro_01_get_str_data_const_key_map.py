"""repro_01: get_str_data 根因 A — BUILD_CONST_KEY_MAP 消费模式未完整建模。

模拟 get_str_data 的 dict 构造：BUILD_CONST_KEY_MAP n + STORE_SUBSCR 消费 7 个值
表达式（含三元 + 普通载入）。R18 已修复 value_target 误识别（STORE_SUBSCR 时 break），
但消费模式整体归约未建模——7 个值表达式应作为整体 dict 构造语句归约。

后续迭代建议：建模 BUILD_CONST_KEY_MAP 消费模式，使 dict value 表达式作为整体语句归约。
"""


def f(data, i):
    cond = data.get('flag')
    data.loc[i] = {
        'open': data['open'],
        'close': data['close'],
        'high': data['high'],
        'low': data['low'],
        'volume': data['volume'],
        'price': data['price'] if cond else 0,
        'money': data['money'] if cond else 0,
    }

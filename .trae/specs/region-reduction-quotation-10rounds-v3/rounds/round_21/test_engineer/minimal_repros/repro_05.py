"""repro_05: BUILD_CONST_KEY_MAP 消费模式 — STORE_SUBSCR 下标赋值消费。

测试 aspect: dict 字面量构造后立即通过 STORE_SUBSCR 写入容器下标
(data.loc[i] = {...})。BUILD_CONST_KEY_MAP 产出的 dict 作为 STORE_SUBSCR 的值操作数
被消费。这是 get_str_data 的实际消费形态：order_data.loc[i] = {'open': ..., ...}。
反编译器需将 BUILD_CONST_KEY_MAP + STORE_SUBSCR 作为整体赋值语句归约。

    data.loc[i] = {'open': a, 'close': b if cond else 0}
"""


def f(data, i, a, b):
    cond = i > 0
    data.loc[i] = {
        'open': a,
        'close': b if cond else 0,
        'high': a,
        'low': b,
    }

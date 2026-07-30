"""repro_10: BUILD_CONST_KEY_MAP 消费模式 — 综合 (循环 + 链式三元 merge + 混合值 + STORE_SUBSCR)。

测试 aspect: 综合模式，对应 get_str_data 实际形态。for 循环内通过 STORE_SUBSCR 将
BUILD_CONST_KEY_MAP 构造的 dict 写入 DataFrame.loc[i]。dict value 包含：
- 普通载入 (data['open'])
- 引用循环变量的三元 (data['price'] if cond else 0)
- 链式共享 merge_block 的连续三元 (price/money 共享 cond)
反编译器需将整组 value 表达式 + BUILD_CONST_KEY_MAP + STORE_SUBSCR 作为循环体内单条
赋值语句归约，遵循原则 2（每块唯一归属）与原则 4（入口引用语义）。

    for i in rdata.items():
        order_data.loc[i] = {'open': ..., 'price': ... if cond else 0, ...}
"""


def f(rdata, order_data):
    for i, item in rdata.items():
        cond = item.get('flag')
        order_data.loc[i] = {
            'open': item['open'],
            'close': item['close'],
            'high': item['high'],
            'low': item['low'],
            'volume': item['volume'],
            'price': item['price'] if cond else 0,
            'money': item['money'] if cond else 0,
        }

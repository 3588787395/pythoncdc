"""repro_04: get_str_data 区域边界对齐 — TernaryRegion@1226 entry 包含前驱载入块。

R19 诊断确认 TernaryRegion@1226 的 entry（1226）不应包含前驱 price 载入块（1226-1270），
应从条件测试点（1274）开始。区域边界未对齐导致 dict value 表达式归约错位。

后续迭代建议：_identify_ternary_regions 的区域边界对齐，entry 不应包含前驱普通载入块。
"""


def f(data, i):
    cond = data.get('flag')
    price = data['price']
    val = price if cond else 0
    data.loc[i] = {'price': val}
    return val

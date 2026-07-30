"""repro_08: BUILD_CONST_KEY_MAP 消费模式 — 循环内三元引用循环变量 + 普通载入混合。

测试 aspect: dict 构造在 for 循环内，部分 value 是引用循环变量的三元表达式，部分是
普通载入。三元 merge_block + BUILD_CONST_KEY_MAP + STORE_SUBSCR 都在循环体内。反编译器
需保证循环 region 正确包含 dict 构造消费节点，三元 value 的归约不穿透循环边界。

    for i, item in enumerate(items):
        result[i] = {'idx': i, 'val': item if item else 0, 'flag': flag}
"""


def f(items, flag):
    result = {}
    for i, item in enumerate(items):
        result[i] = {
            'idx': i,
            'val': item if item else 0,
            'flag': flag,
            'next': items[i + 1] if i + 1 < len(items) else None,
        }
    return result

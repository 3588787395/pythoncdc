"""R8 repro_09: for 循环体尾部 STORE_SUBSCR 赋值丢失。
缺陷: for 循环体尾部的 `obj[key] = value` 形式赋值被丢弃，循环后构造语句也部分丢失。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(items):
    result = {}
    for k in items:
        v = items[k]
        if v is not None:
            result[k] = v
        result['count'] = len(result)
    total = sum(result.values())
    return total

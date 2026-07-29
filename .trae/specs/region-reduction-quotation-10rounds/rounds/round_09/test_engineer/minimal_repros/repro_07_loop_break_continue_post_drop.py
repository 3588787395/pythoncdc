"""R9 repro_07: for 循环内 break/continue + 循环后语句丢失。
缺陷: for 循环体内 break 与循环后构造语句被部分丢弃。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(items, target):
    found = None
    for x in items:
        if x == target:
            found = x
            break
        elif x > target:
            continue
        else:
            found = x
    if found is not None:
        result = [found]
        result.append(found + 1)
        return result
    return []

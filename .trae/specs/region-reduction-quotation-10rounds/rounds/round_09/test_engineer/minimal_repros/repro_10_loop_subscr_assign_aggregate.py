"""R9 repro_10: for 循环 STORE_SUBSCR 赋值 + 循环后聚合语句丢失。
缺陷: for 循环体内 obj[key]=value 赋值与循环后聚合语句丢失。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(rows):
    result = {}
    for row in rows:
        k = row['key']
        v = row['val']
        if k in result:
            result[k] = result[k] + v
        else:
            result[k] = v
        result['count'] = len(result)
    total = sum(result.values())
    return total

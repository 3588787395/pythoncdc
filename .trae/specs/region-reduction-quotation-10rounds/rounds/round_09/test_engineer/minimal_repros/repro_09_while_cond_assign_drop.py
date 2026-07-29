"""R9 repro_09: while 循环条件赋值与循环体语句丢失。
缺陷: while 循环前/内的条件赋值及循环体末尾语句丢失。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(data, limit):
    i = 0
    total = 0
    while i < len(data):
        cur = data[i]
        if cur > limit:
            total = total + cur
            i = i + 1
        else:
            i = i + 1
            continue
    avg = total / len(data) if len(data) > 0 else 0
    return avg

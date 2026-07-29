"""R9 repro_08: for 循环内多层嵌套 if/elif/else 语句丢失。
缺陷: for 循环体内 3 层嵌套 if/elif/else 的深层分支语句丢失。
区域类型: Loop + Conditional  违反原则: 3(嵌套即抽象节点)
"""
def f(records):
    out = []
    for rec in records:
        if rec['type'] == 'a':
            if rec['sub'] == 1:
                out.append(rec['val'] * 2)
            elif rec['sub'] == 2:
                if rec['flag']:
                    out.append(rec['val'] + 10)
                else:
                    out.append(rec['val'] + 20)
            else:
                out.append(rec['val'])
        elif rec['type'] == 'b':
            out.append(rec['val'] - 1)
        else:
            out.append(0)
    return out

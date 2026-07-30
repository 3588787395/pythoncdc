"""repro_02 — 缺陷1变体: while 循环 + if/elif/else + 兄弟赋值 + 兄弟 if。

then 分支应为简单赋值，循环末尾的兄弟赋值/兄弟 if 不应被并入 then。
"""
def f(items):
    pre = None
    out = []
    i = 0
    while i < len(items):
        n = items[i]
        if pre is None:
            out.append(n)
        elif n < 0:
            break
        else:
            out.append(n + 1)
        pre = n
        if len(out) > 3:
            pass
        i += 1
    return out

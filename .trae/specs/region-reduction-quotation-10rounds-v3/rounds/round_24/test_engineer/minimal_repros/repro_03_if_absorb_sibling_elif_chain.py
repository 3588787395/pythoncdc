"""repro_03 — 缺陷1变体: for 循环 + if/elif 链（无 else）+ 兄弟 if。

测试 elif 链场景下兄弟 if 是否被错误并入第一个 then 分支。
"""
def f(items):
    pre = None
    out = []
    for n in items:
        if pre is None:
            out.append(n)
        elif n == 0:
            break
        elif n < 0:
            out.append(-n)
        if pre != n:
            pre = n
        if len(out) != 0:
            pass
    return out

"""repro_02: while 循环内 if-continue 兄弟语句（while 版本）。

测试 aspect: while 循环体内 if 的两分支均→回边（continue 无条件兄弟）。
与 repro_01（for 循环）对照，验证循环类型无关性。

    while j < n:
        if cond_a:
            if cond_b:
                x = 1
            continue        # ← 兄弟语句
        y = j
        break
"""


def f(items):
    result = []
    j = 0
    n = len(items)
    while j < n:
        if items[j] > 0:
            if j == n - 1:
                result.append(j)
            continue
        result.append(-j)
        break
    return result

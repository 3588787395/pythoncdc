"""repro_01: for 循环内 if-continue 兄弟语句 — 核心模式。

测试 aspect: for 循环体内含一个 if 语句，if 的 true 分支执行赋值后 fallthrough
到回边（JUMP_BACKWARD），if 的 false 分支也跳到回边。两分支均→回边，continue
为无条件兄弟语句（在 if 之后）。反编译器需将 continue 作为 if 的兄弟语句发射，
不可将 if 条件与外层条件合并或把 continue 内嵌于 true 分支。

本 repro 对应 get_str_data instr_diff@179 的核心缺陷：
    for j in range(n):
        if cond_a:
            if cond_b:
                x = 1
            continue        # ← 兄弟语句（两分支均→回边）
        y = j
        break
"""


def f(items):
    result = []
    for j in range(len(items)):
        if items[j] > 0:
            if j == len(items) - 1:
                result.append(j)
            continue
        result.append(-j)
        break
    return result

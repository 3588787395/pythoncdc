"""Round 9 守卫面新构造 6：B2 continue 守卫 × with/try 交叉宿主。

攻击清单第 4 项：BoolOp/continue 守卫 × with/try 交叉。continue 目标块
位于 with 体或 try 体内时的角色判定与归属竞争。
"""


def cont_in_with(xs, p, a):
    for x in xs:
        with open(p) as f:
            if a(f):
                continue
            use(f, x)
    return 1


def cont_in_try(xs, a, b):
    for x in xs:
        try:
            if a(x):
                continue
            work(x)
        except ValueError:
            b(x)
    return 2


def cont_with_boolop(xs, a, b, c):
    for x in xs:
        if a(x) and b(x) or c(x):
            continue
        keep(x)
    return 3

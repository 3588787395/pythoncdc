"""Round 9 守卫面新构造 7：循环守卫 × 生成器（yield 主体内 continue/共享尾）。

攻击清单第 4 项：循环守卫 × 生成器。yield 与 continue 守卫交叠、
yield 作共享尾语句——回边重检与 yield 交织（_has_yield_in_body 面）。
"""


def gen_cont_guard(xs, a):
    for x in xs:
        if a(x):
            continue
        yield x
    yield -1


def gen_shared_tail(xs, a, b):
    for x in xs:
        if a(x):
            yield 1
        elif b(x):
            yield 2
        yield 0


def gen_while_cont(a, b):
    while a:
        if b():
            continue
        yield a
        a = a - 1

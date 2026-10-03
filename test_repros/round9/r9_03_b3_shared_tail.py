"""Round 9 B3 守卫族回归攻击 3：Loop 共享尾守卫（W14-C）外推 + try 内共享尾吸收。

攻击面：W14-C 臂内嵌套 if 汇合剪枝（region_analyzer.py:21095/29844）、
fix3-T1/T2 try 内共享尾吸收（region_ast_generator.py:14898）、
fix3-T6（:20569）。守卫适用形态外推一格：共享尾含多语句与跨结构组合。
"""


def arm_nested_if_shared(a, b, xs):
    for i in xs:
        if a(i):
            if b(i):
                v = 1
            else:
                v = 2
            log(v)
            log2(v)
        keep(i)
    return 1


def try_shared_tail(a, xs):
    for i in xs:
        try:
            if a(i):
                r = step(i)
                r = r + 1
        finally:
            cleanup()
        post(i)
    return 2


def while_arm_nested_shared(a, b):
    while a:
        if b():
            if a > 2:
                m = 3
            else:
                m = 4
            note(m)
        a = a - 1
    return 3

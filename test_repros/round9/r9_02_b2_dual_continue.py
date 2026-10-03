"""Round 9 B2 守卫族回归攻击 2：守卫互斥组合——两臂同时为 continue/break 目标。

攻击面：_then_is_pure_cont / _else_is_pure_cont 同时命中时的分支互斥
（region_ast_generator.py:12380-12410 附近的两条对称 if 守卫），
以及 break 与 continue 混排、嵌套循环 continue 目标归属。
"""


def both_arms_continue(xs, a):
    for x in xs:
        if a(x):
            continue
        else:
            continue
    return 1


def break_continue_mix(xs, a, b):
    for x in xs:
        if a(x):
            break
        if b(x):
            continue
        keep(x)
    return 2


def nested_continue_inner(xs, ys, a):
    for x in xs:
        for y in ys:
            if a(x, y):
                continue
        tag(x)
    return 3


def while_dual_exit(a, b):
    while a:
        if b:
            break
        if a > 3:
            continue
        a = a + 1
    return 4

"""Round 9 守卫族回归攻击 10：守卫适用最小形态收缩一格。

外推（r9_01..r9_09）的反向：把守卫覆盖的最小形态再剥掉一层要素——
continue 即循环体末语句（无尾随语句）、嵌套 if 无共享尾、无循环宿主的
纯嵌套 if-else（B4 孤儿释放面收缩）。守卫不应对收缩形态误触发。
"""


def cont_tail_only(xs, a):
    for x in xs:
        if a(x):
            continue


def while_cont_tail_only(a, b):
    while a:
        if b:
            continue


def nested_if_no_shared_tail(xs, a, b):
    for i in xs:
        if a(i):
            if b(i):
                v = 1
            else:
                v = 2


def pure_nested_ifelse(a, b, c):
    if a:
        if b:
            r = 1
        else:
            r = 2
    else:
        r = 3
    return r

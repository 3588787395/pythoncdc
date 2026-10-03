"""Round 9 负对照 1：B2 守卫适用最小形态（必须保持 MATCH）。"""


def simple_if_cont(xs, a):
    for x in xs:
        if a(x):
            continue
        use(x)
    return 1


def simple_if_break(xs, a):
    for x in xs:
        if a(x):
            break
    return 2

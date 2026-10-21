"""AT-01: 内层循环自然出口落到外层循环回边块（全局角色 CONTINUE 命中外层）"""


def c2(xs):
    for a in xs:
        for b in xs:
            print(b)

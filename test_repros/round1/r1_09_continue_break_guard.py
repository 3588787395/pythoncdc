# r1_09 if 体含 continue/break 守卫（B2 关联）
# 焦点：混合链条件 + 循环控制流（continue/break 守卫族相交）


def f(a, b, c, xs):
    total = 0
    for x in xs:
        if a and b or c:
            if x:
                continue
        total += 1
        if b or c and a:
            break
    return total

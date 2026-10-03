"""Round 9 守卫面新构造 9：B55 窄门控边界外形态（循环控制流尾随 + 守卫交叠）。

攻击清单第 4 项：B55-c 窄门控（_b55_is_pure_const_return_block，round8 :28525
门控）边界外形态——空 try/finally 后尾随 break/continue/if 守卫（循环
控制流角色块），窄门控按设计拒绝后由 _generate_try 收尾装配面接管。
"""


def tryfin_trailing_break(xs, a):
    for x in xs:
        try:
            pass
        finally:
            pass
        if a(x):
            break
    return 1


def tryfin_trailing_cont(xs, a):
    while xs:
        try:
            pass
        finally:
            pass
        if a(1):
            continue
        xs.pop()
    return 2


def tryfin_shared_guard(a, b):
    try:
        pass
    finally:
        pass
    if a and b:
        return 3
    return 4

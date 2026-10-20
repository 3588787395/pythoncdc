def s_b152_if_ternary(a, b, c, flag):
    if a if flag else b < c:
        return "t"
    return "f"


def s_b152_if_ternary2(a, b, flag):
    if (a if flag else b) > 0:
        return a
    return b

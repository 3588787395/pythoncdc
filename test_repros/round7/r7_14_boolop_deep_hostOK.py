# Source Generated with Decompyle++ (Python version)
# File: r7_14_boolop_deep_host.pyc (Python 3.11)

__doc__ = 'R7-14 复合条件深层宿主面（BoolOp+三元+链式比较在 if/while/推导式过滤）。'
def h_if_composite(a, b, c, d, flag):
    if a < b < c:
        if flag and d:
            return 1
    return 0
def h_while_composite(n, a, b, flag):
    if n > 0:
        while a < b or flag:
            n -= 1
    return n
def h_listcomp_filter_composite(xs, lim, flag):
    return [x for x in xs if 0 < x < lim]
def h_if_ternary_chain_composite(a, b, c, flag):
    if (a if flag else b < c):
        pass
    return 't'
def h_for_filter_and_ternary(xs, flag):
    return [x if flag else -x for x in xs if x and flag]
def h_return_composite(a, b, c, flag):
    if flag:
        return a and b
    else:
        return a < b < c

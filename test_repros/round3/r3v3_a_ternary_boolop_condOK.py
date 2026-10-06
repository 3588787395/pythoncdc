# Source Generated with Decompyle++ (Python version)
# File: r3v3_a_ternary_boolop_cond.pyc (Python 3.11)

__doc__ = """r3v3-A 反向外推（假阴性）——位 2 _can_be_ternary_header 新守卫攻击。

真三元/真条件头是否被「末指令 ∈ SHORT_CIRCUIT_JUMP_OPS 即判否」误杀。
"""
def t_simple(a, b, c, d):
    return a or b if c else d
def t_and_cond(a, b, c, d):
    return a if b and c else d
def t_or_cond_pair(a, b, c, d, e):
    if c or d:
        return a and b
    else:
        return e
def t_nested(a, b, c, d, e, f):
    return (a or b if c else d and e) if f else b or c
def t_cond_or_of_and(a, b, c, d, e):
    if b and c or d:
        return a
    else:
        return e
def t_cond_chain_or(a, b, c, d):
    return a if b or c else 0
def t_value_or_cond_simple(a, b, c):
    return a if b else c
def t_in_for(a, b, c, d):
    acc = []
    for i in range(3):
        acc.append(a or b if c else d)
    return acc
def t_in_while(a, b, c, d, n):
    acc = 0
    while n < 3:
        acc += a or b if c else d
        n += 1
    return acc
def t_in_try(a, b, c, d):
    x = 0
    try:
        x = a or b if c else d
    except ValueError:
        x = -1
    return x
def t_in_for_return(y, a, b, c):
    for i in y:
        a or b if c else 0
    return 0

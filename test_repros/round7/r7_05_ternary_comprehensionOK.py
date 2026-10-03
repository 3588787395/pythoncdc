# Source Generated with Decompyle++ (Python version)
# File: r7_05_ternary_comprehension.pyc (Python 3.11)

__doc__ = 'R7-05 推导式内三元位置面（listcomp/dictcomp/setcomp/genexp）。'
def t_listcomp_ternary(xs, flag):
    return [x if flag else -x for x in xs]
def t_listcomp_ternary_filter(xs, flag):
    return [0 for x in xs if flag
                and x % 2]
def t_dictcomp_ternary(ks, vs, flag):
    return {k: v if flag else None for k, v in zip(ks, vs)}
def t_dictcomp_key_ternary(ks, flag):
    return {k if flag else k.upper(): len(k) for k in ks}
def t_setcomp_ternary(xs, flag):
    return {x % 3 if flag else x for x in xs}
def t_genexp_ternary(xs, flag):
    return sum((x if flag else 1 for x in xs))
def t_nested_comp_ternary(xss, flag):
    return [[y if flag else y * 2 for y in row] for row in xss]

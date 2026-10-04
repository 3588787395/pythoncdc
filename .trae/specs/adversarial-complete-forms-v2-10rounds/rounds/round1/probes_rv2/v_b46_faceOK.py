# Source Generated with Decompyle++ (Python version)
# File: v_b46_face.pyc (Python 3.11)

__doc__ = 'rv2 变体面 B46 尾项（r7_07 t_nest_in_condition 邻域）：条件位融合三元'
def v_while_cond_nest(n, a, b, c, d, f1, f2):
    if (c if f2 else d):
        if f1:
            if a:
                pass
        elif b:
            pass
        else:
            pass
    return n
def v_if_cond_nest(a, b, c, d, f1, f2):
    if (c if f2 else d):
        if f1:
            if a:
                pass
        elif b:
            pass
        else:
            return 0
def n_for_body_nest(xs, f1, f2):
    out = []
    for x in xs:
        if not f2 or x:
            x if f1 else 0
        else:
            2
    return out

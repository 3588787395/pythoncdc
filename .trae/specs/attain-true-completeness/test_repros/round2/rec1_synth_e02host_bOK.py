# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_e02host_b.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F2b（e02 宿主族 item 7c 推导式交叉变体，非语料）。'
def v_comp_cond(a, b, c, xs):
    for i in range(2):
        if i:
            return [x for x in xs if (a or b) and c]
    return []
def v_genexp_cond(a, b, c, xs):
    for i in range(2):
        if i:
            return sum((1 for x in xs if (a or b) and c))
    return 0
def v_dictcomp_value(a, b, c, xs):
    for i in range(2):
        if i:
            return {x: (a or b) and c for x in xs if x}
    return {}

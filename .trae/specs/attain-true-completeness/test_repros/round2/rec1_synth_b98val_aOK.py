# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b98val_a.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F1a（B98 值链/融合族，items 1-6/8/10 交叉变体，非语料）。'
def f_orprefix_compare(p, q, r):
    acc = []
    for i in range(2):
        if i and i:
            return ((p or q) and r) > 2
    return acc
def f_andtail_store(p, q, r):
    t = (p or q) and r
    return t
def f_mergenot_wrap(p, q, r):
    return not (p or q and not r)
def f_andor_subscript(v, out):
    out.append((v and [v] or [0])[0])
    return None
def f_ifcond_fused(p, q, r):
    if (p or q) and r:
        return 1
    return 0

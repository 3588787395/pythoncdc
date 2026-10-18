# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b98val_b.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F1b（B98 值链/融合族，items 1-6/12 交叉变体，非语料）。'
def g_call_wrap(p, q, r):
    def sink(x):
        return x + 1
    for i in range(3):
        if i:
            return sink((p or q) and r)
    return 0
def g_walrus_wrap(p, q, r):
    for i in range(2):
        if i:
            if (w := (p or q) and r):
                return w
    return 0
def g_or_tail(p, q, r, s):
    return p and q or r or s
def g_valdiamond_else_and(p, q, r, flag):
    return p if flag else q and r
def g_valdiamond_else_and3(p, q, r, s, flag):
    return p if flag else q and r and s

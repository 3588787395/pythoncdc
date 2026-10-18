# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_rv7cctern_b.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F3b（rv7_02 三元链式比较族 item 9 交叉变体·多位形，非语料）。'
def s_chain_mixed_ops(m, n, o, p, q, g1, g2):
    return (m if g1 else n) > (o if g2 else p) >= q
def s_chain_eq_ne(m, n, o, p, q, r, g1, g2, g3):
    return (m if g1 else n) == (o if g2 else p) != (q if g3 else r)
def s_chain_binop_tail(m, n, o, p, q, g1, g2):
    return (m if g1 else n) <= (o if g2 else p) < q + 1

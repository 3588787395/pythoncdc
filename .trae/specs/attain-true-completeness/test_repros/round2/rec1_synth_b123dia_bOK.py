# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b123dia_b.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F9b（B123 while 头链式比较 + IfExp 尾钻石族 item 16 交叉变体·多位形，非语料）。'
def o_binop_diamond(a, b, d, e):
    s = 0
    while a < b < 100 and (d if d else e * 2):
        a += 1
        s += a
    return s
def o_two_stmt_body(x, y, p, q):
    u = 0
    w = 0
    while 0 < x < 8 and (p if p else q):
        x += 1
        u += x
        w += 1
    return u + w
def o_mixed_chainops(x, y, p, q):
    t = 0
    while 0 <= x != 7 and (y if y else q):
        x += 2
        t += 1
    return t

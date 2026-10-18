# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b78host_b.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F7b（B78 嵌套三元宿主族 item 14 交叉变体·多位形，非语料）。'
def j_if_host_two(m, n, o, p, f1, f2):
    if ((m if f1 else n) if (o if f2 else p) else 0):
        k = 1
        return k
    return 2
def j_while_host_two(x, y, m, n, o, p, f1, f2):
    while ((m if f1 else n) if (o if f2 else p) else 0):
        x += 1
        y += 1
    return x + y
def j_value_call(m, n, o, p, f1, f2):
    def sink(v):
        return v
    return sink((m if f1 else n) if (o if f2 else p) else 0)

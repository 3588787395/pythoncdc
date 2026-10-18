# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b78host_a.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F7a（B78 嵌套三元宿主族 item 14 交叉变体，非语料）。'
def h_if_host(m, n, o, p, f1, f2):
    if ((m if f1 else n) if (o if f2 else p) else 0):
        return 5
    return 6
def h_while_host(k, m, n, o, p, f1, f2):
    while ((m if f1 else n) if (o if f2 else p) else 0):
        k -= 2
    return k
def h_value_host(xs, w, f1, f2):
    out = []
    for x in xs:
        out.append((w if f1 else 9) if (w if f2 else 1) else 7)
    return out

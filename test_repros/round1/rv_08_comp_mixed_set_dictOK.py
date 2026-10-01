# Source Generated with Decompyle++ (Python version)
# File: rv_08_comp_mixed_set_dict.pyc (Python 3.11)

def f(vals, a, b, c):
    n = 0
    out_s = None
    out_d = None
    while n < 2:
        s = {v for v in vals if a and b or c}
        d = {v: n for v in vals if a and b or c}
        out_s = s
        out_d = d
        n += 1
    return (out_s, out_d)

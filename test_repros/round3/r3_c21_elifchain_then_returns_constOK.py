# Source Generated with Decompyle++ (Python version)
# File: r3_c21_elifchain_then_returns_const.pyc (Python 3.11)

def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b':
        if not sv is not None or lv is None:
            return 0
        else:
            return down(sv[-1], lv[-1])

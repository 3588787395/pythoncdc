# Source Generated with Decompyle++ (Python version)
# File: r3_c17_elifchain_no_trailing_return.pyc (Python 3.11)

def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b' and sv is not None:
        if lv is None:
            return None
        else:
            return down(sv, lv)
    else:
        return None

# Source Generated with Decompyle++ (Python version)
# File: r3_c22_elifchain_three_members.pyc (Python 3.11)

def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b' and sv is not None and lv is not None:
        if t is None:
            return None
        else:
            return down(sv[-1], lv[-1])
    else:
        return None

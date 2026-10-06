# Source Generated with Decompyle++ (Python version)
# File: r3_c20_ifarm_not_elif_chain.pyc (Python 3.11)

def f(t, sv, lv):
    if t == 'a':
        if not sv is not None or lv is None:
            return None
        else:
            return down(sv[-1], lv[-1])
    else:
        return None

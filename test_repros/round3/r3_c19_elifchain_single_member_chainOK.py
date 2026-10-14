# Source Generated with Decompyle++ (Python version)
# File: r3_c19_elifchain_single_member_chain.pyc (Python 3.11)

def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b':
        if sv is None:
            return None
        else:
            return down(sv[-1], lv[-1])

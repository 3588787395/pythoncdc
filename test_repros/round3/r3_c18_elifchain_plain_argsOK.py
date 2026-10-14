# Source Generated with Decompyle++ (Python version)
# File: r3_c18_elifchain_plain_args.pyc (Python 3.11)

def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b' and sv is not None:
        if lv is None:
            return None
        else:
            return down(sv[-1], lv[-1])
    else:
        return None

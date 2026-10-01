# Source Generated with Decompyle++ (Python version)
# File: rv_03_loopbody_forinwhile_break.pyc (Python 3.11)

def f(items, a, b, c):
    out = []
    for it in items:
        while it:
            if a:
                if b or c:
                    break
            it -= 1
        out.append(it)
    return out

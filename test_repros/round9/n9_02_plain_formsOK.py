# Source Generated with Decompyle++ (Python version)
# File: n9_02_plain_forms.pyc (Python 3.11)

__doc__ = 'Round 9 负对照 2：基础控制流形态（必须保持 MATCH）。'
def plain_ifelse(a, b):
    if a:
        return 1
    else:
        return 2
def plain_for(xs):
    t = 0
    for x in xs:
        t += x
    return t
def plain_while(a):
    n = 0
    while a:
        n += 1
        a -= 1
    return n

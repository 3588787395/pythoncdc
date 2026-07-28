# Source Generated with Decompyle++ (Python version)
# File: repro_05_for_else_two_branches_continue.pyc (Python 3.11)

def f(items, out):
    for x in items:
        if x == 1:
            continue
        elif x == 2:
            continue
        else:
            out.append(x)
    out.append(-1)

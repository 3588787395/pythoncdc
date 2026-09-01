# Source Generated with Decompyle++ (Python version)
# File: repro_11_for_else_all_branches_return_continue.pyc (Python 3.11)

def f(items, out):
    for x in items:
        if x == 1:
            continue
        elif x == 2:
            out.append(x)
            continue
        else:
            out.append(x * 2)
    out.append(-1)

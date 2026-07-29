# Source Generated with Decompyle++ (Python version)
# File: repro_07_for_else_single_continue.pyc (Python 3.11)

def f(items, out):
    for x in items:
        if x == 0:
            continue
        out.append(x)
    out.append(-1)

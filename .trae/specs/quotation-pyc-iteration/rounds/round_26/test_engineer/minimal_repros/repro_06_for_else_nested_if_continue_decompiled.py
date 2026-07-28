# Source Generated with Decompyle++ (Python version)
# File: repro_06_for_else_nested_if_continue.pyc (Python 3.11)

def f(items, out):
    for x in items:
        if x > 0:
            if x == 5:
                continue
            out.append(x)
        else:
            continue
    out.append(-1)

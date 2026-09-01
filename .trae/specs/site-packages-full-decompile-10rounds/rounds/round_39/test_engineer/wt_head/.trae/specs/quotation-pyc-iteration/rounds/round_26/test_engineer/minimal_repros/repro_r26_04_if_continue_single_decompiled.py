# Source Generated with Decompyle++ (Python version)
# File: repro_r26_04_if_continue_single.pyc (Python 3.11)

def f(items, out):
    for x in items:
        if x == 0:
            continue
        elif x == 1:
            continue
        else:
            out.append(x)

# Source Generated with Decompyle++ (Python version)
# File: repro_r26_05_if_continue_three.pyc (Python 3.11)

def f(items, out):
    for x in items:
        if x == 1:
            continue
        elif x == 2:
            continue
        elif x == 3:
            continue
        else:
            out.append(x)

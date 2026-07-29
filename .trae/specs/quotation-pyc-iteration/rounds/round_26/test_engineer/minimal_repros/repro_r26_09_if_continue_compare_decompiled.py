# Source Generated with Decompyle++ (Python version)
# File: repro_r26_09_if_continue_compare.pyc (Python 3.11)

def f(items, out):
    for x in items:
        if x > 10:
            continue
        elif x < 0:
            continue
        else:
            out.append(x)

# Source Generated with Decompyle++ (Python version)
# File: repro_r26_02_if_continue_chain.pyc (Python 3.11)

def f(items, out):
    for x in items:
        if x == 1:
            continue
        elif x == 2:
            continue
        else:
            out.append(x)

# Source Generated with Decompyle++ (Python version)
# File: repro_r26_07_if_continue_while_loop.pyc (Python 3.11)

def f(items, out):
    while items:
        x = items.pop()
        if x == 0:
            continue
        if x == 1:
            continue
        out.append(x)

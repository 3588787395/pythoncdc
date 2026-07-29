# Source Generated with Decompyle++ (Python version)
# File: repro_r26_10_if_continue_isinstance.pyc (Python 3.11)

def f(items, out):
    for x in items:
        if isinstance(x, str):
            continue
        elif isinstance(x, dict):
            continue
        else:
            out.append(x)

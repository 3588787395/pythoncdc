# Source Generated with Decompyle++ (Python version)
# File: repro_02_for_else_all_continue.pyc (Python 3.11)

def f(items, result):
    for x in items:
        if x > 0:
            continue
        result.append(x)
    result.append(-1)

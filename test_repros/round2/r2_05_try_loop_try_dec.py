# Source Generated with Decompyle++ (Python version)
# File: r2_05_try_loop_try.pyc (Python 3.11)

def f(n, d):
    acc = 0
    try:
        for i in range(n):
            try:
                acc += d[i] // (i + 1)
            except (KeyError, ZeroDivisionError):
                acc -= 1
    except TypeError:
        acc = -1
    return acc

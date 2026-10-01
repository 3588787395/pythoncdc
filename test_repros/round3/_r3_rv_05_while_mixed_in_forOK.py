# Source Generated with Decompyle++ (Python version)
# File: rv_05_while_mixed_in_for.pyc (Python 3.11)

def f(n, a, b, c):
    s = 0
    for _ in range(n):
        if a and b or c:
            s += 1
            if s > 9:
                break
            if a:
                continue
        s += 2
    return s

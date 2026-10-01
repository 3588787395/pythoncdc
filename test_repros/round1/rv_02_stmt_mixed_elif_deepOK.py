# Source Generated with Decompyle++ (Python version)
# File: rv_02_stmt_mixed_elif_deep.pyc (Python 3.11)

def f(a, b, c, x):
    r = 0
    if x:
        if a:
            r = 1
        elif a and b or c:
            r = 2
        else:
            r = 3
    return r

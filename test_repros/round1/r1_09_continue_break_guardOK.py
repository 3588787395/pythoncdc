# Source Generated with Decompyle++ (Python version)
# File: r1_09_continue_break_guard.pyc (Python 3.11)

def f(a, b, c, xs):
    total = 0
    for x in xs:
        if (a and b or c) and x:
            continue
        total += 1
        if b or c and a:
            break
    return total

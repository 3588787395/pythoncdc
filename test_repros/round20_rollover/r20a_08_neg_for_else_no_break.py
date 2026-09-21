import os


def no_break_else(count, g, k):
    total = 0
    for x in range(count, 0, -1):
        total = total + x
        if k:
            total = total + 1
    else:
        g(total)
    g(k)

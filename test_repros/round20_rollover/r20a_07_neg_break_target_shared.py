import os


def shared_target(count, g, k):
    for x in range(count, 0, -1):
        if x == 3:
            break
    else:
        g()
    if k:
        g()
    g()

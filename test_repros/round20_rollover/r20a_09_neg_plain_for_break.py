import os


def plain_break(count, g):
    for x in range(count, 0, -1):
        if os.path.exists(str(x)):
            break
        g(x)
    g(count)

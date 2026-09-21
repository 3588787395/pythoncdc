import os


def break_then_handler(name, count, g):
    for x in range(count, 0, -1):
        if os.path.exists(name):
            break
    else:
        g(x)
    if name:
        g(1)
    else:
        g(2)
    g(3)

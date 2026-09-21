import os


def break_then_try(name, count, g):
    for x in range(count, 0, -1):
        if os.path.exists(name):
            break
    else:
        g(x)
        return
    try:
        g(x)
    except OSError:
        g(0)

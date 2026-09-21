import os


def break_in_except(count, g, h):
    for x in range(count, 0, -1):
        try:
            g(x)
        except OSError:
            h()
            break
    else:
        h()
        return
    tail(count)

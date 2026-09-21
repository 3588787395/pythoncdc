import os


def two_breaks(name, count, finish):
    for x in range(count, 0, -1):
        if os.path.exists(name):
            break
        if x == 1:
            break
    else:
        finish(x)
        return
    after(x)

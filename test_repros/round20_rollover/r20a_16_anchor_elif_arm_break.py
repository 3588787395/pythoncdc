import os


def elif_arm_break(name, count, k, g):
    for x in range(count, 0, -1):
        if k:
            g(x)
        elif os.path.exists(name):
            break
    else:
        g(x)
        return
    after(x)

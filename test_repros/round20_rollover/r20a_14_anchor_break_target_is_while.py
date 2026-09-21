import os


def break_then_while(name, count, flag, g):
    for x in range(count, 0, -1):
        if os.path.exists(name):
            break
    else:
        g(x)
        return
    while flag:
        g(1)

import os


def nested_for_else(name, count, g):
    for x in range(count, 0, -1):
        for y in range(count, 0, -1):
            if os.path.exists(name):
                break
        else:
            g(y)
            continue
        break
    else:
        g(x)
        return
    after(x)

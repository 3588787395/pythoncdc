import os


def rollover(name, count, rename, open_w):
    for x in range(count, 0, -1):
        if os.path.exists(name):
            break
    else:
        rename(name, name + '.1')
        open_w()
        return
    after(x)

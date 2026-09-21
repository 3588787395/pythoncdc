import os


def nested_if_break(name, flag, count, rename, open_w):
    for x in range(count, 0, -1):
        if flag:
            if os.path.exists(name):
                break
    else:
        rename(name, name + '.1')
        open_w()
        return
    after(x)

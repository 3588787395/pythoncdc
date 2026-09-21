import os


def target_is_next_loop(name, count, rename, open_w):
    for x in range(count, 0, -1):
        if os.path.exists(name):
            break
    else:
        rename(name, name + '.1')
        open_w()
        return
    total = 0
    for i in range(x, 0, -1):
        total = total + i
    use(total)

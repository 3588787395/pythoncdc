def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i

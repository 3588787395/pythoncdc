def f(x, items):
    if x == 1:
        items = items[1:]
    elif x == 2:
        items = items[2:]
    i = 0
    while i < len(items):
        items[i] = items[i] + 1
        i += 1
    return items

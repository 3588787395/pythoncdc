
def f(items, result):
    for x in items:
        if x > 0:
            continue
        else:
            result.append(x)
            continue
    else:
        result.append(-1)

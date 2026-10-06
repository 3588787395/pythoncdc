def b3b03_shallow(n, k):
    while n > 0:
        if n == k:
            break
        n -= 1
    else:
        return -1
    return 1


def b3b03_deep(n, k, flag):
    res = 0
    while n > 0:
        if flag:
            if n > 5:
                if n == k:
                    break
        n -= 1
    else:
        res = -1
    return res

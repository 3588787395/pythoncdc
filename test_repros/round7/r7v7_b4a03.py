def b4a03_shallow(flag):
    if flag:
        try:
            pass
        finally:
            flag = not flag
    return flag


def b4a03_deep(flag, n):
    while n > 0:
        if flag:
            try:
                pass
            finally:
                flag = not flag
        n -= 1
    return flag

def b4a06_shallow(a, b):
    try:
        a + b
    finally:
        a = b
    return a


def b4a06_deep(a, b, flag):
    if flag:
        if a > 0:
            try:
                a + b
            finally:
                a = b
    return a

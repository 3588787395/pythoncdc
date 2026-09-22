def r43d_02_while_and_after_guard(data, done):
    n = len(data)
    if n == 0:
        return 0
    while not done and n > 0:
        n = n - 1
    return n


def r43d_03_while_or_after_guard(a, b):
    if a == 0:
        return 0
    while a > 0 or b > 0:
        a = a - 1
        b = b - 1
    return a

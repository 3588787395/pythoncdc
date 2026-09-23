def w(a, b, k, n):
    if a > b:
        n += 1
    elif a > b or a < k and b < k:
        return 1
    return n

def w(a, b, k, n):
    x = a > b or a < k and b < k
    if x:
        return 1
    return n

def f(high, low, n1):
    dmp = sum((high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > 0 and high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] else 0 for i in range(1, n1 + 1)))
    return dmp

def f(high, low, n1):
    a = high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > 0 and high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] else 0
    return a

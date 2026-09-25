def v1(high, low, n):
    return sum((high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > 0 and low[-(i + 1)] - low[-i] > 0 else 0 for i in range(1, n + 1)))
def v2(high, low, i):
    a = high[-i] - high[-(i + 1)]
    b = low[-(i + 1)] - low[-i]
    return a if a > 0 and b > 0 else 0
def v3(high, low, n):
    out = []
    for i in range(n):
        out.append(1 if i > 0 and high[i] > low[i] else 2)
    return out
def v4(high, low, n):
    total = 0
    for i in range(n):
        total = total + (high[i] if high[i] > 0 and low[i] > 0 else 0)
    return total

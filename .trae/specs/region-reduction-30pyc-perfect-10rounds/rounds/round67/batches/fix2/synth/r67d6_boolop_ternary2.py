def v5(high, low, n):
    for i in range(n):
        yield high[i] if high[i] > 0 and low[i] > 0 else 0
def v6(high, low, n):
    return [high[i] - high[i - 1] if high[i] - high[i - 1] > 0 and low[i - 1] - low[i] > 0 else 0 for i in range(1, n + 1)]
def v7(high, low, n):
    return sum((high[i] if high[i] > 0 and low[i] > 0 else 0 for i in range(n)))
def v8(high, low, n):
    return sum((high[i] - high[i - 1] if high[i] - high[i - 1] > 0 and low[i] > 0 else 0 for i in range(1, n)))
def v9(high, low, n):
    return sum((high[i] if high[i] > 0 and high[i - 1] > 0 else low[i] for i in range(1, n)))

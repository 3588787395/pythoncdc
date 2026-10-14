# Source Generated with Decompyle++ (Python version)
# File: r3_c11_genexpr_three_conjuncts.pyc (Python 3.11)

def f(high, low, n1):
    return sum((high[-i] - high[-(i + 1)] if low[-(i + 1)] - low[-i] > 0 else 0 for i in range(1, n1 + 1)))

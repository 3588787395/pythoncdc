# Source Generated with Decompyle++ (Python version)
# File: r3_c10_genexpr_or_test_ternary.pyc (Python 3.11)

def f(high, low, n1):
    return sum((high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] if not high[-i] - high[-(i + 1)] > 0 else 0 for i in range(1, n1 + 1)))

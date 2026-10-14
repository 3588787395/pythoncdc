# Source Generated with Decompyle++ (Python version)
# File: r3_c05_max_default_genexpr_andtest.pyc (Python 3.11)

def f(high, low, n1):
    return max((high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] else 0 for i in range(1, n1 + 1)), default=0)

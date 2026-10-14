# Source Generated with Decompyle++ (Python version)
# File: r3_c02_genexpr_andtest_ternary_assign.pyc (Python 3.11)

def f(high, low, n1):
    dmp = sum((high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] else 0 for i in range(1, n1 + 1)))
    return dmp

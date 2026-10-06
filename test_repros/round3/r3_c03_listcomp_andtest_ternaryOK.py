# Source Generated with Decompyle++ (Python version)
# File: r3_c03_listcomp_andtest_ternary.pyc (Python 3.11)

out = [high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] else 0 for i in range(1, 9)]

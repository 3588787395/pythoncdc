# Source Generated with Decompyle++ (Python version)
# File: r3_c09_lambda_host_andtest.pyc (Python 3.11)

fn = lambda high, low, n1: sum((high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] else 0 for i in range(1, n1 + 1)))

# Source Generated with Decompyle++ (Python version)
# File: r3_c08_loop_try_host_andtest.pyc (Python 3.11)

def f(high, low, n1):
    for i in range(1, n1 + 1):
        try:
            acc = acc + (high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > 0 and high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] else 0)
        except TypeError:
            pass
    return acc

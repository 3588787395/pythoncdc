# Source Generated with Decompyle++ (Python version)
# File: r3_c04_method_host_genexpr_andtest.pyc (Python 3.11)

class C:
    def m(self, high, low, n1):
        return sum((high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] else 0 for i in range(1, n1 + 1)))

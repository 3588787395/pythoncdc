# Source Generated with Decompyle++ (Python version)
# File: r6_g6_genexpr_and_spec.pyc (Python 3.11)

def r6_g6_genexpr_and_spec(high, low, i, rng):
    return sum(((high[i] - low[i - 1]) / 2 for i in rng if high[i] - low[i - 1] > 0 and low[i] - high[i] < 0))

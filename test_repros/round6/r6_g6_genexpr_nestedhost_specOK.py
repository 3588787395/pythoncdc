# Source Generated with Decompyle++ (Python version)
# File: r6_g6_genexpr_nestedhost_spec.pyc (Python 3.11)

def r6_g6_genexpr_nestedhost_spec(high, low, rng):
    total = 0
    for j in rng:
        total += sum(((high[j] - low[j - 1]) / 2 for j2 in rng if high[j] - low[j - 1] > 0 and low[j] - high[j] < 0))
    return total

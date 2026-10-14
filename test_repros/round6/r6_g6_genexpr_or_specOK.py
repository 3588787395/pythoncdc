# Source Generated with Decompyle++ (Python version)
# File: r6_g6_genexpr_or_spec.pyc (Python 3.11)

def r6_g6_genexpr_or_spec(high, low, i, rng):
    return [x for x in rng if high[x] > 0 or low[x] < 0]

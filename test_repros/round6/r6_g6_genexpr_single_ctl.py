def r6_g6_genexpr_single_ctl(high, low, i, rng):
    return sum((high[i] - low[i - 1]) / 2 for i in rng
               if (high[i] - low[i - 1]) > 0)

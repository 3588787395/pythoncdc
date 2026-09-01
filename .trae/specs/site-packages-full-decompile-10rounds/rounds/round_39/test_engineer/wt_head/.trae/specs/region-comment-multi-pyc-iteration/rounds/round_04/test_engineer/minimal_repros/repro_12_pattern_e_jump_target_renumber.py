# repro_12: Pattern E — jump-target renumbering (forward jump offset mismatch)
# Pattern: E-JUMP-TARGET renumber (conditional jump offset renumbered; structural NOP drop)
# Original failing function: get_kline_by_date_ndarray / get_kline_by_date_new (klinedata.pyc)
# Ported from R03 repro_14 (true_diffs=4, jump_diffs=0)
# Expected: forward conditional jump -> POP_JUMP_FORWARD_IF_TRUE with consistent target
# Actual (pre-fix): orig index 47 POP_JUMP_FORWARD_IF_TRUE arg=656 vs decomp arg=308
def f(x, y, z):
    if x is not None and y is not None:
        if z:
            return x
        return y
    return z
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 4, jump_diffs: 0
# first_diff: index=2 orig=POP_JUMP_FORWARD_IF_NONE 22 vs decomp=POP_JUMP_FORWARD_IF_NONE 18

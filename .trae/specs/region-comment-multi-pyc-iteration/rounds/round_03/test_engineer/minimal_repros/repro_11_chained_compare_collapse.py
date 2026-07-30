# repro_11: SWAP -> COMPARE_OP (chained comparison in if/elif collapse)
# Pattern: CHAINED-COMPARE collapse (SWAP for chained compare replaced by COMPARE_OP)
# Original failing function: kline_datetime_list (klinedata.pyc, true_diffs=208)
# Expected: a < b < c -> chained compare with SWAP/COMPARE_OP sequence
# Actual diff summary: orig index 148 SWAP 2 vs decomp COMPARE_OP '>'
# Expected vs actual bytecode diff: index 148 orig_op=SWAP decomp_op=COMPARE_OP
def f(a, b, c, d):
    if a < b < c:
        return a
    elif a > b > c:
        return c
    elif a <= b <= d:
        return b
    return d
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 16, jump_diffs: 0
# first_diff: index=29 orig=LOAD_FAST 'a' vs decomp=LOAD_FAST 'd'

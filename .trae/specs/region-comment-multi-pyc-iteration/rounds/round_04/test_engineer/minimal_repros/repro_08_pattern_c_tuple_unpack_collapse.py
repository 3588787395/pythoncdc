# repro_08: Pattern C — tuple unpack collapse (UNPACK_SEQUENCE -> STORE_FAST)
# Pattern: C-TUPLE-UNPACK collapse (UNPACK_SEQUENCE dropped, one target lost)
# Original failing function: get_kline_by_count_new (klinedata.pyc, true_diffs=507)
# Ported from R03 repro_08 (true_diffs=3, jump_diffs=0)
# Expected: a, b = func() -> CALL; UNPACK_SEQUENCE 2; STORE_FAST a; STORE_FAST b
# Actual (pre-fix): orig index 14 UNPACK_SEQUENCE 2 vs decomp STORE_FAST 'start_000300'
def g(count, query_date):
    return count, query_date


def f(count, query_date):
    start_000300, end_000300 = g(count, query_date)
    if start_000300 is None or end_000300 is None:
        return None
    return start_000300 + end_000300
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 3, jump_diffs: 0
# first_diff: index=10 orig=POP_JUMP_FORWARD_IF_NONE 48 vs decomp=POP_JUMP_FORWARD_IF_NONE 62

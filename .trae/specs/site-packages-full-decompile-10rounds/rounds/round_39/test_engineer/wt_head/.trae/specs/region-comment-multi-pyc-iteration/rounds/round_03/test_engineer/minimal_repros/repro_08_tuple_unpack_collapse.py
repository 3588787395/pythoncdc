# repro_08: tuple unpack collapse (UNPACK_SEQUENCE -> STORE_FAST)
# Pattern: TUPLE-UNPACK region collapse (UNPACK_SEQUENCE dropped, one target lost)
# Original failing function: get_kline_by_count_new (klinedata.pyc, true_diffs=507)
# Expected: a, b = func() -> CALL; UNPACK_SEQUENCE 2; STORE_FAST a; STORE_FAST b
# Actual diff summary: orig index 14 UNPACK_SEQUENCE 2 vs decomp STORE_FAST 'start_000300'
# Expected vs actual bytecode diff: index 14 orig_op=UNPACK_SEQUENCE decomp_op=STORE_FAST
def g(count, query_date):
    return count, query_date


def f(count, query_date):
    start_000300, end_000300 = g(count, query_date)
    if start_000300 is None or end_000300 is None:
        return None
    return start_000300 + end_000300

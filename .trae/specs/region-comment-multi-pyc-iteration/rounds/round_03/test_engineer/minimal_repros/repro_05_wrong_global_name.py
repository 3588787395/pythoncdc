# repro_05: wrong global name in loop + if/elif (range->other global)
# Pattern: WRONG-GLOBAL-NAME resolution (builtin 'range' replaced by unrelated module global)
# Original failing function: get_all_real_minute_kline (klinedata.pyc, true_diffs=191)
# Expected: for i in range(n) -> LOAD_GLOBAL range
# Actual diff summary: orig index 82 LOAD_GLOBAL 'range' vs decomp LOAD_GLOBAL 'system_log'
# Expected vs actual bytecode diff: index 82 orig_arg='range' decomp_arg='system_log'
import logging
system_log = logging.getLogger('x')


def f(n, items, fields):
    out = []
    for i in range(n):
        if fields is None:
            out.append(items[i])
        elif fields == 'close':
            out.append(items[i])
        system_log.info(i)
    return out
# --- verification result ---
# verdict: NO-DEFECT
# mismatch_fn: None
# true_diffs: 0, jump_diffs: 0
# 

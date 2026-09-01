# repro_02: Pattern A — compound `and` BoolOp cond in try-body if -> try/except FULL COLLAPSE
# Pattern: A-CONTROL-FLOW region collapse (BoolOp `and` cond in try-body if drops try/except entirely)
# Original failing function: get_history_common (klinedata.pyc, true_diffs=367)
# Isolated via _tmp_v11.py (FULL COLLAPSE: try/except dropped, if-body becomes pass, trailing return becomes else)
# Expected: try: if x is None and y is None: return z / except: return d / return y
# Actual (pre-fix): if x is None and y is None: pass / else: return y  (try/except DROPPED)
def f(x, y, z, d):
    try:
        if x is None and y is None:
            return z
    except BaseException:
        return d
    return y
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 22, jump_diffs: 1
# first_diff: index=1 orig=NOP None vs decomp=LOAD_FAST 'x'

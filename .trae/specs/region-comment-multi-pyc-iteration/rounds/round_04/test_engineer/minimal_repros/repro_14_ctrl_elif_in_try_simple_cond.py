# repro_14: CONTROL — elif + try + trailing return (simple cond, NO BoolOp) -> CORRECT
# Pattern: control (no defect expected; isolates that BoolOp cond is the trigger, not elif+try+trailing)
# Isolated via _tmp_v7.py (CORRECT: try/except preserved, elif chain correct)
# Expected: try: if x is None: return z / elif x==0: return z+1 / except: return d / return y
# Actual (pre-fix): correct (no collapse without compound BoolOp cond)
def f(x, y, z, d):
    try:
        if x is None:
            return z
        elif x == 0:
            return z + 1
    except BaseException:
        return d
    return y
# --- verification result ---
# verdict: NO-DEFECT (control: simple cond + elif + try does not trigger collapse)
# mismatch_fn: None
# true_diffs: 0, jump_diffs: 0

# repro_15: CONTROL — compound `or` + elif but NO try -> CORRECT
# Pattern: control (no defect expected; isolates that try-context is the trigger, not BoolOp+elif alone)
# Isolated via _tmp_v12.py (CORRECT: if/elif chain correct without try/except wrapper)
# Expected: if x is None or y is None: return z / elif x==0: return z+1 / return y
# Actual (pre-fix): correct (no collapse without try/except wrapper)
def f(x, y, z, d):
    if x is None or y is None:
        return z
    elif x == 0:
        return z + 1
    return y
# --- verification result ---
# verdict: NO-DEFECT (control: BoolOp + elif without try does not trigger collapse)
# mismatch_fn: None
# true_diffs: 0, jump_diffs: 0

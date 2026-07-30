# repro_13: CONTROL — simple if+return in try (single cond, NO BoolOp, NO elif) -> CORRECT
# Pattern: control (no defect expected; isolates that BoolOp cond is the trigger)
# Isolated via _tmp_v1.py (CORRECT: try/except preserved, condition correct)
# Expected: try: if x is None: return z / except: return y  (matches orig)
# Actual (pre-fix): correct (no collapse without compound BoolOp cond)
def f(x, y, z):
    try:
        if x is None:
            return z
    except BaseException:
        return y
# --- verification result ---
# verdict: NO-DEFECT (control: simple cond in try does not trigger collapse)
# mismatch_fn: None
# true_diffs: 0, jump_diffs: 0

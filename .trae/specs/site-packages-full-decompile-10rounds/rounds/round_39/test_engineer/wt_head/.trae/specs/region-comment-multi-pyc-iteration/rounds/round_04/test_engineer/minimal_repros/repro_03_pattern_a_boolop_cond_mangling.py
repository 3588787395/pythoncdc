# repro_03: Pattern A — compound `or` BoolOp cond in try-body if (NO elif) -> try/except preserved but condition MANGLED
# Pattern: A-CONTROL-FLOW condition mangling (BoolOp `or` first operand `x is None` -> `not x is not None`)
# Original failing function: get_kline_by_count (klinedata.pyc, POP_JUMP_FORWARD_IF_NONE -> EXTENDED_ARG)
# Isolated via _tmp_v9.py (try/except PRESERVED but condition mangled)
# Expected: try: if x is None or y is None: return z / except: return d / return y
# Actual (pre-fix): try: if not x is not None or y is None: return z / except: return d / return y
def f(x, y, z, d):
    try:
        if x is None or y is None:
            return z
    except BaseException:
        return d
    return y
# --- verification result ---
# verdict: NO-DEFECT
# mismatch_fn: None
# true_diffs: 0, jump_diffs: 0
# note: source-level condition differs ('not x is not None') but peephole folds back to IS_OP, bytecode identical

# repro_07: return value lost in try/except if/elif (R01 repro_10 residual)
# Pattern: RETURN_VALUE -> POP_TOP (return value dropped inside try/except if/elif)
# Original failing function: get_kline_by_date_one (klinedata.pyc, true_diffs=126)
# Expected: try: if cond: return val -> RETURN_VALUE; except: handler
# Actual diff summary: orig index 44 RETURN_VALUE vs decomp POP_TOP (returns None instead of val)
# Expected vs actual bytecode diff: index 44 orig_op=RETURN_VALUE decomp_op=POP_TOP
EMPTY = {}


def f(fields, asset, default):
    history = default
    try:
        if asset is None:
            history = EMPTY if fields is None else EMPTY[fields]
            return history
        elif len(asset) == 0:
            history = EMPTY if fields is None else EMPTY[fields]
            return history
    except BaseException:
        history = EMPTY if fields is None else EMPTY[fields]
    return history
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 32, jump_diffs: 11
# first_diff: index=5 orig=POP_JUMP_FORWARD_IF_NOT_NONE 60 vs decomp=POP_JUMP_FORWARD_IF_NOT_NONE 64

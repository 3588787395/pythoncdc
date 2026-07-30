# repro_07: Pattern C — return value lost in try/except if/elif (R01 repro_10 residual)
# Pattern: C-RETURN-VALUE-LOSS (RETURN_VALUE -> POP_TOP; return value dropped inside try/except if/elif)
# Original failing function: get_kline_by_date_one (klinedata.pyc, true_diffs=126)
# Ported from R03 repro_07 (true_diffs=32, jump_diffs=11)
# Expected: try: if cond: return val -> RETURN_VALUE; except: handler
# Actual (pre-fix): orig index 44 RETURN_VALUE vs decomp POP_TOP (returns None instead of val)
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

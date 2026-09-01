# repro_04: Pattern A — compound None-check `or` + 3-branch elif + try/except + return (POP_JUMP->EXTENDED_ARG)
# Pattern: A-CONTROL-FLOW region collapse (compound None-check jump replaced by EXTENDED_ARG)
# Original failing function: get_kline_by_count / get_price_common (klinedata.pyc)
# Ported from R03 repro_06 (true_diffs=35, jump_diffs=6, first_diff idx 1 NOP->LOAD_FAST 'x')
# Expected: try: if x is None or y is None: return z / elif x==0 and y==0: return z+1 / elif x>y: return x / except: return default / return y
# Actual (pre-fix): try/except dropped; if/elif bodies collapse to pass; trailing return becomes else branch
def f(x, y, z, default):
    try:
        if x is None or y is None:
            return z
        elif x == 0 and y == 0:
            return z + 1
        elif x > y:
            return x
    except BaseException:
        return default
    return y
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 35, jump_diffs: 6
# first_diff: index=1 orig=NOP None vs decomp=LOAD_FAST 'x'

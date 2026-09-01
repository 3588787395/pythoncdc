# repro_05: Pattern A — major region loss: 5-branch if/elif + return in try/except (EXTENDED_ARG misaligned, 90+ instr lost)
# Pattern: A-MAJOR-REGION-LOSS (try body if/elif+return collapsed; EXTENDED_ARG misaligned)
# Original failing function: get_history_new / get_multiminute_his_data (klinedata.pyc)
# Ported from R03 repro_12 (true_diffs=22, jump_diffs=8, first_diff idx 30 LOAD_FAST 'd' -> LOAD_CONST None)
# Expected: try: if/elif/else 5-branch with return -> full conditional jump chain in try body
# Actual (pre-fix): try body collapsed; EXTENDED_ARG arg=2 -> arg=1 (90 instructions lost)
def f(mode, a, b, c, d, e):
    try:
        if mode == 1:
            return a + b
        elif mode == 2:
            return b + c
        elif mode == 3:
            return c + d
        elif mode == 4:
            return d + e
        elif mode == 5:
            return a + e
    except BaseException:
        pass
    return a
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 22, jump_diffs: 8
# first_diff: index=30 orig=LOAD_FAST 'd' vs decomp=LOAD_CONST None

# repro_12: major region loss in try/except + if/elif + return (EXTENDED_ARG offset mismatch)
# Pattern: MAJOR-REGION-LOSS (try body if/elif+return collapsed; 90+ instr lost; EXTENDED_ARG misaligned)
# Original failing function: get_history_new / get_multiminute_his_data (klinedata.pyc)
# Expected: try: if/elif/else 5-branch with return -> full conditional jump chain in try body
# Actual diff summary: orig index 65 EXTENDED_ARG arg=2 vs decomp EXTENDED_ARG arg=1 (orig=352 decomp=262)
# Expected vs actual bytecode diff: index 65 orig_arg=2 decomp_arg=1 (90 instructions lost)
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

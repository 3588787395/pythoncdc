# repro_04: global builtin len() in long if/elif chain inside try/except (global->local)
# Pattern: GLOBAL-BUILTIN->LOCAL scope (len() resolved as LOAD_FAST / wrong name in try+elif)
# Original failing function: get_pre_date (klinedata.pyc, true_diffs=117)
# Expected: 1 / len(x) * int(frequency[:-1]) -> LOAD_GLOBAL len
# Actual diff summary: orig index 34 LOAD_GLOBAL 'len' vs decomp LOAD_FAST 'frequency'
# Expected vs actual bytecode diff: index 34 orig_op=LOAD_GLOBAL orig_arg='len' decomp_op=LOAD_FAST
def f(frequency, items, default):
    multi = 1
    try:
        if frequency[-1] == 'm':
            multi = 1 / len(items) * int(frequency[:-1])
        elif frequency == '1d':
            multi = 1
        elif frequency == '5m':
            multi = 2
        elif frequency == '15m':
            multi = 3
        elif frequency == '30m':
            multi = 4
        elif frequency == '60m':
            multi = 5
        return multi
    except BaseException:
        return default
# --- verification result ---
# verdict: NO-DEFECT
# mismatch_fn: None
# true_diffs: 0, jump_diffs: 0
# 

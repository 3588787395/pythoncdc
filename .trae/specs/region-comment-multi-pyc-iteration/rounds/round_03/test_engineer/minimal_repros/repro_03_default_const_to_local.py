# repro_03: constant comparison in `if not a > b` + elif (const->local scope)
# Pattern: CONSTANT->LOCAL scope (default/literal const in comparison turned into LOAD_FAST)
# Original failing function: _all_bars_of_cache (klinedata.pyc, true_diffs=187)
# Expected: if not start_date > end_date: elif start_date < '20050101' -> LOAD_CONST '20050101'
# Actual diff summary: orig index 29 LOAD_CONST '20050101' vs decomp LOAD_FAST 'start_date'
# Expected vs actual bytecode diff: index 29 orig_arg='20050101' decomp_arg='start_date'
def f(start_date, end_date):
    if not start_date > end_date:
        if start_date < '20050101' and end_date < '20050101':
            return []
        elif start_date < '20050101' <= end_date:
            start_date = '20050101'
    return start_date, end_date
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 0, jump_diffs: 1
# first_diff: index=4 orig=POP_JUMP_FORWARD_IF_TRUE 78 vs decomp=POP_JUMP_FORWARD_IF_TRUE 26

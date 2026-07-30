# repro_01: DictComp key/value swap
# Pattern: DICT-COMPREHENSION key/value collapse
# Original failing function: <dictcomp> (klinedata.pyc)
# Expected: {date: idx for idx, date in pairs}  -> LOAD_FAST date; LOAD_FAST idx; MAP_ADD
# Actual diff summary: orig index 7 LOAD_FAST 'date' vs decomp LOAD_FAST 'idx'
#   (decompiler swaps key/value, emitting idx->idx map; loses date->idx mapping)
# Expected vs actual bytecode diff: index 7 orig_arg='date' decomp_arg='idx' (true_diffs=1)
def f(pairs):
    return {date: idx for idx, date in pairs}
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: <dictcomp>
# true_diffs: 1, jump_diffs: 0
# first_diff: index=7 orig=LOAD_FAST 'date' vs decomp=LOAD_FAST 'idx'

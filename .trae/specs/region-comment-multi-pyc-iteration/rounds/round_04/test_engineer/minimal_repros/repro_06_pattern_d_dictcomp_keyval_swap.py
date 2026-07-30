# repro_06: Pattern D — dictcomp key/value swap (R03 fixed; control for regression)
# Pattern: DICT-COMPREHENSION key/value collapse
# Original failing function: <dictcomp> (klinedata.pyc)
# Ported from R03 repro_01 (R03 fixed via _find_dict_kv_split_point; should be OK after R03)
# Expected: {date: idx for idx, date in pairs}  -> LOAD_FAST date; LOAD_FAST idx; MAP_ADD
# Actual (post-R03): correct (key=date, value=idx)
def f(pairs):
    return {date: idx for idx, date in pairs}
# --- verification result ---
# verdict: NO-DEFECT (R03 fix holds; regression control)
# mismatch_fn: None
# true_diffs: 0, jump_diffs: 0

# repro_02: Module-level if/elif + try/except region collapse
# Pattern: MODULE-LEVEL conditional collapse (NOP vs LOAD_CONST) compounded by try/except
# Original failing function: <module> (klinedata.pyc, true_diffs=189)
# Expected: module-level if/elif/else with try/except emits full conditional + handler
# Actual diff summary: orig index 344 NOP vs decomp LOAD_CONST tuple (189 true_diffs)
# Expected vs actual bytecode diff: index 344 orig_op=NOP decomp_op=LOAD_CONST
import sys
_v = sys.version_info[0]
data = {}
try:
    if _v == 3:
        data['a'] = 1
    elif _v == 5:
        data['a'] = 2
    else:
        data['a'] = 3
except Exception:
    data['a'] = 0
# --- verification result ---
# verdict: NO-DEFECT
# mismatch_fn: None
# true_diffs: 0, jump_diffs: 0
# 

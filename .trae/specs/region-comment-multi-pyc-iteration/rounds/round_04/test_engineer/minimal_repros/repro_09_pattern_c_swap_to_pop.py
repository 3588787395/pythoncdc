# repro_09: Pattern C — SWAP -> POP_TOP (tuple swap value dropped)
# Pattern: C-SWAP collapse (tuple swap a,b=b,a loses one operand -> POP_TOP)
# Original failing function: np_tp_pd (klinedata.pyc, true_diffs=111)
# Ported from R03 repro_10 (true_diffs=8, jump_diffs=1)
# Expected: a, b = b, a  -> SWAP 2
# Actual (pre-fix): orig index 56 SWAP 2 vs decomp POP_TOP
def f(a, b):
    if a > b:
        a, b = b, a
    return a, b
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 8, jump_diffs: 1
# first_diff: index=5 orig=LOAD_FAST 'b' vs decomp=LOAD_FAST 'a'

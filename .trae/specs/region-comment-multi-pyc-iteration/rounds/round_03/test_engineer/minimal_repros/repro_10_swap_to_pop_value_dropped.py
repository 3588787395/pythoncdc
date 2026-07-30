# repro_10: SWAP -> POP_TOP (tuple swap value dropped)
# Pattern: SWAP collapse (tuple swap a,b=b,a loses one operand -> POP_TOP)
# Original failing function: np_tp_pd (klinedata.pyc, true_diffs=111)
# Expected: a, b = b, a  -> SWAP 2
# Actual diff summary: orig index 56 SWAP 2 vs decomp POP_TOP
# Expected vs actual bytecode diff: index 56 orig_op=SWAP decomp_op=POP_TOP
def f(a, b):
    if a > b:
        a, b = b, a
    return a, b

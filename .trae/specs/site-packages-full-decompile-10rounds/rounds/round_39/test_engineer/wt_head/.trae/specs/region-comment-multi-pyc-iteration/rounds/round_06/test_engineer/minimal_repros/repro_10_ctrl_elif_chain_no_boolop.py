# Pattern: elif chain without BoolOp (cross-ref Pattern F from R01)
# Pattern F: elif BoolOp chain split to nested if (R01 residual)
# This pyc has if/else (not elif chain), so F does not trigger.
# Expected: if a: ... elif b: ... else: ...
# Actual: same (pyc 100% match, NO-DEFECT control — confirms elif without BoolOp is fine)
def elif_chain(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    else:
        return 'c'
# NO-DEFECT

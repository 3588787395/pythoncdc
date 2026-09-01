# Pattern: simple if/else without BoolOp (cross-ref Pattern A2 from R04)
# Pattern A2: simple condition + try-body if + multi-branch + return collapse (no BoolOp)
# This pyc has NO try blocks, so A2 does not trigger.
# Expected: if cond: return a else: return b
# Actual: same (pyc 100% match, NO-DEFECT control — confirms A2 requires try context)
def simple_if_else(x):
    if x:
        return x
    else:
        return None
# NO-DEFECT

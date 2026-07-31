# Pattern: CTRL - simple if/else without try (cross-validate Pattern A2 needs try)
# Function: control group confirming A2 does not trigger without try context
# Expected: if x > 0: return x else: return -x
# Actual: same (pyc 100% match, NO-DEFECT control)
def abs_val(x):
    if x > 0:
        return x
    else:
        return -x
# NO-DEFECT

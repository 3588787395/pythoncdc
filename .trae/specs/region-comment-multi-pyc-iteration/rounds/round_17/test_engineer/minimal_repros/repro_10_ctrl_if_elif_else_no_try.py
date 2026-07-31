# Pattern: CTRL - simple if/elif/else without try (cross-validate Pattern A2 needs try context)
# Function: control group confirming if/elif/else without try + no BoolOp is fine
# Expected: if x=='a': ... elif x=='b': ... else: ...
# Actual: same (pyc 100% match, NO-DEFECT control)
def classify(x, amt):
    if x == 'a':
        amt = int(amt / 10) * 10
    elif x == 'b':
        amt = int(amt / 100) * 100
    else:
        amt = int(amt)
    return amt
# NO-DEFECT

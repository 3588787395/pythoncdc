# Pattern: CTRL - elif chain without BoolOp (cross-validate Pattern F needs BoolOp)
# Function: control group confirming elif chain without BoolOp is fine
# Expected: if x==1: ... elif x==2: ... else: ...
# Actual: same (pyc 100% match, NO-DEFECT control)
def classify(x):
    if x == 1:
        return 'one'
    elif x == 2:
        return 'two'
    else:
        return 'many'
# NO-DEFECT

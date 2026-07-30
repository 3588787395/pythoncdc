# Pattern M variant: @deco(1, 2) multiple positional args
# Expected: @deco(1, 2)  Actual: may collapse or lose args
def deco(a, b):
    def inner(f):
        return f
    return inner

class C:
    @deco(1, 2)
    def m(self, x):
        return x
# verification: DEFECT-REPRO / NO-DEFECT

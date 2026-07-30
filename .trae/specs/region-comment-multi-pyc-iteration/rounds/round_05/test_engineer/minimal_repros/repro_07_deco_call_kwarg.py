# Pattern M variant: @deco(key=val) keyword arg
# Expected: @deco(n=5)  Actual: may collapse or lose kwarg
def deco(n=0):
    def inner(f):
        return f
    return inner

class C:
    @deco(n=5)
    def m(self, x):
        return x
# verification: DEFECT-REPRO / NO-DEFECT

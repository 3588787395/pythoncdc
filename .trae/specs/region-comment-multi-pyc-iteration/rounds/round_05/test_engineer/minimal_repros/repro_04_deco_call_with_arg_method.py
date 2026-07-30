# Pattern M variant: @deco(arg) on class method — decorator called with positional arg
# Expected: @deco(5)  Actual: may collapse to @deco or lose arg
def deco(n):
    def inner(f):
        return f
    return inner

class C:
    @deco(5)
    def m(self, x):
        return x
# verification: DEFECT-REPRO / NO-DEFECT

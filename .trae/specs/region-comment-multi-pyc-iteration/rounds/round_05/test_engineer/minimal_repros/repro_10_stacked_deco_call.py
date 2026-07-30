# Pattern M variant: stacked @deco1() @deco2 — one with call, one without
# Expected: @deco1() then @deco2  Actual: may collapse deco1() to deco1
def deco1():
    def inner(f):
        return f
    return inner

def deco2(f):
    return f

class C:
    @deco1()
    @deco2
    def m(self, x):
        return x
# verification: DEFECT-REPRO / NO-DEFECT

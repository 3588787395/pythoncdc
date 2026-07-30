# Pattern M variant: two stacked @deco() both with calls
# Expected: @deco1() @deco2()  Actual: may collapse one or both
def deco1():
    def inner(f):
        return f
    return inner

def deco2():
    def inner(f):
        return f
    return inner

class C:
    @deco1()
    @deco2()
    def m(self, x):
        return x
# verification: DEFECT-REPRO / NO-DEFECT

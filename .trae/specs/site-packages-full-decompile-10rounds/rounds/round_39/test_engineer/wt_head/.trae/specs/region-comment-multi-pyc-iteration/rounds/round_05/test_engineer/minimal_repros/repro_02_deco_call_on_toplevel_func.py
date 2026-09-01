# Pattern M: decorator call collapse — @deco() on top-level function
# Original failing function: BaseStorage.__new__ (base_storage.pyc, class body)
# Expected: @deco()  Actual: @deco (decorator invocation CALL dropped)
def deco():
    def inner(f):
        return f
    return inner

@deco()
def f(x):
    return x
# verification: DEFECT-REPRO / NO-DEFECT

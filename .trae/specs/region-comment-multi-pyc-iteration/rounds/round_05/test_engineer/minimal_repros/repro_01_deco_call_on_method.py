# Pattern M: decorator call collapse — @deco() on class method
# Original failing function: BaseStorage.__new__ (base_storage.pyc)
# Expected: @deco()  Actual: @deco (PUSH_NULL/PRECALL/CALL dropped, lru_cache()->lru_cache)
def deco():
    def inner(f):
        return f
    return inner

class C:
    @deco()
    def m(self, x):
        return x
# verification: DEFECT-REPRO / NO-DEFECT

# Pattern M variant: @mod.deco() attribute decorator with call
# Expected: @mod.deco()  Actual: may collapse to @mod.deco
class mod:
    @staticmethod
    def deco():
        def inner(f):
            return f
        return inner

class C:
    @mod.deco()
    def m(self, x):
        return x
# verification: DEFECT-REPRO / NO-DEFECT

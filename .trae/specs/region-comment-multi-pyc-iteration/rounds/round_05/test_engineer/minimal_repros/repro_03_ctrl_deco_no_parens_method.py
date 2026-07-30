# CONTROL: @deco (no parens) on class method — should be NO-DEFECT
# Isolates that the bug is specifically the () call, not the decorator itself.
def deco(f):
    return f

class C:
    @deco
    def m(self, x):
        return x
# verification: DEFECT-REPRO / NO-DEFECT

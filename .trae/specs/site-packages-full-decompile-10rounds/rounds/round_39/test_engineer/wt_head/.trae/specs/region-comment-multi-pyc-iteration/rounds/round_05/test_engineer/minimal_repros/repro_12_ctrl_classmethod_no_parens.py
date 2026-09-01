# CONTROL: @classmethod (builtin, no parens) on method — should be NO-DEFECT
# Isolates that builtins without parens are unaffected.
class C:
    @classmethod
    def m(cls, x):
        return x
    @staticmethod
    def s(x):
        return x
# verification: DEFECT-REPRO / NO-DEFECT

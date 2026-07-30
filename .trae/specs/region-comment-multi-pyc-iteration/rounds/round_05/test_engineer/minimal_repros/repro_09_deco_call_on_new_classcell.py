# Pattern M: @deco() on __new__ with classcell closure — close to real BaseStorage
# Expected: @deco() preserved  Actual: @deco (CALL dropped), classcell offsets shift
def deco():
    def inner(f):
        return f
    return inner

class C(object):
    @deco()
    def __new__(cls, path):
        return super(C, cls).__new__(cls)
# verification: DEFECT-REPRO / NO-DEFECT

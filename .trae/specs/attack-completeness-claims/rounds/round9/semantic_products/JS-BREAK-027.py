# Source Generated with Decompyle++ (Python version)
# File: c13_class_misc.pyc (Python 3.11)

"""c13: class-level del/assert/raise/pass/Expr statements."""
class CMisc:
    TMP = 1
    del TMP
    KEEP = 2
    assert KEEP
    def boom(self):
        for i in range(2):
            if i > 0:
                while 1:
                    if i:
                        break
    print = staticmethod(print)

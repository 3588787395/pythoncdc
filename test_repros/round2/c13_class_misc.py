"""c13: class-level del/assert/raise/pass/Expr statements."""
class CMisc:
    TMP = 1
    del TMP
    KEEP = 2
    assert KEEP

    def boom(self):
        if 0:
            raise ValueError('x')
        for i in range(2):
            if i > 0:
                while True:
                    if i:
                        break
                    else:
                        continue
        pass
        return None
    print = staticmethod(print)

# Source Generated with Decompyle++ (Python version)
# File: rvC_v3.pyc (Python 3.11)

class _Ctx:
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
    def touch(self):
        return 1
def guarded(res, items):
    kept = []
    with _Ctx():
        try:
            for x in items:
                if x > 0:
                    kept.append(x)
        finally:
            pass
        res.touch()
    if kept:
        kept.append(None)
    return kept

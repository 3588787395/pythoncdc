# Source Generated with Decompyle++ (Python version)
# File: c03_class_for.pyc (Python 3.11)

__doc__ = 'c03: class-level for loop.'
class CFor:
    REG = []
    for _n in range(3):
        REG.append(_n)
        while _n and _n:
            _n -= 1
    NAMES = dict(((m, len(m)) for m in ('a', 'bb')))
    def total(self):
        t = 0
        for v in self.REG:
            t += v
        return t

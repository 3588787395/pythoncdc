"""c03: class-level for loop."""
class CFor:
    REG = []
    for _n in range(3):
        REG.append(_n)
        if _n:
            while _n:
                _n -= 1
    NAMES = dict((m, len(m)) for m in ('a', 'bb'))

    def total(self):
        t = 0
        for v in self.REG:
            t += v
        return t

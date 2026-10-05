# Source Generated with Decompyle++ (Python version)
# File: c04_class_try.pyc (Python 3.11)

__doc__ = 'c04: class-level try/except/else/finally and nested try.'
class CTry:
    try:
        VAL = int('3')
    except ValueError:
        VAL = -1
    else:
        EXTRA = VAL + 1
    finally:
        TAG = 'done'
    def show(self):
        return (self.VAL, self.TAG)
class CTryFin:
    try:
        BASE = 10
    finally:
        UNIT = 'fin'
    def base(self):
        return self.BASE
class CTryNest:
    try:
        try:
            try:
                DEEP = 1
            finally:
                MID = 3
        except ValueError:
            DEEP = 2
        except NameError:
            DEEP = 4
    finally:
        LEAF = 6

"""c04: class-level try/except/else/finally and nested try."""
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
            DEEP = 1
        except ValueError:
            DEEP = 2
        finally:
            MID = 3
    except NameError:
        DEEP = 4
    else:
        OUT = 5
    finally:
        LEAF = 6

def _host():
    pass

class Outer:
    def m(self, v):
        if v:
            return 1
        elif not v:
            return 2
        return 3

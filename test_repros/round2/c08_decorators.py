"""c08: class and method decorators with args."""
DEC = lambda *a, **k: (lambda f: f)


@DEC('cls', flag=1)
class CDeco:
    ATTR = 1

    @staticmethod
    @DEC('s')
    def st(v):
        return v

    @classmethod
    def cm(cls):
        return cls.ATTR

    @property
    def p(self):
        return self.ATTR

    @DEC('m', key=[1, {'k': (2, 3)}])
    def m(self):
        return 2

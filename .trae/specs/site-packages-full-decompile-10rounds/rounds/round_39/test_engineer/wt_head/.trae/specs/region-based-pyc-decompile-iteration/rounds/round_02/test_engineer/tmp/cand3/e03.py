def f(self, k):
    r = self.get(k, None)
    if r is not None:
        return r
    try:
        return Position(self.a.b[k])
    except (AttributeError, KeyError):
        raise KeyError(k)

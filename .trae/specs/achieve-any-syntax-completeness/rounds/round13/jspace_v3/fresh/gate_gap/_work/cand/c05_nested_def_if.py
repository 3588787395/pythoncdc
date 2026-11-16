def _host():
    pass

def outer(n):
    def inner(v):
        if v > 0:
            if v > 1:
                return v * 2
            elif v == 1:
                return 10
        elif v == 0:
            return 0
        return -1
    return inner(n)

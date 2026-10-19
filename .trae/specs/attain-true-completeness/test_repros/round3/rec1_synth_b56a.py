def s_b56a(x, y):
    def inner(v):
        return v + 1
    return inner(x) + (y or 0)

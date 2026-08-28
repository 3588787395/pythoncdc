def f(a):
    b = a if a is not None else g()
    return b

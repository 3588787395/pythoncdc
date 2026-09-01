# R20 repro_10: kwonly 无默认值（required kwonly）
def f(a, *, kw1):
    return a, kw1


result = f(1, kw1=2)

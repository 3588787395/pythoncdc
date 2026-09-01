# R20 repro_03: 纯 kwonly 参数（无位置参数、无 vararg）
def f(*, kw1, kw2=5):
    return kw1 + kw2


result = f(kw1=1)

# R20 repro_04: 位置参数 + kwonly（无 vararg）
def f(a, *, kw1='x'):
    return a + kw1


result = f(1, kw1='z')

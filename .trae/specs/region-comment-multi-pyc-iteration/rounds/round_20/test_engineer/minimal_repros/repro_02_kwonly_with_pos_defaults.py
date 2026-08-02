# R20 repro_02: 位置参数(含默认值) + *vararg + kwonly 默认值
def f(a, b=1, *args, kw1='x', kw2=None):
    return a, b, args, kw1, kw2


result = f(10, kw1='y')

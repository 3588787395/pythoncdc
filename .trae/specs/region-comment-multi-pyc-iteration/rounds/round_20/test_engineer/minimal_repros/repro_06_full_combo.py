# R20 repro_06: 完整组合 - pos + pos-default + *vararg + kwonly(无默认) + kwonly(有默认) + **kwarg
def f(a, b, *args, kw1, kw2='z', **kwargs):
    return a, b, args, kw1, kw2, kwargs


result = f(1, 2, 3, 4, kw1=5, extra=6)

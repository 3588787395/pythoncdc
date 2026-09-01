# R20 repro_08: pos 默认值 + *vararg + kwonly + **kwarg
def f(a=1, *args, sep=' ', **kwargs):
    return a, args, sep, kwargs


result = f(2, 3, sep='-', mode='x')

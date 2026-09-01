# R20 repro_05: *vararg + **kwarg
def f(*args, **kwargs):
    return args, kwargs


result = f(1, 2, x=3)

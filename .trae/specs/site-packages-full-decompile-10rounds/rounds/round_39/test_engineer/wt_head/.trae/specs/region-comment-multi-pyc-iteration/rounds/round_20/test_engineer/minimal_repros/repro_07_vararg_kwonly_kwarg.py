# R20 repro_07: *vararg + 多 kwonly + **kwarg
def f(*args, sep=' ', end='', file=None, flush=None, **kwargs):
    message = sep.join(map(str, args)) + end
    return message, file, flush, kwargs


result = f('a', 'b', sep='-', mode='w')

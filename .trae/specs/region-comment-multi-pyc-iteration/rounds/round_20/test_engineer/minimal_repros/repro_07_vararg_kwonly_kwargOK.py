# Source Generated with Decompyle++ (Python version)
# File: repro_07_vararg_kwonly_kwarg.pyc (Python 3.11)

def f(*args, sep=' ', end='', file=None, flush=None, **kwargs):
    message = sep.join(map(str, args)) + end
    return (message, file, flush, kwargs)
result = f('a', 'b', sep='-', mode='w')

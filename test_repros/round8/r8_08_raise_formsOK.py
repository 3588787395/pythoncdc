# Source Generated with Decompyle++ (Python version)
# File: r8_08_raise_forms.pyc (Python 3.11)

__doc__ = 'R8-08 Raise forms: bare reraise / instance / class / from / call arg / except chain / deep host / f-string msg.'
def r8_raise_reraise(xs, i):
    try:
        return xs[i]
    except IndexError:
        raise
def r8_raise_instance(x):
    if x < 0:
        raise ValueError('negative')
    return x
def r8_raise_class(x):
    if x is None:
        raise KeyError
    return 1
def r8_raise_from(a, b):
    try:
        return a / b
    except ZeroDivisionError as exc:
        raise ValueError('bad divisor') from exc
def r8_raise_call(f, x):
    v = f(x)
    if v is None:
        raise RuntimeError(f(x))
    return v
def r8_raise_in_except_chain(xs, i):
    try:
        return xs[i]
    except IndexError:
        try:
            return xs[i - 1]
        except IndexError:
            raise ValueError('both failed')
def r8_raise_deep_host(x, n):
    for _ in range(n):
        if x == 0:
            raise ArithmeticError('zero in loop')
        x -= 1
    return x
def r8_raise_fstring(a, b):
    if a > b:
        raise ValueError(f'{a} > {b}')
    return b - a

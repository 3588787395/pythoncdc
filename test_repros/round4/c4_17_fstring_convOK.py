# Source Generated with Decompyle++ (Python version)
# File: c4_17_fstring_conv.pyc (Python 3.11)

def e01_root(x):
    return f'{x!r} {x!s} {x!a}'
def e02_shallow(x):
    return f'{x!r}'
def e03_nested(x, w):
    if x:
        return f'a{x:>{w}}b'
    else:
        return f'{x!r:{w}}'
def e04_deep(d):
    r = ''
    for k in d:
        if k:
            r = f'{d[k]!r:>{10}}'
    return r
def e05_nested_field(d):
    return f"{d['k']} = {d['k']!r}"
def e06_format_spec(x, y):
    return f'{x:{y}}'
def e07_multi(a, b):
    return f'{a}{b!r}{a!s}'
class CFS:
    def m(self, x):
        return f'self={x!r}'
def e08_deep_field(d, n):
    r = ''
    for i in range(n):
        if i:
            r = f'{d[i]!r:{i}}'
    return r
def e09_conversion_expr(x):
    return f'{x + 1!r} {x * 2!s}'

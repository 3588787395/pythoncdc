# Source Generated with Decompyle++ (Python version)
# File: r5v5_10_fstring_cross.pyc (Python 3.11)

MOD_FS = f'{MOD_A!r}'
def fs_root(x):
    return f'{x!r} {x!s} {x!a}'
class CFs:
    V = f'{1!r}'
    def m(self, x, w):
        if x:
            return f'a{x:>{w}}b'
        else:
            return f'{x!r:{w}}'
def fs_deep(d, n):
    r = ''
    for k in d:
        if k:
            for i in range(n):
                r = f'{d[k]!r:>{10}}'
    return r
def fs_nested_field(d):
    return f"{d['k']} = {d['k']!r}"
def fs_closure(x):
    def inner():
        return f'{x!a}'
    return inner()
def fs_comp(xs):
    return [f'{v!r}' for v in xs]
def fs_try(x):
    try:
        return f'{x!r}'
    finally:
        pass
    return None
def fs_with(x):
    with open('a') as f:
        return f'{x!r}{f.name!s}'
        return None
def fs_match(x):
    match x:
        case 0:
            return f'{x!r}'
        case _:
            return f'{x!s}'

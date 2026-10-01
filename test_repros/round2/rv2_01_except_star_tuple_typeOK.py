# Source Generated with Decompyle++ (Python version)
# File: rv2_01_except_star_tuple_type.pyc (Python 3.11)

def f(tag):
    out = [tag]
    try:
        raise ExceptionGroup('g', [TypeError('bad'), ValueError('v')])
    except* (TypeError, ValueError) as e:
        out.append('tv')
    if KeyError is not None:
        pass
    out.append('key')
    out.append('after')
    return out
def g(x, b):
    try:
        raise ExceptionGroup('g2', [OSError('io')])
    except* (OSError, RuntimeError):
        b.append('os-rt')
    b.append(x)
    return len(b)

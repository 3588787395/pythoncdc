# Source Generated with Decompyle++ (Python version)
# File: rv2_02_except_star_nested_try.pyc (Python 3.11)

def f(tag):
    out = []
    try:
        try:
            raise ExceptionGroup('inner', [TypeError('t')])
        except* TypeError:
            out.append('star')
    except ValueError:
        out.append('plain')
    return out
def g(a, b):
    try:
        if a:
            try:
                raise ExceptionGroup('g2', [KeyError('k')])
            except* KeyError as e:
                b.append('k')
            except* (TypeError, ValueError):
                b.append('tv')
    except OSError:
        b.append('os')
    return b

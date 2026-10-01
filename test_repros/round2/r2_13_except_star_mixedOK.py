# Source Generated with Decompyle++ (Python version)
# File: r2_13_except_star_mixed.pyc (Python 3.11)

def f(mix):
    out = []
    try:
        try:
            if mix:
                raise ExceptionGroup('g', [TypeError('t')])
            raise ValueError('plain')
        except* TypeError as e:
            out.append('star')
    except ValueError:
        out.append('plain')
    return out
def g(mix):
    out = []
    try:
        try:
            if mix:
                raise ExceptionGroup('g', [TypeError('t'), OSError('o')])
            out.append('no-raise')
        except* TypeError as e:
            out.append('star-T')
        except* OSError as e:
            out.append('star-O')
    finally:
        out.append('fin')
    return out

# Source Generated with Decompyle++ (Python version)
# File: r2_12_except_star_multi.pyc (Python 3.11)

def f(n):
    out = []
    try:
        if n == 0:
            raise ExceptionGroup('g', [TypeError('t'), ValueError('v'), KeyError('k')])
        out.append(n)
    except* Exception as e:
        out.append('T')
    except* ValueError:
        out.append('V')
    except* KeyError as e:
        out.append('K')
    return out

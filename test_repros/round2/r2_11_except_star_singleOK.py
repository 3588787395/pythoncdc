# Source Generated with Decompyle++ (Python version)
# File: r2_11_except_star_single.pyc (Python 3.11)

def f(tag):
    out = [tag]
    try:
        raise ExceptionGroup('g', [TypeError('bad'), ValueError('v')])
    except* TypeError:
        out.append('type')
    out.append('after')
    return out

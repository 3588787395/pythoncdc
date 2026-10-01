# Source Generated with Decompyle++ (Python version)
# File: rv2_04_except_star_tuple_noas_chain.pyc (Python 3.11)

def f(tag):
    out = [tag]
    try:
        raise ExceptionGroup('g', [TypeError('bad'), ValueError('v')])
    except* (TypeError, ValueError):
        out.append('tv')
    if KeyError is not None:
        pass
    out.append('key')
    out.append('after')
    return out

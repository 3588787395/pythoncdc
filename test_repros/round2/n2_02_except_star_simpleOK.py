# Source Generated with Decompyle++ (Python version)
# File: n2_02_except_star_simple.pyc (Python 3.11)

def f(tag):
    try:
        raise ExceptionGroup('g', [ValueError('v')])
    except* ValueError as e:
        tag = tag + 'V'
    return tag

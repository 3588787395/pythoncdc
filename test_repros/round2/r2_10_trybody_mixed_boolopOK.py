# Source Generated with Decompyle++ (Python version)
# File: r2_10_trybody_mixed_boolop.pyc (Python 3.11)

def f_while(a, b, c, acc):
    try:
        if not (a and b):
            acc.append(1)
            if len(acc) > 3:
                pass
            else:
                if a:
                    pass
        if c:
            pass
    except TypeError:
        acc.append('te')
    return acc
def f_assert(a, b, c, acc):
    try:
        if not (a and b or c):
            assert False, 'r2_10'
        acc.append('ok')
    except AssertionError:
        acc.append('ae')
    return acc
def f_ternary(a, b, c, acc):
    try:
        if a and b:
            pass
    except TypeError:
        acc.append('te')
    return acc

# Source Generated with Decompyle++ (Python version)
# File: r1_102_regress_b100win_elif_arm_tailjoin.pyc (Python 3.11)

def f102(a, b, series, log):
    if a > 0:
        return b
    elif a == b:
        n = series[0]
        if n == a:
            if len(series) > 1:
                n = series[1]
            else:
                return b
        b = log(n)
        return b
    elif len(series) > 0:
        m = series[0]
    else:
        m = None
    return m

# Source Generated with Decompyle++ (Python version)
# File: r2_04_try_nest3.pyc (Python 3.11)

def f(a, b, c):
    r = []
    try:
        try:
            r.append(a // b)
        except ZeroDivisionError:
            r.append('z1')
            raise
        else:
            try:
                pass
            except ZeroDivisionError:
                r.append('z2')
    except Exception:
        r.append('top')
    r.append(c)
    return r

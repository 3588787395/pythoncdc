# Source Generated with Decompyle++ (Python version)
# File: r2v3_a19_or_isnone_join_in_loop_break.pyc (Python 3.11)

def f(a, b, redata, n):
    for i in n:
        if i:
            break
        elif a is not None:
            if b is None:
                return redata
            use(a, b)
            continue
        else:
            return redata
    if redata:
        log('x')
        return None
    else:
        return None

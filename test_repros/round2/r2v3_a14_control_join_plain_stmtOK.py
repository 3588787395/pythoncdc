# Source Generated with Decompyle++ (Python version)
# File: r2v3_a14_control_join_plain_stmt.pyc (Python 3.11)

def f(flag, redata, n):
    for i in n:
        if i:
            break
        elif flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        redata = clean(redata)
    if redata:
        log('x')
        return None
    else:
        return None

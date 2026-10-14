# Source Generated with Decompyle++ (Python version)
# File: r2v3_a13_loop_break_chain_join_return.pyc (Python 3.11)

def f(flag, redata, n):
    for i in n:
        if i:
            break
        elif flag == 1:
            log('a')
            return redata
        elif flag == -1:
            log('b')
        else:
            return redata
    if redata:
        log('x')
        return None
    else:
        return None

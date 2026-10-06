# Source Generated with Decompyle++ (Python version)
# File: r2v3_a08_inside_try_chain_join_return.pyc (Python 3.11)

def f(flag, redata):
    try:
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
    except ValueError:
        return None

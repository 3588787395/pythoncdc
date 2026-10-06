# Source Generated with Decompyle++ (Python version)
# File: r2v3_a03_chain_join_plain_stmt.pyc (Python 3.11)

def f(flag, redata):
    if flag == 1:
        log('a')
    elif flag == -1:
        log('b')
    redata = clean(redata)
    if redata:
        return redata
    else:
        return None

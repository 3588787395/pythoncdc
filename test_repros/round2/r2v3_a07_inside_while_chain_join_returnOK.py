# Source Generated with Decompyle++ (Python version)
# File: r2v3_a07_inside_while_chain_join_return.pyc (Python 3.11)

def f(q, stop):
    if not stop:
        flag = q.poll()
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return q
    else:
        return None

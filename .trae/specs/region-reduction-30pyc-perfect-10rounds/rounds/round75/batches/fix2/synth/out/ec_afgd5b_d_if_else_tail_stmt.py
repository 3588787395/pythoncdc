# Source Generated with Decompyle++ (Python version)
# File: d_if_else_tail_stmt.pyc (Python 3.11)

def d_if_else_tail_stmt(items, flag, log):
    if flag:
        return 1
    else:
        for it in items:
            if it:
                break
        del items
        log.append('x')
        return 0

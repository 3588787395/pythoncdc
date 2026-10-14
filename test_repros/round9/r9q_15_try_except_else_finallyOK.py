# Source Generated with Decompyle++ (Python version)
# File: r9q_15_try_except_else_finally.pyc (Python 3.11)

def four_clause(x, lg):
    try:
        v = int(x)
    except BaseException as e:
        lg.error(str(e))
    else:
        if v > 0:
            lg.info('pos')
        else:
            lg.info('nonpos')
    finally:
        cleanup(x)

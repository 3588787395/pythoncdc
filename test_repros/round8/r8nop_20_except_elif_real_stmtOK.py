# Source Generated with Decompyle++ (Python version)
# File: r8nop_20_except_elif_real_stmt.pyc (Python 3.11)

def n8p20(a, log):
    try:
        k(a)
        return None
    except Exception as e:
        if log:
            if a:
                log.info(e)
            elif a is None:
                flag = 1
            else:
                log.warn(e)
                flag = 1

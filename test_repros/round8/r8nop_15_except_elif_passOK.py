# Source Generated with Decompyle++ (Python version)
# File: r8nop_15_except_elif_pass.pyc (Python 3.11)

def n8p15(a, log):
    try:
        k(a)
        return None
    except Exception as e:
        if log:
            if a:
                log.info(e)
            elif a is None:
                pass
            else:
                log.warn(e)
                flag = 1

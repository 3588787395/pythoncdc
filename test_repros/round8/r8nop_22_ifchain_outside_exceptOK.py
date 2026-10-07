# Source Generated with Decompyle++ (Python version)
# File: r8nop_22_ifchain_outside_except.pyc (Python 3.11)

def n8p22(a, log):
    if log:
        if a:
            log.info(a)
            return None
        elif a is None:
            return None
        else:
            log.warn(a)
            flag = 1
    else:
        return None

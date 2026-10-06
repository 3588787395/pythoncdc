# Source Generated with Decompyle++ (Python version)
# File: r1_97_regress_b100reg_tailexit_if_host.pyc (Python 3.11)

def f97(flag, code, log):
    if flag in (1, 2):
        if code == 0:
            log('a')
        else:
            log('b')
            return None
        if code == 1:
            log('c')
    elif code == 2:
        log('d')
    log('tail')

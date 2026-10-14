# Source Generated with Decompyle++ (Python version)
# File: r1_105_regress_b103_getstrat_tailexit.pyc (Python 3.11)

def f105(flag, code, log):
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

# Source Generated with Decompyle++ (Python version)
# File: r1_107_regress_b103_getstrat_noexitarm.pyc (Python 3.11)

def f107(flag, code, log):
    if flag in (1, 2):
        if code == 0:
            log('a')
        else:
            log('b')
        if code == 1:
            log('c')
    elif code == 2:
        log('d')
    log('tail')

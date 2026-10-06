# Source Generated with Decompyle++ (Python version)
# File: r1_100_regress_b100reg_tailexit_loop_cont.pyc (Python 3.11)

def f100(items, code, log):
    for it in items:
        if code == 0:
            log('a')
        else:
            log('b')
            continue
        if code == 1:
            log('c')
        log('tail')

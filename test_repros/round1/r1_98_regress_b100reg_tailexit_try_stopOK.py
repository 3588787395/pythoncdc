# Source Generated with Decompyle++ (Python version)
# File: r1_98_regress_b100reg_tailexit_try_stop.pyc (Python 3.11)

def f98(path, log):
    if path:
        try:
            data = path + 1
        except BaseException:
            log('e')
            return None
        log('after')
        return data
    else:
        log('no')

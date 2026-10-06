# Source Generated with Decompyle++ (Python version)
# File: r1_101_regress_b100win_try_chain_seq_tail.pyc (Python 3.11)

def f101(path, log, data):
    info = {}
    try:
        if path != '':
            if path == 'a':
                info['e'] = 'x'
                return info
            else:
                info['e'] = 'y'
        info['n'] = data
    except BaseException:
        log('e')
    return info

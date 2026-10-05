# Source Generated with Decompyle++ (Python version)
# File: tryintry.pyc (Python 3.11)

def log(m):
    print(m)
def other(u, v):
    print(u, v)
def get_flag(u):
    return u
def f(x):
    try:
        if get_flag(x) is None:
            log('none')
            return None
        try:
            if k1 == 1:
                if k2 == 1:
                    log('in')
                else:
                    log('out')
                log('tail')
            else:
                other(x, 'a')
                return None
            return None
        except BaseException:
            log('inner')
            return None
    except BaseException:
        log('err')
        return None

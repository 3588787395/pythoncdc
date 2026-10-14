# Source Generated with Decompyle++ (Python version)
# File: lastplain.pyc (Python 3.11)

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
        elif k1 == 1:
            if k2 == 1:
                log('in')
            else:
                log('out')
            log('tail')
        else:
            other(x, 'a')
        if k1 == 1:
            log('yes')
            return None
        else:
            other(x, 'a')
            return None
    except BaseException:
        log('err')
        return None

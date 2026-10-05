# Source Generated with Decompyle++ (Python version)
# File: nest3_hret.pyc (Python 3.11)

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
                if k3 == 1:
                    log('d3')
                    return None
                else:
                    log('d3e')
                    return None
            else:
                log('d2e')
                return None
        else:
            other(x, 'a')
    except BaseException:
        log('err')
        return None

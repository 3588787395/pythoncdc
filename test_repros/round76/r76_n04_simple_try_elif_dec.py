# Source Generated with Decompyle++ (Python version)
# File: r76_n04_simple_try_elif.pyc (Python 3.11)

def f(redata, flag):
    if redata:
        try:
            if redata:
                return work(redata)
            log('empty')
            return None
        except BaseException as x:
            log('err: ' + str(x))
            return None
    elif flag == 1:
        log('conv error')
    elif flag == -1:
        log('empty resp')
    return None

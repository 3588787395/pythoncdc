def log(m):
    print(m)


def other(u, v):
    print(u, v)


def get_flag(u):
    return u


def f(x):
    try:
        if k1 == 1:
            if k2 == 1:
                log('in')
            else:
                log('out')
            log('tail')
        else:
            other(x, 'a')
    except BaseException:
        log('err')

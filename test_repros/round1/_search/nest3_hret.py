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
        if k1 == 1:
            if k2 == 1:
                if k3 == 1:
                    log('d3')
                else:
                    log('d3e')
            else:
                log('d2e')
        else:
            other(x, 'a')
    except BaseException:
        log('err')
        return None

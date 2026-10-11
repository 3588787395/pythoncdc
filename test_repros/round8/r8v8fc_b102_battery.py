def tef(fn):
    try:
        fn()
    except KeyError as e:
        h(e)
    else:
        ok()
    finally:
        done()
    return 1


def tesf(fn):
    try:
        fn()
    except* KeyError as eg:
        h(eg)
    else:
        ok()
    finally:
        done()
    return 1


def tesf2(fn):
    try:
        fn()
    except* KeyError as eg:
        h(eg)
    finally:
        done()
    return 1


def tesf3(fn):
    try:
        fn()
    except* KeyError as eg:
        h(eg)
    else:
        ok()
    return 1


def x1deg(fn):
    try:
        x = 1
    except E:
        pass
    finally:
        done()
    return 1


def ideg(fn):
    try:
        try:
            pass
        except E:
            pass
        fn()
    finally:
        done()
    return 1


def oes(fn):
    try:
        pass
    except* E:
        pass
    else:
        ok()
    finally:
        done()
    return 1


def ies(fn):
    try:
        try:
            pass
        except* E:
            pass
        else:
            ok()
    finally:
        done()
    return 1


def pin(fn):
    try:
        fn()
        try:
            pass
        except E:
            pass
    finally:
        done()
    return 1

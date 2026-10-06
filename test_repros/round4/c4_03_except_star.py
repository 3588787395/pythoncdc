def e01_root(fn):
    r = None
    try:
        fn()
    except* ValueError as eg:
        r = eg.exceptions
    except* TypeError as eg:
        r = eg.exceptions
    return r


def e02_shallow(fn):
    r = None
    try:
        fn()
    except* KeyError as eg:
        r = eg
    return r


def e03_deep(fn):
    for i in range(2):
        if i:
            try:
                fn()
            except* ValueError as eg:
                handle(eg)
            except* TypeError as eg:
                handle(eg)
    return i


def e04_with(fn):
    with ctx() as c:
        try:
            fn()
        except* KeyError as eg:
            handle(eg)
        else:
            ok()
        finally:
            done()
    return c


def e05_nested(fn):
    try:
        try:
            fn()
        except* ValueError as eg:
            handle(eg)
    except* TypeError as eg:
        handle(eg)
    return 0


def e06_while(fn):
    n = 0
    while n < 3:
        try:
            fn()
        except* OSError as eg:
            for e in eg.exceptions:
                handle(e)
        n += 1
    return n


class CX:
    def m(self, fn):
        while cond():
            try:
                fn()
            except* RuntimeError as eg:
                handle(eg)


def e07_closure(fn):
    def inner():
        r = None
        try:
            fn()
        except* Exception as eg:
            r = eg.exceptions
        return r
    return inner()


def e08_match_host(fn):
    match flag():
        case 0:
            try:
                fn()
            except* ValueError as eg:
                handle(eg)
        case _:
            pass
    return 0


def e09_if_else(fn):
    if flag():
        try:
            fn()
        except* ValueError as eg:
            handle(eg)
    else:
        try:
            fn()
        except* TypeError as eg:
            handle(eg)
    return 0

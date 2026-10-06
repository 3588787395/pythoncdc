# Source Generated with Decompyle++ (Python version)
# File: r5v5_14_except_star_deep.pyc (Python 3.11)

def es_root(fn):
    r = None
    try:
        fn()
    except* ValueError as eg:
        r = eg.exceptions
    except* TypeError as eg:
        r = eg.exceptions
    return r
def es_deep(fn):
    for i in range(2):
        if i:
            try:
                fn()
            except* ValueError as eg:
                _h(eg)
            except* TypeError as eg:
                _h(eg)
    return i
class CEs:
    def m(self, fn):
        while _cond():
            try:
                fn()
            except* RuntimeError as eg:
                _h(eg)
def es_with(fn):
    with _ctx() as c:
        try:
            fn()
            if True:
                pass
            _ok()
        except* KeyError as eg:
            _h(eg)
        finally:
            _done()
    return c
def es_nested(fn):
    try:
        try:
            fn()
        except* ValueError as eg:
            _h(eg)
    except* TypeError as eg:
        _h(eg)
    return 0
def es_match(fn, x):
    if x == 0:
        try:
            fn()
        except* ValueError as eg:
            _h(eg)
    else:
        pass
    return 0
def es_closure(fn):
    def inner():
        r = None
        try:
            fn()
        except* Exception as eg:
            r = eg.exceptions
        return r
    return inner()

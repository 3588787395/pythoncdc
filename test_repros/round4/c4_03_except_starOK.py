# Source Generated with Decompyle++ (Python version)
# File: c4_03_except_star.pyc (Python 3.11)

def e01_root(fn):
    r = None
    try:
        fn()
    except* ValueError as eg:
        r = eg.exceptions
    else:
        if TypeError is not None:
            pass
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
        try:
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
    if flag() == 0:
        try:
            fn()
        except* ValueError as eg:
            handle(eg)
    else:
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

# Source Generated with Decompyle++ (Python version)
# File: yp4.pyc (Python 3.11)

def yp4(items):
    def inner(lst):
        for x in lst:
            got = yield x
            if got is None:
                got = 0
            yield got * 2
    return inner

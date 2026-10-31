# Source Generated with Decompyle++ (Python version)
# File: yp1.pyc (Python 3.11)

def yp1(items, enc):
    def inner(lst):
        yield 'HEAD'
        if not lst:
            return None
        else:
            yield enc(lst)
            yield 'TAIL'
    return inner

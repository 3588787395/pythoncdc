# Source Generated with Decompyle++ (Python version)
# File: yp3.pyc (Python 3.11)

def yp3(items, enc):
    def inner(lst, marker):
        for x in lst:
            yield enc(x)
        yield ']'
        if marker is not None:
            del marker['k']
            return None
        else:
            return None
    return inner

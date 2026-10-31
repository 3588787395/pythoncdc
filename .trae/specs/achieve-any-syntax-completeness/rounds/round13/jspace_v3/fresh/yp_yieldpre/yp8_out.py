# Source Generated with Decompyle++ (Python version)
# File: yp8.pyc (Python 3.11)

def yp8(lst, enc):
    yield 'S'
    if not lst:
        return None
    else:
        for x in lst:
            yield enc(x)
        yield 'E'
        if not lst:
            del lst[:]
        return None

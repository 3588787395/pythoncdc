# Source Generated with Decompyle++ (Python version)
# File: yp7.pyc (Python 3.11)

def yp7(items, enc, sep):
    def mid(lst):
        yield '{'
        if not lst:
            yield '}'
            return None
        else:
            for x in lst:
                yield enc(x)
                yield sep
            yield '}'
    def top(lst):
        yield '['
        if not lst:
            return None
        yield from mid(lst)
        yield ']'
    return top

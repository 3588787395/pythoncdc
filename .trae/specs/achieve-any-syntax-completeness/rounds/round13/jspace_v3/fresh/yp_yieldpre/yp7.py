def yp7(items, enc, sep):
    def mid(lst):
        yield '{'
        if not lst:
            yield '}'
            return None
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

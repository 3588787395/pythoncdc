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

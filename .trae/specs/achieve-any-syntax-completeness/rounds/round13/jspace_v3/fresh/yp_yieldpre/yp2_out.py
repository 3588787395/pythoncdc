# Source Generated with Decompyle++ (Python version)
# File: yp2.pyc (Python 3.11)

def yp2(items, enc, sep, keyf):
    def inner(pairs):
        for k, v in pairs:
            if k is None:
                continue
            yield enc(k)
            yield sep
            if isinstance(v, str):
                yield enc(v)
                continue
            if v > 0:
                yield enc(v)
            continue
    return inner

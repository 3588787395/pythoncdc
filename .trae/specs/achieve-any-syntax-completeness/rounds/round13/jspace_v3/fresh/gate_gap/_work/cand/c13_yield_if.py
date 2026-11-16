def _host():
    pass

def outer(ns):
    for n in ns:
        if n < 0:
            yield -n
        elif n == 0:
            yield 0
        else:
            yield n * 2

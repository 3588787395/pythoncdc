class E(Exception):
    pass


def g():
    return 1


def s1():
    while True:
        try:
            return g()
        except E:
            continue

class E(Exception):
    pass
def f():
    try:
        raise E()
    except ValueError:
        return 1

def deco(tag):
    def wrap(f):
        return f
    return wrap
@deco("A")
def g():
    return 1

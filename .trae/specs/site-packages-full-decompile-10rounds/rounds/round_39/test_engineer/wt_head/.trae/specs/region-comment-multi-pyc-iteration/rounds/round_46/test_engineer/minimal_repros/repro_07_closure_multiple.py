def outer(a, b):
    def inner():
        return a + b
    return inner

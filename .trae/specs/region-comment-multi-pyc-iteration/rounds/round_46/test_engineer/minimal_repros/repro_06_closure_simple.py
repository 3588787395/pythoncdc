def outer(x):
    def inner():
        return x + 1
    return inner

def outer():
    total = 0
    other = 5
    def inner():
        return total + other
    return inner

def outer():
    c = 0
    d = 1
    def inner():
        nonlocal c
        c += 1
    inner()

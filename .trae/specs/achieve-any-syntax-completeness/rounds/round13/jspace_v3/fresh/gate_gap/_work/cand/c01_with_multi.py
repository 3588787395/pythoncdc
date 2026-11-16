def _host():
    pass

def outer(fa, fb):
    with fa() as a, fb() as b:
        x = a + b
    return x

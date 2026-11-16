def _host():
    pass

def outer(fa, fb):
    with fa() as a:
        with fb() as b:
            return a + b

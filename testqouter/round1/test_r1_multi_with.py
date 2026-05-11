def test():
    class Ctx:
        def __init__(self, v):
            self.v = v
        def __enter__(self):
            return self.v
        def __exit__(self, *args):
            pass
    with Ctx(1) as a, Ctx(2) as b:
        result = a + b
    return result

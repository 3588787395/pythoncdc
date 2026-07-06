def test():
    class Ctx:
        def __enter__(self):
            return 42
        def __exit__(self, *args):
            pass
    with Ctx() as v:
        try:
            result = v + 1
        except TypeError:
            result = 0
    return result

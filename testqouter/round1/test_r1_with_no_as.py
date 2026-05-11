def test():
    class Ctx:
        def __enter__(self):
            return 42
        def __exit__(self, *args):
            pass
    with Ctx():
        result = 1
    return result

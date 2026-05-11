def test():
    class Ctx:
        def __enter__(self):
            return 42
        def __exit__(self, *args):
            pass
    try:
        with Ctx() as v:
            result = v
    except ValueError:
        result = -1
    return result
